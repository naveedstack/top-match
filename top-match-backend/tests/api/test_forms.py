from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import UUID, uuid4
from zipfile import ZipFile

import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations import storage
from app.models import Job
from app.repositories import applications as applications_repo
from app.schemas.forms import ACCEPT_MIME
from app.services.attachments import attachment_meta_key, attachment_storage_key
from app.services.ingestion import IngestionResult
from app.services.pipeline import process_application
from app.services.retention import purge_expired_applications
from tests.api.test_applications import _apply, _upload
from tests.api.test_jobs import JOB_BODY
from tests.api.test_pipeline import RESUME_TEXT, FakeCompleter, _evaluation


def _text_field(**overrides: object) -> dict[str, object]:
    field: dict[str, object] = {
        "id": str(uuid4()),
        "type": "text",
        "label": "Cover note",
        "required": True,
        "multiline": True,
        "max_length": 200,
    }
    field.update(overrides)
    return field


def _number_field(**overrides: object) -> dict[str, object]:
    field: dict[str, object] = {
        "id": str(uuid4()),
        "type": "number",
        "label": "Years of experience",
        "required": True,
        "integer_only": True,
        "min": 0,
        "max": 40,
    }
    field.update(overrides)
    return field


def _dropdown_field(**overrides: object) -> dict[str, object]:
    field: dict[str, object] = {
        "id": str(uuid4()),
        "type": "dropdown",
        "label": "Work authorization",
        "required": True,
        "options": ["Authorized", "Needs sponsorship"],
    }
    field.update(overrides)
    return field


def _radio_field(**overrides: object) -> dict[str, object]:
    field: dict[str, object] = {
        "id": str(uuid4()),
        "type": "radio",
        "label": "Relocation",
        "required": False,
        "options": ["Yes", "No"],
    }
    field.update(overrides)
    return field


def _checkboxes_field(**overrides: object) -> dict[str, object]:
    field: dict[str, object] = {
        "id": str(uuid4()),
        "type": "checkboxes",
        "label": "Skills",
        "required": True,
        "options": ["Python", "Go", "Rust"],
    }
    field.update(overrides)
    return field


def _file_field(**overrides: object) -> dict[str, object]:
    field: dict[str, object] = {
        "id": str(uuid4()),
        "type": "file",
        "label": "Portfolio",
        "required": True,
        "accept": ["png", "jpeg"],
    }
    field.update(overrides)
    return field


def _png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 32


def _docx() -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


@pytest.fixture
def fake_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _extract(_pdf_bytes: bytes) -> IngestionResult:
        return IngestionResult(text=RESUME_TEXT, page_count=1, duration_ms=1, too_empty=False)

    monkeypatch.setattr("app.services.pipeline.extract_text", _extract)


async def _create_job_with_form(
    client: AsyncClient, fields: list[dict[str, object]]
) -> dict[str, object]:
    response = await client.post(
        f"{settings.API_V1_STR}/jobs",
        json={**JOB_BODY, "form_fields": fields},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _upload_attachment(
    client: AsyncClient,
    slug: str,
    field_id: str,
    payload: bytes,
    content_type: str,
    filename: str,
) -> Response:
    signed = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{slug}/attachments/upload-url",
        json={
            "field_id": field_id,
            "filename": filename,
            "content_type": content_type,
            "byte_size": len(payload),
        },
    )
    if signed.status_code != 200:
        return signed
    body = signed.json()
    put = await client.put(body["upload_url"], content=payload, headers=body["headers"])
    if put.status_code != 204:
        return put
    return await client.post(f"{settings.API_V1_STR}/public/attachments/{body['file_id']}/complete")


async def test_create_job_stores_form_fields(client: AsyncClient) -> None:
    text = _text_field()
    created = await _create_job_with_form(client, [text])

    assert created["form_fields"][0]["id"] == text["id"]
    assert created["form_fields"][0]["type"] == "text"

    public = await client.get(f"{settings.API_V1_STR}/public/jobs/{created['public_slug']}")
    assert public.status_code == 200
    assert public.json()["form_fields"][0]["label"] == "Cover note"

    detail = await client.get(f"{settings.API_V1_STR}/jobs/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["form_locked"] is False


async def test_invalid_form_definitions_are_rejected(client: AsyncClient) -> None:
    too_many = [_text_field(required=False) for _ in range(21)]
    too_many_files = [_file_field(required=False) for _ in range(6)]
    duplicate_id = str(uuid4())
    one_option = _dropdown_field(options=["Only"])

    over = await client.post(
        f"{settings.API_V1_STR}/jobs", json={**JOB_BODY, "form_fields": too_many}
    )
    files = await client.post(
        f"{settings.API_V1_STR}/jobs", json={**JOB_BODY, "form_fields": too_many_files}
    )
    dupes = await client.post(
        f"{settings.API_V1_STR}/jobs",
        json={
            **JOB_BODY,
            "form_fields": [_text_field(id=duplicate_id), _number_field(id=duplicate_id)],
        },
    )
    options = await client.post(
        f"{settings.API_V1_STR}/jobs", json={**JOB_BODY, "form_fields": [one_option]}
    )

    assert over.status_code == 422
    assert files.status_code == 422
    assert dupes.status_code == 422
    assert options.status_code == 422


async def test_form_is_locked_after_first_application(client: AsyncClient) -> None:
    text = _text_field()
    job = await _create_job_with_form(client, [text])
    applied = await _apply(
        client,
        str(job["public_slug"]),
        email="locked@example.com",
    )
    # apply without answers should 422 because required field
    assert applied.status_code == 422

    uploaded = await _upload(client)
    assert uploaded.status_code == 201
    accepted = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}/applications",
        json={
            "email": "locked@example.com",
            "file_id": uploaded.json()["id"],
            "consented": True,
            "answers": {str(text["id"]): "Hello"},
        },
    )
    assert accepted.status_code == 202

    locked = await client.patch(
        f"{settings.API_V1_STR}/jobs/{job['id']}",
        json={"form_fields": [_text_field()]},
    )
    title = await client.patch(
        f"{settings.API_V1_STR}/jobs/{job['id']}",
        json={"title": "Still editable"},
    )
    detail = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}")

    assert locked.status_code == 409
    assert title.status_code == 200
    assert title.json()["title"] == "Still editable"
    assert detail.json()["form_locked"] is True


