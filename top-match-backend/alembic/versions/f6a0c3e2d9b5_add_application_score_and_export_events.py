"""add application score and export events

Revision ID: f6a0c3e2d9b5
Revises: e5f9b2d1c8a4
Create Date: 2026-10-02 15:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a0c3e2d9b5"
down_revision: str | Sequence[str] | None = "e5f9b2d1c8a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("applications", sa.Column("score", sa.Integer(), nullable=True))
    op.create_index("ix_applications_job_id_score", "applications", ["job_id", "score"])
    op.create_table(
        "export_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recruiter_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("application_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_export_events_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recruiter_id"],
            ["recruiters.id"],
            name=op.f("fk_export_events_recruiter_id_recruiters"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_events")),
    )
    op.create_index(op.f("ix_export_events_job_id"), "export_events", ["job_id"], unique=False)
    op.create_index(
        op.f("ix_export_events_recruiter_id"), "export_events", ["recruiter_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_export_events_recruiter_id"), table_name="export_events")
    op.drop_index(op.f("ix_export_events_job_id"), table_name="export_events")
    op.drop_table("export_events")
    op.drop_index("ix_applications_job_id_score", table_name="applications")
    op.drop_column("applications", "score")
