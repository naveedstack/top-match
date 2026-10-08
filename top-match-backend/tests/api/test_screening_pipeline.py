import csv
import io
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import (
    Application,
    ApplicationStatus,
    PhaseOutcome,
    PhaseResult,
    Recruiter,
    ScreeningPhase,
)
from app.repositories import applications as applications_repo
from app.schemas.evaluation import ModelEvaluation
from app.services.ingestion import IngestionResult
from app.services.pipeline import process_application, recover_stuck_applications
from tests.api.test_applications import _upload
from tests.api.test_jobs import JOB_BODY, _insert_job
from tests.api.test_pipeline import RESUME_TEXT, FakeCompleter, _evaluation

AUTH_REASON = "Not authorized to work in Pakistan"


def _auth_field() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "type": "radio",
        "label": "Are you authorized to work in Pakistan?",
        "required": True,
        "options": ["Yes", "No"],
        "knockout": {"reason": AUTH_REASON, "allowed_values": ["Yes"]},
    }


def _years_field() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "type": "number",
        "label": "Years of Python",
        "required": True,
        "min": 0,
        "knockout": {"reason": "Fewer than 3 years of Python", "min": 3},
        "scoring": {"weight": 1, "target": 6},
    }


@pytest.fixture(autouse=True)
def fake_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _extract(_pdf_bytes: bytes) -> IngestionResult:
        return IngestionResult(text=RESUME_TEXT, page_count=1, duration_ms=1, too_empty=False)

    monkeypatch.setattr("app.services.pipeline.extract_text", _extract)


async def _job(client: AsyncClient, fields: list[dict[str, Any]]) -> dict[str, Any]:
    response = await client.post(
        f"{settings.API_V1_STR}/jobs", json={**JOB_BODY, "form_fields": fields}
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def _apply(
    client: AsyncClient, job: dict[str, Any], answers: dict[str, Any], email: str
) -> UUID:
    uploaded = await _upload(client)
    assert uploaded.status_code == 201
    response = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}/applications",
        json={
            "email": email,
            "file_id": uploaded.json()["id"],
            "consented": True,
            "answers": answers,
        },
    )
    assert response.status_code == 202, response.text
    return UUID(response.json()["id"])


async def _phase_rows(db_session: AsyncSession, application_id: UUID) -> list[PhaseResult]:
    result = await db_session.execute(
        select(PhaseResult)
        .where(PhaseResult.application_id == application_id)
        .order_by(PhaseResult.created_at)
    )
    return list(result.scalars().all())