async def test_answer_validation_rules(client: AsyncClient) -> None:
    text = _text_field()
    number = _number_field()
    dropdown = _dropdown_field()
    boxes = _checkboxes_field()
    extra_id = str(uuid4())
    job = await _create_job_with_form(client, [text, number, dropdown, boxes])
    slug = str(job["public_slug"])
    uploaded = await _upload(client)
    assert uploaded.status_code == 201
    url = f"{settings.API_V1_STR}/public/jobs/{slug}/applications"
    file_id = uploaded.json()["id"]

    missing = await client.post(
        url,
        json={"email": "a@example.com", "file_id": file_id, "consented": True, "answers": {}},
    )
    unknown = await client.post(
        url,
        json={
            "email": "a@example.com",
            "file_id": file_id,
            "consented": True,
            "answers": {
                str(text["id"]): "Hi",
                str(number["id"]): 3,
                str(dropdown["id"]): "Authorized",
                str(boxes["id"]): ["Python"],
                extra_id: "nope",
            },
        },
    )
    bad_number = await client.post(
        url,
        json={
            "email": "a@example.com",
            "file_id": file_id,
            "consented": True,
            "answers": {
                str(text["id"]): "Hi",
                str(number["id"]): 3.5,
                str(dropdown["id"]): "Authorized",
                str(boxes["id"]): ["Python"],
            },
        },
    )
    bad_option = await client.post(
        url,
        json={
            "email": "a@example.com",
            "file_id": file_id,
            "consented": True,
            "answers": {
                str(text["id"]): "Hi",
                str(number["id"]): 3,
                str(dropdown["id"]): "Martian",
                str(boxes["id"]): ["Python"],
            },
        },
    )

    assert missing.status_code == 422
    assert missing.json()["field_errors"][str(text["id"])] == "This field is required"
    assert unknown.status_code == 422
    assert unknown.json()["field_errors"][extra_id] == "Unknown field"
    assert bad_number.status_code == 422
    assert "whole number" in bad_number.json()["field_errors"][str(number["id"])]
    assert bad_option.status_code == 422
    assert bad_option.json()["field_errors"][str(dropdown["id"])] == "Select a valid option"


async def test_optional_fields_can_be_omitted(client: AsyncClient) -> None:
    optional = _radio_field(required=False)
    job = await _create_job_with_form(client, [optional])
    uploaded = await _upload(client)
    assert uploaded.status_code == 201
    response = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}/applications",
        json={
            "email": "optional@example.com",
            "file_id": uploaded.json()["id"],
            "consented": True,
            "answers": {},
        },
    )
    assert response.status_code == 202


async def test_attachment_upload_complete_apply_detail_and_download(
    client: AsyncClient,
) -> None:
    file_field = _file_field()
    text = _text_field(required=False)
    job = await _create_job_with_form(client, [file_field, text])
    slug = str(job["public_slug"])
    png = _png()
    uploaded_file = await _upload_attachment(
        client, slug, str(file_field["id"]), png, "image/png", "shot.png"
    )
    assert uploaded_file.status_code == 201
    attachment_id = uploaded_file.json()["id"]
    resume = await _upload(client)
    assert resume.status_code == 201

    applied = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{slug}/applications",
        json={
            "email": "files@example.com",
            "file_id": resume.json()["id"],
            "consented": True,
            "answers": {str(file_field["id"]): attachment_id},
        },
    )
    assert applied.status_code == 202

    detail = await client.get(f"{settings.API_V1_STR}/applications/{applied.json()['id']}")
    assert detail.status_code == 200
    answers = detail.json()["answers"]
    file_answer = next(item for item in answers if item["type"] == "file")
    assert file_answer["filename"] == "shot.png"
    assert file_answer["download_url"]

    downloaded = await client.get(file_answer["download_url"])
    assert downloaded.status_code == 200
    assert downloaded.content == png
    assert downloaded.headers["content-type"] == "image/png"
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert "shot.png" in downloaded.headers["content-disposition"]


