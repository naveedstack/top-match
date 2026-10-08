from uuid import UUID

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationStatus, Recruiter, ScreeningPhase
from app.schemas.applications import ExportRequest, LeaderboardResponse
from app.schemas.jobs import (
    JobCreate,
    JobDetailResponse,
    JobListItemResponse,
    JobResponse,
    JobUpdate,
    PublicJobResponse,
)
from app.services import applications as applications_service
from app.services import exports as exports_service
from app.services import jobs as jobs_service


async def create_job(db: AsyncSession, recruiter: Recruiter, body: JobCreate) -> JobResponse:
    job = await jobs_service.create_job(db, recruiter, body)
    return jobs_service.to_job_response(job, recruiter)


async def list_jobs(db: AsyncSession, recruiter: Recruiter) -> list[JobListItemResponse]:
    return await jobs_service.list_jobs_with_counts(db, recruiter)


async def get_job(db: AsyncSession, recruiter: Recruiter, job_id: UUID) -> JobDetailResponse:
    return await jobs_service.get_job_detail(db, job_id, recruiter)


async def update_job(
    db: AsyncSession, recruiter: Recruiter, job_id: UUID, body: JobUpdate
) -> JobResponse:
    job = await jobs_service.update_job(db, job_id, recruiter.id, body)
    return jobs_service.to_job_response(job, recruiter)


async def close_job(db: AsyncSession, recruiter: Recruiter, job_id: UUID) -> JobResponse:
    job = await jobs_service.close_job(db, job_id, recruiter.id)
    return jobs_service.to_job_response(job, recruiter)


async def get_public_job(db: AsyncSession, slug: str) -> PublicJobResponse:
    job = await jobs_service.get_public_job(db, slug)
    return jobs_service.to_public_response(job)


async def get_leaderboard(
    db: AsyncSession,
    recruiter: Recruiter,
    job_id: UUID,
    statuses: list[ApplicationStatus] | None,
    stage: ScreeningPhase | None,
    limit: int,
    offset: int,
) -> LeaderboardResponse:
    return await applications_service.get_leaderboard(
        db, job_id, recruiter.id, statuses=statuses, stage=stage, limit=limit, offset=offset
    )


async def export_job(
    db: AsyncSession, recruiter: Recruiter, job_id: UUID, body: ExportRequest
) -> Response:
    content, _ids = await exports_service.export_job(db, job_id, recruiter, body)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="job-{job_id}-export.csv"'},
    )
