from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Application


async def get_by_job_and_email(
    session: AsyncSession, job_id: UUID, email: str
) -> Application | None:
    result = await session.execute(
        select(Application).where(Application.job_id == job_id, Application.email == email)
    )
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, application_id: UUID) -> Application | None:
    result = await session.execute(select(Application).where(Application.id == application_id))
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
