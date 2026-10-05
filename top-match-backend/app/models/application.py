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
from app.models.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.application_attachment import ApplicationAttachment
    from app.models.evaluation import Evaluation
    from app.models.job import Job


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_id", "email", name="uq_applications_job_id_email"),
        Index("ix_applications_job_id_score", "job_id", "score"),
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
