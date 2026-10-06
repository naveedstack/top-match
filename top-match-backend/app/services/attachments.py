from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AttachmentAlreadyUsedError,
    AttachmentNotFoundError,
    InvalidAttachmentError,
    JobClosedError,
    JobNotFoundError,
    ResumeTooLargeError,
)
from app.core.security import create_attachment_token, decode_attachment_token
from app.integrations import storage
from app.models import ApplicationAttachment, JobStatus
from app.repositories import attachments as attachments_repo
from app.repositories import jobs as jobs_repo
from app.schemas.forms import (
    ACCEPT_MIME,
    MIME_TO_ACCEPT,
    FileAccept,
    FileFormField,
    parse_form_fields,
)

_MAX_FILENAME = 255


@dataclass(frozen=True)
class PreparedAttachment:
    file_id: UUID
    field_id: UUID
    storage_key: str
    filename: str
    content_type: str
    byte_size: int


def attachment_storage_key(file_id: UUID) -> str:
    return f"attachments/{file_id}"


def attachment_meta_key(file_id: UUID) -> str:
    return f"attachments/{file_id}.meta.json"


def attachment_url_for(attachment_id: UUID) -> str:
    token = create_attachment_token(attachment_id)
    return f"{settings.API_V1_STR}/public/attachments/{token}"


def content_disposition(filename: str) -> str:
    ascii_name = filename.encode("ascii", "replace").decode("ascii").replace('"', "")
    if not ascii_name or ascii_name == "?" * len(ascii_name):
        ascii_name = "download"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


def sanitize_filename(name: str) -> str:
    base = Path(name).name.strip()
    if not base or base in {".", ".."}:
        raise InvalidAttachmentError("Invalid filename")
    return base[:_MAX_FILENAME]


def sniff_accept(data: bytes) -> FileAccept | None:
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if _is_docx(data):
        return "docx"
    return None


def _is_docx(data: bytes) -> bool:
    if not data.startswith(b"PK"):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
    except zipfile.BadZipFile:
        return False
    return "[Content_Types].xml" in names and any(name.startswith("word/") for name in names)


def _file_field(job_fields: object, field_id: UUID) -> FileFormField:
    for field in parse_form_fields(job_fields):
        if field.id == field_id and field.type == "file":
            return field
    raise InvalidAttachmentError("Unknown file field")


async def _read_meta(file_id: UUID) -> dict[str, Any] | None:
    key = attachment_meta_key(file_id)
    if not await storage.exists(key):
        return None
    try:
        payload = json.loads((await storage.get(key)).decode("utf-8"))
    except UnicodeDecodeError, json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


async def _write_meta(file_id: UUID, meta: dict[str, Any]) -> None:
    payload = json.dumps(meta).encode("utf-8")
    await storage.put(
        attachment_meta_key(file_id),
        payload,
        content_type="application/json",
    )


async def request_upload_url(
    session: AsyncSession,
    slug: str,
    file_id: UUID,
    *,
    field_id: UUID,
    filename: str,
    content_type: str,
    byte_size: int,
    put_url: str,
) -> storage.PresignedPut:
    job = await jobs_repo.get_by_slug(session, slug)
    if job is None:
        raise JobNotFoundError
    if job.status != JobStatus.OPEN:
        raise JobClosedError
    field = _file_field(job.form_fields, field_id)
    normalized_type = content_type.split(";")[0].strip().lower()
    allowed = {ACCEPT_MIME[item] for item in field.accept}
    if normalized_type not in allowed:
        raise InvalidAttachmentError("File type is not allowed for this field")
    if byte_size > settings.MAX_UPLOAD_BYTES:
        raise ResumeTooLargeError
    safe_name = sanitize_filename(filename)
    await _write_meta(
        file_id,
        {
            "content_type": normalized_type,
            "filename": safe_name,
            "field_id": str(field_id),
            "job_id": str(job.id),
            "byte_size": byte_size,
            "completed": False,
        },
    )
    return await storage.presign_put(
        attachment_storage_key(file_id),
        content_type=normalized_type,
        byte_size=byte_size,
        put_url=put_url,
    )


