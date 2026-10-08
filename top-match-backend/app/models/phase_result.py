from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PhaseOutcome, ScreeningPhase

if TYPE_CHECKING:
    from app.models.application import Application

screening_phase_enum = Enum(
    ScreeningPhase,
    name="screening_phase",
    native_enum=True,
    values_callable=lambda members: [member.value for member in members],
    validate_strings=True,
)

phase_outcome_enum = Enum(
    PhaseOutcome,
    name="phase_outcome",
    native_enum=True,
    values_callable=lambda members: [member.value for member in members],
    validate_strings=True,
)


class PhaseResult(Base):
    """One row per phase run (or recruiter override). Rows are never updated."""

    __tablename__ = "phase_results"
    __table_args__ = (
        Index("ix_phase_results_application_id_created_at", "application_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
    )
    phase: Mapped[ScreeningPhase] = mapped_column(screening_phase_enum)
    outcome: Mapped[PhaseOutcome] = mapped_column(phase_outcome_enum)
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    config_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overridden_by_recruiter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    application: Mapped[Application] = relationship("Application", back_populates="phase_results")
