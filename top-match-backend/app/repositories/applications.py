from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import ColumnElement, and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Application, ApplicationStatus, Evaluation, Job, ScreeningPhase


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
        .options(
            selectinload(Application.job),
            selectinload(Application.evaluation),
            selectinload(Application.attachments),
            selectinload(Application.phase_results),
        )
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
        .options(
            selectinload(Application.job),
            selectinload(Application.evaluation),
            selectinload(Application.attachments),
            selectinload(Application.phase_results),
        )
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
    allowed = [ApplicationStatus.RECEIVED]
    if reclaim_processing:
        allowed.append(ApplicationStatus.PROCESSING)
    result = await session.execute(
        update(Application)
        .where(Application.id == application_id, Application.status.in_(allowed))
        .values(status=ApplicationStatus.PROCESSING, processing_started_at=datetime.now(UTC))
        .returning(Application.id)
        .execution_options(synchronize_session=False)
    )
    claimed = result.scalar_one_or_none() is not None
    if claimed:
        await session.commit()
    return claimed


async def delete(session: AsyncSession, application: Application) -> None:
    await session.delete(application)
    await session.flush()


async def list_stuck_ids(session: AsyncSession, cutoff: datetime) -> list[UUID]:
    """Received rows never picked up, and processing rows with no progress since `cutoff`."""
    result = await session.execute(
        select(Application.id).where(
            or_(
                and_(
                    Application.status == ApplicationStatus.RECEIVED,
                    Application.created_at <= cutoff,
                ),
                and_(
                    Application.status == ApplicationStatus.PROCESSING,
                    func.coalesce(Application.processing_started_at, Application.created_at)
                    <= cutoff,
                ),
            )
        )
    )
    return list(result.scalars().all())


def _leaderboard_filters(
    job_id: UUID,
    statuses: list[ApplicationStatus] | None,
    stage: ScreeningPhase | None,
) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = [Application.job_id == job_id]
    if statuses:
        filters.append(Application.status.in_(statuses))
    if stage is not None:
        filters.append(Application.current_phase == stage)
    return filters


async def list_for_leaderboard(
    session: AsyncSession,
    job_id: UUID,
    *,
    statuses: list[ApplicationStatus] | None,
    stage: ScreeningPhase | None = None,
    limit: int,
    offset: int,
) -> list[tuple[Application, bool]]:
    stmt = (
        select(Application, Evaluation.needs_review)
        .outerjoin(Evaluation, Evaluation.application_id == Application.id)
        .where(*_leaderboard_filters(job_id, statuses, stage))
        .order_by(Application.score.desc().nulls_last(), Application.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    rows: list[tuple[Application, bool]] = []
    for application, needs_review in result.all():
        rows.append((application, bool(needs_review)))
    return rows


async def count_for_leaderboard(
    session: AsyncSession,
    job_id: UUID,
    *,
    statuses: list[ApplicationStatus] | None,
    stage: ScreeningPhase | None = None,
) -> int:
    stmt = (
        select(func.count())
        .select_from(Application)
        .where(*_leaderboard_filters(job_id, statuses, stage))
    )
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def list_for_export(
    session: AsyncSession, job_id: UUID, application_ids: list[UUID] | None, top_n: int | None
) -> list[Application]:
    stmt = (
        select(Application)
        .options(
            selectinload(Application.evaluation),
            selectinload(Application.attachments),
            selectinload(Application.phase_results),
        )
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
        select(Application)
        .join(Job)
        .options(selectinload(Application.attachments))
        .where(Job.closed_at.is_not(None), Job.closed_at <= cutoff)
    )
    return list(result.scalars().all())