async def store_local_put(file_id: UUID, data: bytes, content_type: str) -> None:
    normalized_type = content_type.split(";")[0].strip().lower()
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise ResumeTooLargeError
    try:
        await storage.receive_local_put(
            attachment_storage_key(file_id),
            data,
            normalized_type,
        )
    except FileNotFoundError as exc:
        raise AttachmentNotFoundError from exc


async def confirm_attachment(file_id: UUID) -> UUID:
    key = attachment_storage_key(file_id)
    meta_key = attachment_meta_key(file_id)
    meta = await _read_meta(file_id)
    if meta is None:
        raise AttachmentNotFoundError
    obj = await storage.head(key)
    if obj is None:
        raise AttachmentNotFoundError
    expected_type = meta.get("content_type")
    expected_size = meta.get("byte_size")
    if obj.content_length > settings.MAX_UPLOAD_BYTES:
        await storage.delete(key)
        await storage.delete(meta_key)
        raise ResumeTooLargeError
    if not isinstance(expected_size, int) or obj.content_length != expected_size:
        await storage.delete(key)
        await storage.delete(meta_key)
        raise InvalidAttachmentError("Upload does not match the signed request")
    data = await storage.get(key)
    sniffed = sniff_accept(data)
    declared = MIME_TO_ACCEPT.get(expected_type) if isinstance(expected_type, str) else None
    if sniffed is None or declared is None or sniffed != declared:
        await storage.delete(key)
        await storage.delete(meta_key)
        raise InvalidAttachmentError("File type is not allowed for this field")
    meta["completed"] = True
    await _write_meta(file_id, meta)
    return file_id


async def load_prepared(
    session: AsyncSession,
    file_id: UUID,
    *,
    job_id: UUID,
    field_id: UUID,
    accept: list[FileAccept],
) -> PreparedAttachment:
    meta = await _read_meta(file_id)
    if meta is None or meta.get("completed") is not True:
        raise AttachmentNotFoundError
    if meta.get("job_id") != str(job_id) or meta.get("field_id") != str(field_id):
        raise InvalidAttachmentError("File does not belong to this field")
    content_type = meta.get("content_type")
    filename = meta.get("filename")
    byte_size = meta.get("byte_size")
    declared = MIME_TO_ACCEPT.get(content_type) if isinstance(content_type, str) else None
    if declared is None or declared not in accept:
        raise InvalidAttachmentError("File type is not allowed for this field")
    if not isinstance(filename, str) or not filename:
        raise InvalidAttachmentError("Invalid filename")
    if not isinstance(byte_size, int) or byte_size < 1:
        raise InvalidAttachmentError("File is empty")
    storage_key = attachment_storage_key(file_id)
    if not await storage.exists(storage_key):
        raise AttachmentNotFoundError
    if await attachments_repo.get_by_storage_key(session, storage_key) is not None:
        raise AttachmentAlreadyUsedError
    return PreparedAttachment(
        file_id=file_id,
        field_id=field_id,
        storage_key=storage_key,
        filename=filename,
        content_type=content_type if isinstance(content_type, str) else "",
        byte_size=byte_size,
    )


async def get_attachment_file(session: AsyncSession, token: str) -> tuple[bytes, str, str]:
    attachment_id = decode_attachment_token(token)
    attachment = await attachments_repo.get_by_id(session, attachment_id)
    if attachment is None:
        raise AttachmentNotFoundError
    if not await storage.exists(attachment.storage_key):
        raise AttachmentNotFoundError
    payload = await storage.get(attachment.storage_key)
    return payload, attachment.content_type, attachment.filename


async def delete_storage(attachment: ApplicationAttachment) -> None:
    await storage.delete(attachment.storage_key)
    file_id = _file_id_from_key(attachment.storage_key)
    if file_id is not None:
        await storage.delete(attachment_meta_key(file_id))


def _file_id_from_key(storage_key: str) -> UUID | None:
    name = storage_key.rsplit("/", 1)[-1]
    try:
        return UUID(name)
    except ValueError:
        return None
