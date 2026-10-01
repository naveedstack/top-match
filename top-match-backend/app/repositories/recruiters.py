from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recruiter, RefreshToken


async def get_by_email(session: AsyncSession, email: str) -> Recruiter | None:
    result = await session.execute(select(Recruiter).where(Recruiter.email == email))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, recruiter_id: UUID) -> Recruiter | None:
    result = await session.execute(select(Recruiter).where(Recruiter.id == recruiter_id))
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    *,
    email: str,
    name: str,
    company_name: str,
    password_hash: str,
) -> Recruiter:
    recruiter = Recruiter(
        email=email,
        name=name,
        company_name=company_name,
        password_hash=password_hash,
    )
    session.add(recruiter)
    await session.flush()
    return recruiter


async def add_refresh_token(
    session: AsyncSession,
    *,
    recruiter_id: UUID,
    jti: str,
    expires_at: datetime,
) -> RefreshToken:
    record = RefreshToken(recruiter_id=recruiter_id, jti=jti, expires_at=expires_at)
    session.add(record)
    await session.flush()
    return record


async def revoke_active_refresh_token(session: AsyncSession, jti: str) -> bool:
    now = datetime.now(UTC)
    result = await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.jti == jti,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .values(revoked_at=now)
        .returning(RefreshToken.id)
        .execution_options(synchronize_session=False)
    )
    return result.scalar_one_or_none() is not None
