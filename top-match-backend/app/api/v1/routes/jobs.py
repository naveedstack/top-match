from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentRecruiter, DbSession
from app.api.v1.handlers.jobs import handler as job_handlers
from app.models import ApplicationStatus
from app.schemas.applications import ExportRequest, LeaderboardResponse
from app.schemas.jobs import (
    JobCreate,
    JobDetailResponse,
    JobListItemResponse,
    JobResponse,
    JobUpdate,
    PublicJobResponse,
)

router = APIRouter(tags=["jobs"])


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(body: JobCreate, db: DbSession, recruiter: CurrentRecruiter) -> JobResponse:
    return await job_handlers.create_job(db, recruiter, body)


@router.get("/jobs")
async def list_jobs(db: DbSession, recruiter: CurrentRecruiter) -> list[JobListItemResponse]:
    return await job_handlers.list_jobs(db, recruiter)


@router.get("/jobs/{job_id}")
async def get_job(job_id: UUID, db: DbSession, recruiter: CurrentRecruiter) -> JobDetailResponse:
    return await job_handlers.get_job(db, recruiter, job_id)


@router.patch("/jobs/{job_id}")
async def update_job(
    job_id: UUID, body: JobUpdate, db: DbSession, recruiter: CurrentRecruiter
) -> JobResponse:
    return await job_handlers.update_job(db, recruiter, job_id, body)


@router.post("/jobs/{job_id}/close")
async def close_job(job_id: UUID, db: DbSession, recruiter: CurrentRecruiter) -> JobResponse:
    return await job_handlers.close_job(db, recruiter, job_id)


@router.get("/jobs/{job_id}/leaderboard")
async def get_leaderboard(
    job_id: UUID,
    db: DbSession,
    recruiter: CurrentRecruiter,
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LeaderboardResponse:
    return await job_handlers.get_leaderboard(db, recruiter, job_id, status_filter, limit, offset)


@router.post("/jobs/{job_id}/exports")
async def export_job(
    job_id: UUID, body: ExportRequest, db: DbSession, recruiter: CurrentRecruiter
) -> Response:
    content = await job_handlers.export_job(db, recruiter, job_id, body)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="job-{job_id}-export.csv"'},
    )


@router.get("/public/jobs/{slug}")
async def get_public_job(slug: str, db: DbSession) -> PublicJobResponse:
    return await job_handlers.get_public_job(db, slug)
