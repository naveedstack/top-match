from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExportEvent


async def add(session: AsyncSession, event: ExportEvent) -> ExportEvent:
    session.add(event)
    await session.flush()
    return event


async def list_for_job(session: AsyncSession, job_id: UUID) -> list[ExportEvent]:
    from sqlalchemy import select

    result = await session.execute(select(ExportEvent).where(ExportEvent.job_id == job_id))
    return list(result.scalars().all())
