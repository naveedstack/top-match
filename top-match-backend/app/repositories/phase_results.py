from uuid import UUID

from sqlalchemy import case, column, distinct, exists, func, select, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models import Application, PhaseOutcome, PhaseResult, ReasonCode, ScreeningPhase


async def add(session: AsyncSession, phase_result: PhaseResult) -> PhaseResult:
    session.add(phase_result)
    await session.flush()
    return phase_result


async def count_knockouts_by_field(
    session: AsyncSession, job_id: UUID
) -> dict[UUID, tuple[int, int]]:
    """Per knockout field: (applications it ever stopped, of those later moved forward)."""
    reason = (
        func.jsonb_array_elements(PhaseResult.reasons)
        .table_valued(column("value", JSONB))
        .render_derived(name="reason")
    )
    override = aliased(PhaseResult)
    moved_forward = exists().where(
        override.application_id == PhaseResult.application_id,
        override.phase == ScreeningPhase.KNOCKOUT,
        override.overridden_by_recruiter_id.is_not(None),
    )
    field_id = reason.c.value["field_id"].astext
    statement = (
        select(
            field_id,
            func.count(distinct(PhaseResult.application_id)),
            func.count(distinct(case((moved_forward, PhaseResult.application_id)))),
        )
        .select_from(PhaseResult)
        .join(Application, Application.id == PhaseResult.application_id)
        .join(reason, true())
        .where(
            Application.job_id == job_id,
            PhaseResult.phase == ScreeningPhase.KNOCKOUT,
            PhaseResult.outcome == PhaseOutcome.FAIL,
            reason.c.value["code"].astext == ReasonCode.KNOCKOUT_FAILED.value,
        )
        .group_by(field_id)
    )
    rows = await session.execute(statement)
    return {UUID(row[0]): (row[1], row[2]) for row in rows}
