from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Evaluation


async def add(session: AsyncSession, evaluation: Evaluation) -> Evaluation:
    session.add(evaluation)
    await session.flush()
    return evaluation


async def get_by_application_id(session: AsyncSession, application_id: UUID) -> Evaluation | None:
    result = await session.execute(
        select(Evaluation).where(Evaluation.application_id == application_id)
    )
    return result.scalar_one_or_none()


async def delete_by_application_id(session: AsyncSession, application_id: UUID) -> None:
    existing = await get_by_application_id(session, application_id)
    if existing is not None:
        await session.delete(existing)
        await session.flush()
