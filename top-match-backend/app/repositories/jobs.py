from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Application, ApplicationStatus, Job


async def get_by_id_and_recruiter(
    session: AsyncSession, job_id: UUID, recruiter_id: UUID
) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == job_id, Job.recruiter_id == recruiter_id)
    )
    return result.scalar_one_or_none()


async def get_by_slug(session: AsyncSession, slug: str) -> Job | None:
    result = await session.execute(select(Job).where(Job.public_slug == slug))
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


async def count_applications_by_status(
    session: AsyncSession, job_id: UUID
) -> dict[ApplicationStatus, int]:
    result = await session.execute(
        select(Application.status, func.count())
        .where(Application.job_id == job_id)
        .group_by(Application.status)
    )
    counts = dict.fromkeys(ApplicationStatus, 0)
    for status, count in result.all():
        counts[status] = count
    return counts
