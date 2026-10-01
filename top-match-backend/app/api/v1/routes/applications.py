from fastapi import APIRouter, Request, Response, status

from app.api.deps import DbSession
from app.api.v1.handlers.applications import handler as application_handlers
from app.core.rate_limit import limiter
from app.schemas.applications import ApplicationAccepted, ApplicationCreate, ResumeUploaded

router = APIRouter(tags=["applications"])


def _job_slug_key(request: Request) -> str:
    return str(request.path_params.get("slug", "unknown"))


@router.post("/public/files", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_resume(request: Request, response: Response) -> ResumeUploaded:
    return await application_handlers.upload_resume(request)


@router.post("/public/jobs/{slug}/applications", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("30/minute", key_func=_job_slug_key)
@limiter.limit("10/minute")
async def apply_to_job(
    request: Request,
    response: Response,
    slug: str,
    db: DbSession,
    body: ApplicationCreate,
) -> ApplicationAccepted:
    return await application_handlers.apply_to_job(db, slug, body)
