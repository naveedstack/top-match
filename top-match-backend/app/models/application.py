from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApplicationStatus, ScreeningPhase
from app.models.phase_result import screening_phase_enum

if TYPE_CHECKING:
    from app.models.application_attachment import ApplicationAttachment
    from app.models.evaluation import Evaluation
    from app.models.job import Job
    from app.models.phase_result import PhaseResult


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_id", "email", name="uq_applications_job_id_email"),
        Index("ix_applications_job_id_score", "job_id", "score"),
        Index("ix_applications_job_id_current_phase", "job_id", "current_phase"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320))
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            native_enum=True,
            values_callable=lambda members: [member.value for member in members],
            validate_strings=True,
        ),
        default=ApplicationStatus.RECEIVED,
    )
    resume_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    answers: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Furthest phase reached. A run resumes at the phase after this one.
    current_phase: Mapped[ScreeningPhase | None] = mapped_column(
        screening_phase_enum, nullable=True
    )
    # Phase that stopped the pipeline (fail or error); cleared when a run restarts.
    stopped_phase: Mapped[ScreeningPhase | None] = mapped_column(
        screening_phase_enum, nullable=True
    )
    # Machine-readable cause, e.g. knockout_failed, unreadable, not_resume, scoring_failed.
    stop_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    stop_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    job: Mapped[Job] = relationship("Job", back_populates="applications")
    evaluation: Mapped[Evaluation | None] = relationship(
        "Evaluation", back_populates="application", uselist=False
    )
    attachments: Mapped[list[ApplicationAttachment]] = relationship(
        "ApplicationAttachment",
        back_populates="application",
        cascade="all, delete-orphan",
    )
    phase_results: Mapped[list[PhaseResult]] = relationship(
        "PhaseResult",
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PhaseResult.created_at",
    )
