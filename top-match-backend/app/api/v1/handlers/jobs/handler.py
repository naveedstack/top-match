from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recruiter
from app.schemas.jobs import (
    JobCreate,
    JobDetailResponse,
    JobResponse,
    JobUpdate,
    PublicJobResponse,
)
from app.services import jobs as jobs_service


async def create_job(db: AsyncSession, recruiter: Recruiter, body: JobCreate) -> JobResponse:
    job = await jobs_service.create_job(db, recruiter, body)
    return jobs_service.to_job_response(job)


async def list_jobs(db: AsyncSession, recruiter: Recruiter) -> list[JobResponse]:
    jobs = await jobs_service.list_jobs(db, recruiter.id)
    return [jobs_service.to_job_response(job) for job in jobs]


async def get_job(db: AsyncSession, recruiter: Recruiter, job_id: UUID) -> JobDetailResponse:
    return await jobs_service.get_job_detail(db, job_id, recruiter.id)


async def update_job(
    db: AsyncSession, recruiter: Recruiter, job_id: UUID, body: JobUpdate
) -> JobResponse:
    job = await jobs_service.update_job(db, job_id, recruiter.id, body)
    return jobs_service.to_job_response(job)


async def close_job(db: AsyncSession, recruiter: Recruiter, job_id: UUID) -> JobResponse:
    job = await jobs_service.close_job(db, job_id, recruiter.id)
    return jobs_service.to_job_response(job)


async def get_public_job(db: AsyncSession, slug: str) -> PublicJobResponse:
    job = await jobs_service.get_public_job(db, slug)
    return jobs_service.to_public_response(job)
