from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import EvaluationFailedError
from app.integrations.llm import JobLike, LLMCompletion
from app.models import Application, ApplicationStatus, Recruiter
from app.repositories import applications as applications_repo
from app.repositories import exports as exports_repo
from app.schemas.evaluation import Citation, ModelEvaluation
from app.services.ingestion import IngestionResult
from app.services.pipeline import process_application, recover_stuck_applications
from tests.api.test_applications import _apply
from tests.api.test_jobs import _create_job, _insert_job

RESUME_TEXT = (
    "Senior software engineer with eight years of Python. "
    "Built production HTTP APIs in FastAPI. "
    "Designed PostgreSQL schemas for high-volume applications."
)


class FakeCompleter:
    def __init__(self, evaluation: ModelEvaluation | None = None, *, fail: bool = False) -> None:
        self.evaluation = evaluation
        self.fail = fail
        self.calls = 0

    async def complete(self, job: JobLike, resume_text: str) -> LLMCompletion:
        self.calls += 1
        if self.fail:
            raise EvaluationFailedError
        assert self.evaluation is not None
        return LLMCompletion(
            evaluation=self.evaluation,
            model_name="fake-model",
            latency_ms=5,
            input_tokens=1,
            output_tokens=1,
        )


def _evaluation(score: int, *, strengths: list[str] | None = None) -> ModelEvaluation:
    return ModelEvaluation(
        is_resume=True,
        score=score,
        key_strengths=strengths or ["FastAPI production APIs"],
        missing_requirements=[],
        citations=[Citation(claim="Uses FastAPI", quote="Built production HTTP APIs in FastAPI.")],
        injection_suspected=False,
    )


@pytest.fixture(autouse=True)
def fake_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _extract(_pdf_bytes: bytes) -> IngestionResult:
        return IngestionResult(text=RESUME_TEXT, page_count=1, duration_ms=1, too_empty=False)

    monkeypatch.setattr("app.services.pipeline.extract_text", _extract)


async def test_pipeline_scores_and_orders_leaderboard(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _create_job(client)
    slug = str(job["public_slug"])
    first = await _apply(client, slug, email="high@example.com")
    second = await _apply(client, slug, email="low@example.com")
    assert first.status_code == 202
    assert second.status_code == 202
    first_id = UUID(first.json()["id"])
    second_id = UUID(second.json()["id"])

    received = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}/leaderboard")
    assert received.status_code == 200
    assert received.json()["counts"]["received"] == 2

    assert await applications_repo.claim_for_processing(db_session, first_id)
    processing = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}/leaderboard")
    assert processing.json()["counts"]["processing"] == 1
    assert processing.json()["counts"]["received"] == 1

    await process_application(
        first_id,
        db_session,
        reclaim_processing=True,
        completer=FakeCompleter(_evaluation(91)),
    )
    await process_application(second_id, db_session, completer=FakeCompleter(_evaluation(44)))

    board = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}/leaderboard")
    assert board.status_code == 200
    body = board.json()
    assert [item["email"] for item in body["items"]] == ["high@example.com", "low@example.com"]
    assert [item["score"] for item in body["items"]] == [91, 44]
    assert body["counts"]["scored"] == 2


async def test_non_resume_is_refused(client: AsyncClient, db_session: AsyncSession) -> None:
    job = await _create_job(client)
    applied = await _apply(client, str(job["public_slug"]))
    completer = FakeCompleter(
        ModelEvaluation(
            is_resume=False,
            refusal_reason="Not a resume",
            score=None,
            injection_suspected=False,
        )
    )

    await process_application(UUID(applied.json()["id"]), db_session, completer=completer)

    detail = await client.get(f"{settings.API_V1_STR}/applications/{applied.json()['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "refused"
    assert body["score"] is None
    assert body["is_resume"] is False
    assert body["resume_url"]
    pdf = await client.get(body["resume_url"])
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")


async def test_failed_application_can_be_rescored(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _create_job(client)
    applied = await _apply(client, str(job["public_slug"]))
    application_id = UUID(applied.json()["id"])

    too_early = await client.post(f"{settings.API_V1_STR}/applications/{application_id}/rescore")
    assert too_early.status_code == 404

    await process_application(application_id, db_session, completer=FakeCompleter(fail=True))
    failed = await applications_repo.get_by_id(db_session, application_id)
    assert failed is not None
    assert failed.status == ApplicationStatus.FAILED

    response = await client.post(f"{settings.API_V1_STR}/applications/{application_id}/rescore")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    await process_application(
        application_id,
        db_session,
        reclaim_processing=True,
        completer=FakeCompleter(_evaluation(80)),
    )
    scored = await applications_repo.get_by_id(db_session, application_id)
    assert scored is not None
    assert scored.status == ApplicationStatus.SCORED
    assert scored.score == 80


async def test_stuck_received_application_is_recovered(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "STUCK_APPLICATION_MINUTES", 5)
    job = await _create_job(client)
    applied = await _apply(client, str(job["public_slug"]))
    application = await applications_repo.get_by_id(db_session, UUID(applied.json()["id"]))
    assert application is not None
    application.created_at = datetime.now(UTC) - timedelta(minutes=6)
    await db_session.commit()

    ids = await recover_stuck_applications(db_session, completer=FakeCompleter(_evaluation(70)))

    assert application.id in ids
    refreshed = await applications_repo.get_by_id(db_session, application.id)
    assert refreshed is not None
    assert refreshed.status == ApplicationStatus.SCORED


async def test_csv_escapes_formula_and_records_export(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _create_job(client)
    applied = await _apply(client, str(job["public_slug"]))
    application_id = UUID(applied.json()["id"])
    await process_application(
        application_id,
        db_session,
        completer=FakeCompleter(_evaluation(88, strengths=["=1+1", "FastAPI"])),
    )

    response = await client.post(
        f"{settings.API_V1_STR}/jobs/{job['id']}/exports",
        json={"application_ids": [str(application_id)]},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "'=1+1" in response.text
    events = await exports_repo.list_for_job(db_session, UUID(str(job["id"])))
    assert len(events) == 1
    assert events[0].application_ids == [str(application_id)]

    missing = await client.post(
        f"{settings.API_V1_STR}/jobs/{job['id']}/exports",
        json={"application_ids": [str(uuid4())]},
    )
    assert missing.status_code == 404


async def test_foreign_job_and_application_are_hidden(
    client: AsyncClient, db_session: AsyncSession, other_recruiter: Recruiter
) -> None:
    job = await _insert_job(db_session, other_recruiter)
    application = Application(
        job_id=job.id,
        email="hidden@example.com",
        status=ApplicationStatus.RECEIVED,
    )
    db_session.add(application)
    await db_session.flush()

    board = await client.get(f"{settings.API_V1_STR}/jobs/{job.id}/leaderboard")
    detail = await client.get(f"{settings.API_V1_STR}/applications/{application.id}")
    export = await client.post(
        f"{settings.API_V1_STR}/jobs/{job.id}/exports",
        json={"top_n": 1},
    )

    assert board.status_code == 404
    assert detail.status_code == 404
    assert export.status_code == 404


async def test_resume_token_rejects_garbage(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/public/resumes/not-a-token")
    assert response.status_code == 401
