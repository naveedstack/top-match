from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Request, Response, status

from app.api.deps import CurrentRecruiter, DbSession
from app.api.v1.handlers.applications import handler as application_handlers
from app.core.config import settings
from app.core.exceptions import ResumeNotFoundError
from app.core.rate_limit import limiter
from app.schemas.applications import (
    ApplicationAccepted,
    ApplicationCreate,
    ApplicationDetailResponse,
    ResumeUploaded,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.services.pipeline import process_application

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
    if settings.STORAGE_BACKEND != "local":
        raise ResumeNotFoundError
    await application_handlers.store_local_put(file_id, request)


@router.post("/public/files/{file_id}/complete", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def complete_upload(request: Request, response: Response, file_id: UUID) -> ResumeUploaded:
    return await application_handlers.complete_upload(file_id)


@router.post("/public/jobs/{slug}/applications", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("30/minute", key_func=_job_slug_key)
@limiter.limit("10/minute")
async def apply_to_job(
    request: Request,
    response: Response,
    slug: str,
    db: DbSession,
    body: ApplicationCreate,
    background_tasks: BackgroundTasks,
) -> ApplicationAccepted:
    accepted = await application_handlers.apply_to_job(db, slug, body)
    if settings.PIPELINE_ENABLED:
        background_tasks.add_task(process_application, accepted.id)
    return accepted


@router.get("/applications/{application_id}")
async def get_application(
    application_id: UUID, db: DbSession, recruiter: CurrentRecruiter
) -> ApplicationDetailResponse:
    return await application_handlers.get_application(db, recruiter, application_id)


@router.post("/applications/{application_id}/rescore")
async def rescore_application(
    application_id: UUID,
    db: DbSession,
    recruiter: CurrentRecruiter,
    background_tasks: BackgroundTasks,
) -> ApplicationAccepted:
    accepted = await application_handlers.rescore_application(db, recruiter, application_id)
    if settings.PIPELINE_ENABLED:
        background_tasks.add_task(process_application, accepted.id, reclaim_processing=True)
    return accepted


@router.get("/public/resumes/{token}")
async def get_resume_pdf(token: str, db: DbSession) -> Response:
    pdf_bytes = await application_handlers.get_resume_pdf(db, token)
    return Response(content=pdf_bytes, media_type="application/pdf")
