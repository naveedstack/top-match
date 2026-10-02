from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.application import Application


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        unique=True,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key_strengths: Mapped[list[str]] = mapped_column(JSONB)
    missing_requirements: Mapped[list[str]] = mapped_column(JSONB)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    is_resume: Mapped[bool] = mapped_column(Boolean)
    refusal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    injection_suspected: Mapped[bool] = mapped_column(Boolean)
    needs_review: Mapped[bool] = mapped_column(Boolean)
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    application: Mapped[Application] = relationship("Application", back_populates="evaluation")
