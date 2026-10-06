from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationAttachment


async def get_by_storage_key(
    session: AsyncSession, storage_key: str
) -> ApplicationAttachment | None:
    result = await session.execute(
        select(ApplicationAttachment).where(ApplicationAttachment.storage_key == storage_key)
    )
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, attachment_id: UUID) -> ApplicationAttachment | None:
    result = await session.execute(
        select(ApplicationAttachment).where(ApplicationAttachment.id == attachment_id)
    )
    return result.scalar_one_or_none()


async def add(session: AsyncSession, attachment: ApplicationAttachment) -> ApplicationAttachment:
    session.add(attachment)
    await session.flush()
    return attachment
