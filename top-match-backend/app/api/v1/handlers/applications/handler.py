from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidResumeError, ResumeTooLargeError
from app.schemas.applications import ApplicationAccepted, ApplicationCreate, ResumeUploaded
from app.services import applications as applications_service

_ALLOWED_UPLOAD_TYPES = {"application/pdf", "application/octet-stream"}


async def _read_limited_body(request: Request) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > settings.MAX_UPLOAD_BYTES:
            raise ResumeTooLargeError
        chunks.append(chunk)
    if not chunks:
        raise InvalidResumeError("File is empty")
    return b"".join(chunks)


async def upload_resume(request: Request) -> ResumeUploaded:
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type not in _ALLOWED_UPLOAD_TYPES:
        raise InvalidResumeError("File is not a PDF")
    pdf_bytes = await _read_limited_body(request)
    file_id = await applications_service.store_resume(pdf_bytes)
    return ResumeUploaded(id=file_id)


async def apply_to_job(db: AsyncSession, slug: str, body: ApplicationCreate) -> ApplicationAccepted:
    application = await applications_service.apply_to_job(db, slug, str(body.email), body.file_id)
    return ApplicationAccepted(id=application.id, status=application.status)
