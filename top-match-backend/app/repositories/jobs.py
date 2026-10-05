from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Application, ApplicationStatus, Job


async def get_by_id_and_recruiter(
    session: AsyncSession, job_id: UUID, recruiter_id: UUID
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == job_id, Job.recruiter_id == recruiter_id)
    )
    return result.scalar_one_or_none()


async def get_by_slug(session: AsyncSession, slug: str) -> Job | None:
    result = await session.execute(
        select(Job).options(selectinload(Job.recruiter)).where(Job.public_slug == slug)
    )
    return result.scalar_one_or_none()


async def list_for_recruiter(session: AsyncSession, recruiter_id: UUID) -> list[Job]:
    result = await session.execute(
        select(Job).where(Job.recruiter_id == recruiter_id).order_by(Job.created_at.desc())
    )
    return list(result.scalars().all())


async def add(session: AsyncSession, job: Job) -> Job:
    session.add(job)
    await session.flush()
    return job


def _empty_status_counts() -> dict[ApplicationStatus, int]:
    return dict.fromkeys(ApplicationStatus, 0)


async def count_applications_by_status(
    session: AsyncSession, job_id: UUID
) -> dict[ApplicationStatus, int]:
    counts_by_job = await count_applications_by_status_for_jobs(session, [job_id])
    return counts_by_job.get(job_id, _empty_status_counts())


async def count_applications_by_status_for_jobs(
    session: AsyncSession, job_ids: list[UUID]
) -> dict[UUID, dict[ApplicationStatus, int]]:
    counts_by_job = {job_id: _empty_status_counts() for job_id in job_ids}
    if not job_ids:
        return counts_by_job
    result = await session.execute(
        select(Application.job_id, Application.status, func.count())
        .where(Application.job_id.in_(job_ids))
        .group_by(Application.job_id, Application.status)
    )
    for job_id, status, count in result.all():
        counts_by_job[job_id][status] = count
    return counts_by_job


async def has_applications(session: AsyncSession, job_id: UUID) -> bool:
    result = await session.execute(
        select(Application.id).where(Application.job_id == job_id).limit(1)
    )
    return result.scalar_one_or_none() is not None
