from pathlib import Path
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations import storage
from app.models import Application
from app.repositories import applications as applications_repo
from tests.api.test_jobs import _create_job
from tests.support.pdfs import encrypted_pdf, simple_pdf


async def _upload(client: AsyncClient, pdf: bytes | None = None) -> Response:
    payload = pdf if pdf is not None else simple_pdf()
    return await client.post(
        f"{settings.API_V1_STR}/public/files",
        content=payload,
        headers={"Content-Type": "application/pdf"},
    )


async def _apply(
    client: AsyncClient,
    slug: str,
    email: str = "candidate@example.com",
    file_id: UUID | None = None,
) -> Response:
    if file_id is None:
        uploaded = await _upload(client)
        assert uploaded.status_code == 201
        file_id = UUID(uploaded.json()["id"])
    return await client.post(
        f"{settings.API_V1_STR}/public/jobs/{slug}/applications",
        json={"email": email, "file_id": str(file_id)},
    )


async def test_apply_stores_pdf_without_running_ocr(
    client: AsyncClient, db_session: AsyncSession, isolated_storage: Path
) -> None:
    job = await _create_job(client)

    response = await _apply(client, str(job["public_slug"]))

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "received"
    application = await applications_repo.get_by_id(db_session, UUID(body["id"]))
    assert application is not None
    assert application.extracted_text is None
    assert application.resume_storage_key is not None
    assert await storage.exists(application.resume_storage_key)
    stored = isolated_storage / application.resume_storage_key
    assert stored.is_file()


async def test_closed_job_rejects_applications(client: AsyncClient) -> None:
    job = await _create_job(client)
    await client.post(f"{settings.API_V1_STR}/jobs/{job['id']}/close")

    response = await _apply(client, str(job["public_slug"]))

    assert response.status_code == 409


async def test_unknown_slug_is_not_found(client: AsyncClient) -> None:
    response = await _apply(client, "missing-slug")
    assert response.status_code == 404


async def test_duplicate_email_is_conflict(client: AsyncClient) -> None:
    job = await _create_job(client)
    slug = str(job["public_slug"])

    first = await _apply(client, slug, email="candidate@example.com")
    second = await _apply(client, slug, email="candidate@example.com")

    assert first.status_code == 202
    assert second.status_code == 409


async def test_duplicate_email_is_case_insensitive(client: AsyncClient) -> None:
    job = await _create_job(client)
    slug = str(job["public_slug"])

    first = await _apply(client, slug, email="John@example.com")
    second = await _apply(client, slug, email="john@example.com")

    assert first.status_code == 202
    assert second.status_code == 409


async def test_unique_constraint_rejects_when_precheck_misses(
    client: AsyncClient,
    db_session: AsyncSession,
    isolated_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = await _create_job(client)
    slug = str(job["public_slug"])
    first = await _apply(client, slug, email="race@example.com")
    assert first.status_code == 202

    async def always_missing(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(
        "app.services.applications.applications_repo.get_by_job_and_email",
        always_missing,
    )

    second = await _apply(client, slug, email="race@example.com")

    assert second.status_code == 409
    count = await db_session.scalar(select(func.count()).select_from(Application))
    assert count == 1


async def test_missing_file_id_is_not_found(client: AsyncClient) -> None:
    job = await _create_job(client)
    response = await _apply(client, str(job["public_slug"]), file_id=uuid4())
    assert response.status_code == 404


async def test_rejects_non_pdf(client: AsyncClient) -> None:
    response = await _upload(client, pdf=b"this is not a pdf")
    assert response.status_code == 400


async def test_rejects_oversized_upload(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 512)
    response = await _upload(client, pdf=simple_pdf() + b"x" * 1024)
    assert response.status_code == 413


async def test_rejects_too_many_pages(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "MAX_RESUME_PAGES", 1)
    response = await _upload(client, pdf=simple_pdf(pages=2))
    assert response.status_code == 400


async def test_rejects_encrypted_pdf(client: AsyncClient) -> None:
    response = await _upload(client, pdf=encrypted_pdf())
    assert response.status_code == 400
