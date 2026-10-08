from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PhaseResult


async def add(session: AsyncSession, phase_result: PhaseResult) -> PhaseResult:
    session.add(phase_result)
    await session.flush()
    return phase_result
