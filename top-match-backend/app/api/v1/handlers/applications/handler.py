from uuid import UUID, uuid4

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AttachmentNotFoundError,
    InvalidResumeError,
    ResumeNotFoundError,
    ResumeTooLargeError,
)
from app.models import Recruiter
from app.schemas.applications import (
    ApplicationAccepted,
    ApplicationCreate,
    ApplicationDetailResponse,
    AttachmentUploadUrlRequest,
    ResumeUploaded,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.services import applications as applications_service
from app.services import attachments as attachments_service


def _local_put_url(request: Request, file_id: UUID) -> str:
    return (
        f"{str(request.base_url).rstrip('/')}{settings.API_V1_STR}/public/files/{file_id}/content"
    )


def _local_attachment_put_url(request: Request, file_id: UUID) -> str:
    return (
        f"{str(request.base_url).rstrip('/')}"
        f"{settings.API_V1_STR}/public/attachments/{file_id}/content"
    )


async def create_upload_url(request: Request, body: UploadUrlRequest) -> UploadUrlResponse:
    file_id = uuid4()
    presigned = await applications_service.request_upload_url(
        file_id,
        content_type=body.content_type,
        byte_size=body.byte_size,
        put_url=_local_put_url(request, file_id),
    )
    return UploadUrlResponse(
        file_id=file_id,
        upload_url=presigned.url,
        headers=presigned.headers,
        expires_at=presigned.expires_at,
    )


async def _read_limited_body(request: Request, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise ResumeTooLargeError
        chunks.append(chunk)
    if not chunks:
        raise InvalidResumeError("File is empty")
    return b"".join(chunks)


async def store_local_put(file_id: UUID, request: Request) -> None:
    # Direct PUTs exist only for local storage; S3 uploads go to the presigned URL.
    if settings.STORAGE_BACKEND != "local":
        raise ResumeNotFoundError
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    pdf_bytes = await _read_limited_body(request, settings.MAX_UPLOAD_BYTES)
    await applications_service.store_local_put(file_id, pdf_bytes, content_type)


async def complete_upload(file_id: UUID) -> ResumeUploaded:
    confirmed = await applications_service.confirm_resume(file_id)
    return ResumeUploaded(id=confirmed)


async def create_attachment_upload_url(
    request: Request, db: AsyncSession, slug: str, body: AttachmentUploadUrlRequest
) -> UploadUrlResponse:
    file_id = uuid4()
    presigned = await attachments_service.request_upload_url(
        db,
        slug,
        file_id,
        field_id=body.field_id,
        filename=body.filename,
        content_type=body.content_type,
        byte_size=body.byte_size,
        put_url=_local_attachment_put_url(request, file_id),
    )
    return UploadUrlResponse(
        file_id=file_id,
        upload_url=presigned.url,
        headers=presigned.headers,
        expires_at=presigned.expires_at,
    )


async def store_attachment_local_put(file_id: UUID, request: Request) -> None:
    if settings.STORAGE_BACKEND != "local":
        raise AttachmentNotFoundError
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    payload = await _read_limited_body(request, settings.MAX_UPLOAD_BYTES)
    await attachments_service.store_local_put(file_id, payload, content_type)


async def complete_attachment_upload(file_id: UUID) -> ResumeUploaded:
    confirmed = await attachments_service.confirm_attachment(file_id)
    return ResumeUploaded(id=confirmed)


async def apply_to_job(db: AsyncSession, slug: str, body: ApplicationCreate) -> ApplicationAccepted:
    application = await applications_service.apply_to_job(
        db, slug, str(body.email), body.file_id, body.answers
    )
    return ApplicationAccepted(id=application.id, status=application.status)


async def get_application(
    db: AsyncSession, recruiter: Recruiter, application_id: UUID
) -> ApplicationDetailResponse:
    return await applications_service.get_owned_detail(db, application_id, recruiter.id)


async def rescore_application(
    db: AsyncSession, recruiter: Recruiter, application_id: UUID
) -> ApplicationAccepted:
    application = await applications_service.rescore(db, application_id, recruiter)
    return ApplicationAccepted(id=application.id, status=application.status)


async def move_forward(
    db: AsyncSession, recruiter: Recruiter, application_id: UUID
) -> ApplicationAccepted:
    application = await applications_service.move_forward(db, application_id, recruiter)
    return ApplicationAccepted(id=application.id, status=application.status)


async def mark_reviewed(
    db: AsyncSession, recruiter: Recruiter, application_id: UUID
) -> ApplicationAccepted:
    application = await applications_service.mark_reviewed(db, application_id, recruiter)
    return ApplicationAccepted(id=application.id, status=application.status)


async def get_resume_pdf(db: AsyncSession, token: str) -> Response:
    pdf_bytes = await applications_service.get_resume_pdf(db, token)
    return Response(content=pdf_bytes, media_type="application/pdf")


async def get_attachment_file(db: AsyncSession, token: str) -> Response:
    payload, content_type, filename = await attachments_service.get_attachment_file(db, token)
    return Response(
        content=payload,
        media_type=content_type,
        headers={
            "Content-Disposition": attachments_service.content_disposition(filename),
            "X-Content-Type-Options": "nosniff",
        },
    )
