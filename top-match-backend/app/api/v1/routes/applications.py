from uuid import UUID

from fastapi import APIRouter, Request, Response, status

from app.api.deps import CurrentRecruiter, DbSession
from app.api.v1.handlers.applications import handler as application_handlers
from app.core.rate_limit import limiter
from app.schemas.applications import (
    ApplicationAccepted,
    ApplicationCreate,
    ApplicationDetailResponse,
    AttachmentUploadUrlRequest,
    ResumeUploaded,
    UploadUrlRequest,
    UploadUrlResponse,
)

router = APIRouter(tags=["applications"])


def _job_slug_key(request: Request) -> str:
    return str(request.path_params.get("slug", "unknown"))


@router.post("/public/files/upload-url")
@limiter.limit("10/minute")
async def create_upload_url(
    request: Request, response: Response, body: UploadUrlRequest
) -> UploadUrlResponse:
    return await application_handlers.create_upload_url(request, body)


@router.put("/public/files/{file_id}/content", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def store_local_put(request: Request, response: Response, file_id: UUID) -> None:
    await application_handlers.store_local_put(file_id, request)


@router.post("/public/files/{file_id}/complete", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def complete_upload(request: Request, response: Response, file_id: UUID) -> ResumeUploaded:
    return await application_handlers.complete_upload(file_id)


@router.post("/public/jobs/{slug}/attachments/upload-url")
@limiter.limit("10/minute")
async def create_attachment_upload_url(
    request: Request, response: Response, slug: str, db: DbSession, body: AttachmentUploadUrlRequest
) -> UploadUrlResponse:
    return await application_handlers.create_attachment_upload_url(request, db, slug, body)


@router.put("/public/attachments/{file_id}/content", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def store_attachment_local_put(request: Request, response: Response, file_id: UUID) -> None:
    await application_handlers.store_attachment_local_put(file_id, request)


@router.post("/public/attachments/{file_id}/complete", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def complete_attachment_upload(
    request: Request, response: Response, file_id: UUID
) -> ResumeUploaded:
    return await application_handlers.complete_attachment_upload(file_id)


@router.post("/public/jobs/{slug}/applications", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("30/minute", key_func=_job_slug_key)
@limiter.limit("10/minute")
async def apply_to_job(
    request: Request, response: Response, slug: str, db: DbSession, body: ApplicationCreate
) -> ApplicationAccepted:
    return await application_handlers.apply_to_job(db, slug, body)


@router.get("/applications/{application_id}")
async def get_application(
    application_id: UUID, db: DbSession, recruiter: CurrentRecruiter
) -> ApplicationDetailResponse:
    return await application_handlers.get_application(db, recruiter, application_id)


@router.post("/applications/{application_id}/rescore")
async def rescore_application(
    application_id: UUID, db: DbSession, recruiter: CurrentRecruiter
) -> ApplicationAccepted:
    return await application_handlers.rescore_application(db, recruiter, application_id)


@router.post("/applications/{application_id}/move-forward")
async def move_forward(
    application_id: UUID, db: DbSession, recruiter: CurrentRecruiter
) -> ApplicationAccepted:
    return await application_handlers.move_forward(db, recruiter, application_id)


@router.post("/applications/{application_id}/mark-reviewed")
async def mark_reviewed(
    application_id: UUID, db: DbSession, recruiter: CurrentRecruiter
) -> ApplicationAccepted:
    return await application_handlers.mark_reviewed(db, recruiter, application_id)


@router.get("/public/resumes/{token}")
async def get_resume_pdf(token: str, db: DbSession) -> Response:
    return await application_handlers.get_resume_pdf(db, token)


@router.get("/public/attachments/{token}")
async def get_attachment(token: str, db: DbSession) -> Response:
    return await application_handlers.get_attachment_file(db, token)