async def _knocked_out(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[dict[str, Any], UUID, FakeCompleter]:
    field = _auth_field()
    job = await _job(client, [field])
    application_id = await _apply(client, job, {field["id"]: "No"}, "out@example.com")
    completer = FakeCompleter(_evaluation(90))
    await process_application(application_id, db_session, completer=completer)
    return job, application_id, completer


async def test_knockout_failure_never_calls_the_model(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _job_body, application_id, completer = await _knocked_out(client, db_session)

    assert completer.calls == 0
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.status == ApplicationStatus.KNOCKED_OUT
    assert application.current_phase == ScreeningPhase.KNOCKOUT
    assert application.stopped_phase == ScreeningPhase.KNOCKOUT
    assert application.stop_code == "knockout_failed"
    assert application.stop_reason == AUTH_REASON
    assert application.score is None
    assert application.extracted_text is None
    rows = await _phase_rows(db_session, application_id)
    assert [(row.phase, row.outcome) for row in rows] == [
        (ScreeningPhase.ACCEPT, PhaseOutcome.PASS),
        (ScreeningPhase.KNOCKOUT, PhaseOutcome.FAIL),
    ]
    assert rows[1].reasons[0]["message"] == AUTH_REASON
    assert rows[1].config_version


async def test_number_below_knockout_minimum_is_accepted_then_knocked_out(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    field = _years_field()
    job = await _job(client, [field])

    application_id = await _apply(client, job, {field["id"]: 1}, "junior@example.com")
    completer = FakeCompleter(_evaluation(90))
    await process_application(application_id, db_session, completer=completer)

    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.status == ApplicationStatus.KNOCKED_OUT
    assert completer.calls == 0


async def test_passing_application_runs_every_phase_in_order(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    auth, years = _auth_field(), _years_field()
    job = await _job(client, [auth, years])
    application_id = await _apply(client, job, {auth["id"]: "Yes", years["id"]: 3}, "ok@x.com")
    completer = FakeCompleter(_evaluation(81))

    await process_application(application_id, db_session, completer=completer)

    assert completer.calls == 1
    rows = await _phase_rows(db_session, application_id)
    assert [row.phase for row in rows] == [
        ScreeningPhase.ACCEPT,
        ScreeningPhase.KNOCKOUT,
        ScreeningPhase.ANSWERS,
        ScreeningPhase.RESUME,
    ]
    assert rows[2].evidence["answers_score"] == 50
    assert rows[3].model_name == "fake-model"
    detail = await client.get(f"{settings.API_V1_STR}/applications/{application_id}")
    body = detail.json()
    assert body["status"] == "scored"
    # The answers score stays separate from the resume score.
    assert body["score"] == 81
    assert body["answers_score"] == 50
    assert body["current_phase"] == "resume"
    assert body["stopped_phase"] is None
    assert [item["phase"] for item in body["phase_results"]] == [
        "accept",
        "knockout",
        "answers",
        "resume",
    ]


async def test_job_without_questions_skips_code_phases(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _job(client, [])
    application_id = await _apply(client, job, {}, "plain@example.com")

    await process_application(application_id, db_session, completer=FakeCompleter(_evaluation(70)))

    rows = await _phase_rows(db_session, application_id)
    assert [row.outcome for row in rows] == [
        PhaseOutcome.PASS,
        PhaseOutcome.SKIPPED,
        PhaseOutcome.SKIPPED,
        PhaseOutcome.PASS,
    ]


async def test_move_forward_records_override_and_continues(
    client: AsyncClient, db_session: AsyncSession, recruiter: Recruiter
) -> None:
    _job_body, application_id, _completer = await _knocked_out(client, db_session)

    response = await client.post(
        f"{settings.API_V1_STR}/applications/{application_id}/move-forward"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    completer = FakeCompleter(_evaluation(77))
    await process_application(
        application_id, db_session, reclaim_processing=True, completer=completer
    )

    assert completer.calls == 1
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.status == ApplicationStatus.SCORED
    assert application.score == 77
    assert application.stopped_phase is None
    rows = await _phase_rows(db_session, application_id)
    assert [(row.phase, row.outcome) for row in rows] == [
        (ScreeningPhase.ACCEPT, PhaseOutcome.PASS),
        (ScreeningPhase.KNOCKOUT, PhaseOutcome.FAIL),
        (ScreeningPhase.KNOCKOUT, PhaseOutcome.PASS),
        (ScreeningPhase.ANSWERS, PhaseOutcome.SKIPPED),
        (ScreeningPhase.RESUME, PhaseOutcome.PASS),
    ]
    override = rows[2]
    assert override.overridden_by_recruiter_id == recruiter.id
    assert override.evidence["overridden_reason"] == AUTH_REASON
    detail = await client.get(f"{settings.API_V1_STR}/applications/{application_id}")
    assert [item["overridden"] for item in detail.json()["phase_results"]] == [
        False,
        False,
        True,
        False,
        False,
    ]


async def test_move_forward_rejects_other_states_and_other_companies(
    client: AsyncClient, db_session: AsyncSession, other_recruiter: Recruiter
) -> None:
    job = await _job(client, [])
    application_id = await _apply(client, job, {}, "fresh@example.com")
    not_knocked_out = await client.post(
        f"{settings.API_V1_STR}/applications/{application_id}/move-forward"
    )
    assert not_knocked_out.status_code == 404

    foreign_job = await _insert_job(db_session, other_recruiter)
    foreign = Application(
        job_id=foreign_job.id,
        email="foreign@example.com",
        status=ApplicationStatus.KNOCKED_OUT,
        stopped_phase=ScreeningPhase.KNOCKOUT,
        current_phase=ScreeningPhase.KNOCKOUT,
    )
    db_session.add(foreign)
    await db_session.flush()
    for action in ("move-forward", "mark-reviewed", "rescore"):
        response = await client.post(f"{settings.API_V1_STR}/applications/{foreign.id}/{action}")
        assert response.status_code == 404


async def test_refused_application_can_be_retried(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _job(client, [])
    application_id = await _apply(client, job, {}, "menu@example.com")
    refusal = ModelEvaluation(is_resume=False, refusal_reason="Not a resume", score=None)
    await process_application(application_id, db_session, completer=FakeCompleter(refusal))
    refused = await applications_repo.get_by_id(db_session, application_id)
    assert refused is not None
    assert refused.status == ApplicationStatus.REFUSED
    assert refused.stop_code == "not_resume"

    response = await client.post(f"{settings.API_V1_STR}/applications/{application_id}/rescore")
    assert response.status_code == 200
    completer = FakeCompleter(_evaluation(64))
    await process_application(
        application_id, db_session, reclaim_processing=True, completer=completer
    )

    scored = await applications_repo.get_by_id(db_session, application_id)
    assert scored is not None
    assert scored.status == ApplicationStatus.SCORED
    assert scored.stop_reason is None
    # Retry resumes at the resume phase; accept/knockout/answers are not rerun.
    rows = await _phase_rows(db_session, application_id)
    assert [row.phase for row in rows][-2:] == [ScreeningPhase.RESUME, ScreeningPhase.RESUME]
    assert len(rows) == 5


async def test_mark_reviewed_records_manual_override(
    client: AsyncClient, db_session: AsyncSession, recruiter: Recruiter
) -> None:
    job = await _job(client, [])
    application_id = await _apply(client, job, {}, "fail@example.com")
    await process_application(application_id, db_session, completer=FakeCompleter(fail=True))

    response = await client.post(
        f"{settings.API_V1_STR}/applications/{application_id}/mark-reviewed"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.reviewed_at is not None
    rows = await _phase_rows(db_session, application_id)
    assert rows[-1].outcome == PhaseOutcome.REVIEW
    assert rows[-1].overridden_by_recruiter_id == recruiter.id

    scored_job = await _job(client, [])
    scored_id = await _apply(client, scored_job, {}, "good@example.com")
    await process_application(scored_id, db_session, completer=FakeCompleter(_evaluation(90)))
    not_allowed = await client.post(f"{settings.API_V1_STR}/applications/{scored_id}/mark-reviewed")
    assert not_allowed.status_code == 404


async def test_unreadable_resume_fails_without_model_call(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _blank(_pdf_bytes: bytes) -> IngestionResult:
        return IngestionResult(text="", page_count=1, duration_ms=1, too_empty=True)

    monkeypatch.setattr("app.services.pipeline.extract_text", _blank)
    job = await _job(client, [])
    application_id = await _apply(client, job, {}, "blank@example.com")
    completer = FakeCompleter(_evaluation(90))

    await process_application(application_id, db_session, completer=completer)

    assert completer.calls == 0
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.status == ApplicationStatus.FAILED
    assert application.stop_code == "unreadable"
    assert application.stopped_phase == ScreeningPhase.RESUME


async def test_stuck_sweep_ignores_recently_retried_old_application(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "STUCK_APPLICATION_MINUTES", 5)
    job = await _job(client, [])
    application_id = await _apply(client, job, {}, "old@example.com")
    await process_application(application_id, db_session, completer=FakeCompleter(fail=True))
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    application.created_at = datetime.now(UTC) - timedelta(minutes=30)
    await db_session.commit()

    retried = await client.post(f"{settings.API_V1_STR}/applications/{application_id}/rescore")
    assert retried.status_code == 200
    completer = FakeCompleter(_evaluation(50))
    ids = await recover_stuck_applications(db_session, completer=completer)

    assert application_id not in ids
    assert completer.calls == 0

    application.processing_started_at = datetime.now(UTC) - timedelta(minutes=6)
    await db_session.commit()
    ids = await recover_stuck_applications(db_session, completer=completer)
    assert application_id in ids
    assert completer.calls == 1


async def test_export_includes_stopped_at_and_reason(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job, application_id, _completer = await _knocked_out(client, db_session)

    response = await client.post(
        f"{settings.API_V1_STR}/jobs/{job['id']}/exports",
        json={"application_ids": [str(application_id)]},
    )

    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.text)))
    header, row = rows[1], rows[2]
    assert header[6:8] == ["stopped at", "reason"]
    assert row[6:8] == ["knockout", AUTH_REASON]


async def test_leaderboard_stage_filter_and_lists(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    field = _auth_field()
    job = await _job(client, [field])
    out_id = await _apply(client, job, {field["id"]: "No"}, "out@example.com")
    in_id = await _apply(client, job, {field["id"]: "Yes"}, "in@example.com")
    for application_id in (out_id, in_id):
        await process_application(
            application_id, db_session, completer=FakeCompleter(_evaluation(60))
        )
    url = f"{settings.API_V1_STR}/jobs/{job['id']}/leaderboard"

    board = (await client.get(url)).json()
    assert board["counts"]["knocked_out"] == 1
    assert board["counts"]["scored"] == 1

    knocked = (await client.get(url, params={"stage": "knockout"})).json()
    assert [item["email"] for item in knocked["items"]] == ["out@example.com"]
    assert knocked["items"][0]["stop_reason"] == AUTH_REASON
    assert knocked["items"][0]["stopped_phase"] == "knockout"

    active = (await client.get(url, params=[("status", "scored"), ("status", "processing")])).json()
    assert [item["email"] for item in active["items"]] == ["in@example.com"]
    assert active["items"][0]["current_phase"] == "resume"


async def test_public_form_hides_knockout_rules_and_weights(client: AsyncClient) -> None:
    job = await _job(client, [_auth_field(), _years_field()])

    response = await client.get(f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}")

    assert response.status_code == 200
    text = response.text
    assert AUTH_REASON not in text
    for field in response.json()["form_fields"]:
        assert field.get("knockout") is None
        assert field.get("scoring") is None
    private = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}")
    assert private.json()["form_fields"][0]["knockout"]["reason"] == AUTH_REASON


async def test_age_proxy_knockout_warns_but_saves(client: AsyncClient) -> None:
    field = {
        "id": str(uuid4()),
        "type": "dropdown",
        "label": "Year of graduation",
        "required": True,
        "options": ["Before 2000", "2000 or later"],
        "knockout": {"reason": "Graduated too early", "allowed_values": ["2000 or later"]},
    }

    response: Response = await client.post(
        f"{settings.API_V1_STR}/jobs", json={**JOB_BODY, "form_fields": [field]}
    )

    assert response.status_code == 201
    warnings = response.json()["form_warnings"]
    assert [item["field_id"] for item in warnings] == [field["id"]]


async def test_invalid_knockout_definition_is_rejected(client: AsyncClient) -> None:
    field = _auth_field() | {"required": False}

    response = await client.post(
        f"{settings.API_V1_STR}/jobs", json={**JOB_BODY, "form_fields": [field]}
    )

    assert response.status_code == 422
