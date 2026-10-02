from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExportEvent(Base):
    __tablename__ = "export_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="RESTRICT"),
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    application_ids: Mapped[list[str]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