async def test_attachment_complete_rejects_wrong_magic_and_deletes(
    client: AsyncClient,
) -> None:
    file_field = _file_field(accept=["png"])
    job = await _create_job_with_form(client, [file_field])
    slug = str(job["public_slug"])
    signed = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{slug}/attachments/upload-url",
        json={
            "field_id": str(file_field["id"]),
            "filename": "shot.png",
            "content_type": "image/png",
            "byte_size": 20,
        },
    )
    assert signed.status_code == 200
    body = signed.json()
    put = await client.put(
        body["upload_url"], content=b"not-a-png-file!!!!!!", headers=body["headers"]
    )
    assert put.status_code == 204
    file_id = UUID(body["file_id"])
    key = attachment_storage_key(file_id)

    response = await client.post(f"{settings.API_V1_STR}/public/attachments/{file_id}/complete")

    assert response.status_code == 400
    assert not await storage.exists(key)
    assert not await storage.exists(attachment_meta_key(file_id))


async def test_attachment_sign_rejects_disallowed_type(client: AsyncClient) -> None:
    file_field = _file_field(accept=["png"])
    job = await _create_job_with_form(client, [file_field])
    response = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}/attachments/upload-url",
        json={
            "field_id": str(file_field["id"]),
            "filename": "doc.docx",
            "content_type": ACCEPT_MIME["docx"],
            "byte_size": len(_docx()),
        },
    )
    assert response.status_code == 400


async def test_incomplete_attachment_is_rejected_on_apply(client: AsyncClient) -> None:
    file_field = _file_field()
    job = await _create_job_with_form(client, [file_field])
    slug = str(job["public_slug"])
    resume = await _upload(client)
    assert resume.status_code == 201
    response = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{slug}/applications",
        json={
            "email": "missing-file@example.com",
            "file_id": resume.json()["id"],
            "consented": True,
            "answers": {str(file_field["id"]): str(uuid4())},
        },
    )
    assert response.status_code == 422
    assert response.json()["field_errors"][str(file_field["id"])] == "Upload a file"


async def test_retention_deletes_attachments(client: AsyncClient, db_session: AsyncSession) -> None:
    file_field = _file_field()
    job = await _create_job_with_form(client, [file_field])
    slug = str(job["public_slug"])
    uploaded_file = await _upload_attachment(
        client, slug, str(file_field["id"]), _png(), "image/png", "shot.png"
    )
    assert uploaded_file.status_code == 201
    resume = await _upload(client)
    assert resume.status_code == 201
    applied = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{slug}/applications",
        json={
            "email": "retain@example.com",
            "file_id": resume.json()["id"],
            "consented": True,
            "answers": {str(file_field["id"]): uploaded_file.json()["id"]},
        },
    )
    assert applied.status_code == 202
    application_id = UUID(applied.json()["id"])
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.attachments
    storage_key = application.attachments[0].storage_key
    await client.post(f"{settings.API_V1_STR}/jobs/{job['id']}/close")

    record = await db_session.get(Job, UUID(str(job["id"])))
    assert record is not None
    record.closed_at = datetime.now(UTC) - timedelta(days=settings.RETENTION_DAYS + 1)
    await db_session.commit()

    counts = await purge_expired_applications(db_session)

    assert counts["purged"] == 1
    assert await applications_repo.get_by_id(db_session, application_id) is None
    assert not await storage.exists(storage_key)


async def test_csv_includes_custom_field_columns(
    client: AsyncClient, db_session: AsyncSession, fake_ocr: None
) -> None:
    text = _text_field()
    job = await _create_job_with_form(client, [text])
    resume = await _upload(client)
    assert resume.status_code == 201
    applied = await client.post(
        f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}/applications",
        json={
            "email": "csv@example.com",
            "file_id": resume.json()["id"],
            "consented": True,
            "answers": {str(text["id"]): "=1+1"},
        },
    )
    assert applied.status_code == 202
    application_id = UUID(applied.json()["id"])
    await process_application(
        application_id,
        db_session,
        completer=FakeCompleter(_evaluation(80, strengths=["FastAPI"])),
    )

    response = await client.post(
        f"{settings.API_V1_STR}/jobs/{job['id']}/exports",
        json={"application_ids": [str(application_id)]},
    )

    assert response.status_code == 200
    assert "Cover note" in response.text
    assert "'=1+1" in response.text


async def test_docx_and_jpeg_attachments_complete(client: AsyncClient) -> None:
    jpeg_field = _file_field(accept=["jpeg"], required=False)
    docx_field = _file_field(accept=["docx"], required=False, label="Writing sample")
    job = await _create_job_with_form(client, [jpeg_field, docx_field])
    slug = str(job["public_slug"])
    jpeg = await _upload_attachment(
        client, slug, str(jpeg_field["id"]), _jpeg(), "image/jpeg", "photo.jpg"
    )
    docx = await _upload_attachment(
        client,
        slug,
        str(docx_field["id"]),
        _docx(),
        ACCEPT_MIME["docx"],
        "sample.docx",
    )
    assert jpeg.status_code == 201
    assert docx.status_code == 201
