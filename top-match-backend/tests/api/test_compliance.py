from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.notices import AI_SCREENING_NOTICE, SCREENING_DISCLAIMER, privacy_notice
from app.integrations import storage
from app.main import create_app
from app.models import Job
from app.repositories import applications as applications_repo
from app.services.ingestion import IngestionResult
from app.services.pipeline import process_application
from app.services.retention import purge_expired_applications
from tests.api.test_applications import _apply, _upload
from tests.api.test_jobs import _create_job
from tests.api.test_pipeline import RESUME_TEXT, FakeCompleter, _evaluation


@pytest.fixture
def fake_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _extract(_pdf_bytes: bytes) -> IngestionResult:
        return IngestionResult(text=RESUME_TEXT, page_count=1, duration_ms=1, too_empty=False)

    monkeypatch.setattr("app.services.pipeline.extract_text", _extract)


async def test_apply_requires_true_consent(client: AsyncClient, db_session: AsyncSession) -> None:
    job = await _create_job(client)
    slug = str(job["public_slug"])
    uploaded = await _upload(client)
    assert uploaded.status_code == 201
    file_id = uploaded.json()["id"]
    url = f"{settings.API_V1_STR}/public/jobs/{slug}/applications"

    missing = await client.post(url, json={"email": "c@example.com", "file_id": file_id})
    denied = await client.post(
        url, json={"email": "c@example.com", "file_id": file_id, "consented": False}
    )
    accepted = await _apply(client, slug, email="c@example.com")

    assert missing.status_code == 422
    assert denied.status_code == 422
    assert accepted.status_code == 202
    application = await applications_repo.get_by_id(db_session, UUID(accepted.json()["id"]))
    assert application is not None
    assert application.consented_at is not None


async def test_public_job_includes_notices(client: AsyncClient) -> None:
    job = await _create_job(client)

    response = await client.get(f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}")

    assert response.status_code == 200
    body = response.json()
    assert body["privacy_notice"] == privacy_notice()
    assert body["ai_screening_notice"] == AI_SCREENING_NOTICE
    assert body["screening_disclaimer"] == SCREENING_DISCLAIMER


async def test_purge_removes_expired_closed_job_applications(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _create_job(client)
    applied = await _apply(client, str(job["public_slug"]))
    application_id = UUID(applied.json()["id"])
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    storage_key = application.resume_storage_key
    assert storage_key is not None
    await client.post(f"{settings.API_V1_STR}/jobs/{job['id']}/close")

    record = await db_session.get(Job, UUID(str(job["id"])))
    assert record is not None
    record.closed_at = datetime.now(UTC) - timedelta(days=settings.RETENTION_DAYS + 1)
    await db_session.commit()

    counts = await purge_expired_applications(db_session)

    assert counts["purged"] == 1
    assert await applications_repo.get_by_id(db_session, application_id) is None
    assert not await storage.exists(storage_key)


async def test_purge_skips_open_and_recently_closed_jobs(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    open_job = await _create_job(client)
    open_apply = await _apply(client, str(open_job["public_slug"]), email="open@example.com")
    closed_job = await _create_job(client)
    closed_apply = await _apply(client, str(closed_job["public_slug"]), email="closed@example.com")
    await client.post(f"{settings.API_V1_STR}/jobs/{closed_job['id']}/close")

    counts = await purge_expired_applications(db_session)

    assert counts["purged"] == 0
    assert await applications_repo.get_by_id(db_session, UUID(open_apply.json()["id"])) is not None
    assert (
        await applications_repo.get_by_id(db_session, UUID(closed_apply.json()["id"])) is not None
    )


async def test_csv_starts_with_disclaimer_and_escapes_formula(
    client: AsyncClient, db_session: AsyncSession, fake_ocr: None
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
    lines = response.text.splitlines()
    assert SCREENING_DISCLAIMER in lines[0]
    assert "'=1+1" in response.text

    board = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}/leaderboard")
    detail = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}")
    assert board.json()["screening_disclaimer"] == SCREENING_DISCLAIMER
    assert detail.json()["screening_disclaimer"] == SCREENING_DISCLAIMER


async def test_request_id_is_echoed(client: AsyncClient) -> None:
    generated = await client.get(f"{settings.API_V1_STR}/health")
    echoed = await client.get(
        f"{settings.API_V1_STR}/health", headers={"X-Request-ID": "test-request-id"}
    )

    assert generated.status_code == 200
    assert generated.headers.get("x-request-id")
    assert echoed.headers.get("x-request-id") == "test-request-id"


def test_production_hides_openapi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "GEMINI_DATA_USE_ACKNOWLEDGED", True)
    app = create_app()
    assert app.openapi_url is None
    assert app.docs_url is None
    assert app.redoc_url is None


def test_production_requires_gemini_ack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "GEMINI_DATA_USE_ACKNOWLEDGED", False)
    with pytest.raises(RuntimeError, match="GEMINI_DATA_USE_ACKNOWLEDGED"):
        create_app()
