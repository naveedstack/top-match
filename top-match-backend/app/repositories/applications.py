from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Application, ApplicationStatus, Evaluation, Job


async def get_by_job_and_email(
    session: AsyncSession, job_id: UUID, email: str
) -> Application | None:
    result = await session.execute(
        select(Application).where(Application.job_id == job_id, Application.email == email)
    )
    return result.scalar_one_or_none()


async def get_by_id(
    session: AsyncSession, application_id: UUID, *, populate_existing: bool = False
) -> Application | None:
    stmt = (
        select(Application)
        .options(selectinload(Application.job), selectinload(Application.evaluation))
        .where(Application.id == application_id)
    )
    if populate_existing:
        stmt = stmt.execution_options(populate_existing=True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_id_and_recruiter(
    session: AsyncSession, application_id: UUID, recruiter_id: UUID
) -> Application | None:
    result = await session.execute(
        select(Application)
        .join(Job)
        .options(selectinload(Application.job), selectinload(Application.evaluation))
        .where(Application.id == application_id, Job.recruiter_id == recruiter_id)
    )
    return result.scalar_one_or_none()


async def get_by_storage_key(session: AsyncSession, storage_key: str) -> Application | None:
    result = await session.execute(
        select(Application).where(Application.resume_storage_key == storage_key)
    )
    return result.scalar_one_or_none()


async def add(session: AsyncSession, application: Application) -> Application:
    session.add(application)
    await session.flush()
    return application


async def claim_for_processing(
    session: AsyncSession, application_id: UUID, *, reclaim_processing: bool = False
) -> bool:
    allowed = [ApplicationStatus.RECEIVED, ApplicationStatus.FAILED]
    if reclaim_processing:
        allowed.append(ApplicationStatus.PROCESSING)
    result = await session.execute(
        update(Application)
        .where(Application.id == application_id, Application.status.in_(allowed))
        .values(status=ApplicationStatus.PROCESSING)
        .returning(Application.id)
        .execution_options(synchronize_session=False)
    )
    claimed = result.scalar_one_or_none() is not None
    if claimed:
        await session.commit()
    return claimed


async def list_stuck_ids(session: AsyncSession, cutoff: datetime) -> list[UUID]:
    result = await session.execute(
        select(Application.id).where(
            Application.status.in_((ApplicationStatus.RECEIVED, ApplicationStatus.PROCESSING)),
            Application.created_at <= cutoff,
        )
    )
    return list(result.scalars().all())


async def list_for_leaderboard(
    session: AsyncSession,
    job_id: UUID,
    *,
    status: ApplicationStatus | None,
    limit: int,
    offset: int,
) -> list[tuple[Application, bool]]:
    stmt = (
        select(Application, Evaluation.needs_review)
        .outerjoin(Evaluation, Evaluation.application_id == Application.id)
        .where(Application.job_id == job_id)
        .order_by(Application.score.desc().nulls_last(), Application.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    if status is not None:
        stmt = stmt.where(Application.status == status)
    result = await session.execute(stmt)
    rows: list[tuple[Application, bool]] = []
    for application, needs_review in result.all():
        rows.append((application, bool(needs_review)))
    return rows


async def count_for_leaderboard(
    session: AsyncSession, job_id: UUID, *, status: ApplicationStatus | None
) -> int:
    stmt = select(func.count()).select_from(Application).where(Application.job_id == job_id)
    if status is not None:
        stmt = stmt.where(Application.status == status)
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def list_for_export(
    session: AsyncSession, job_id: UUID, application_ids: list[UUID] | None, top_n: int | None
) -> list[Application]:
    stmt = (
        select(Application)
        .options(selectinload(Application.evaluation))
        .where(Application.job_id == job_id)
        .order_by(Application.score.desc().nulls_last(), Application.created_at.asc())
    )
    if application_ids is not None:
        stmt = stmt.where(Application.id.in_(application_ids))
    elif top_n is not None:
        stmt = stmt.limit(top_n)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_expired_for_purge(session: AsyncSession, cutoff: datetime) -> list[Application]:
    result = await session.execute(
        select(Application).join(Job).where(Job.closed_at.is_not(None), Job.closed_at <= cutoff)
    )
    return list(result.scalars().all())
