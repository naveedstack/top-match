"""add phase results and application phase columns

Revision ID: d2e6f8a0b3c5
Revises: c1d5e7f9a2b4
Create Date: 2026-10-07 17:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2e6f8a0b3c5"
down_revision: str | Sequence[str] | None = "c1d5e7f9a2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

screening_phase = postgresql.ENUM(
    "accept", "knockout", "answers", "resume", name="screening_phase", create_type=False
)
phase_outcome = postgresql.ENUM(
    "pass", "fail", "review", "error", "skipped", name="phase_outcome", create_type=False
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    screening_phase.create(bind, checkfirst=True)
    phase_outcome.create(bind, checkfirst=True)

    op.create_table(
        "phase_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("phase", screening_phase, nullable=False),
        sa.Column("outcome", phase_outcome, nullable=False),
        sa.Column(
            "reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("config_version", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=32), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("overridden_by_recruiter_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_phase_results_application_id_applications"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["overridden_by_recruiter_id"],
            ["recruiters.id"],
            name=op.f("fk_phase_results_overridden_by_recruiter_id_recruiters"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_phase_results")),
    )
    op.create_index(
        "ix_phase_results_application_id_created_at",
        "phase_results",
        ["application_id", "created_at"],
    )

    op.add_column("applications", sa.Column("current_phase", screening_phase, nullable=True))
    op.add_column("applications", sa.Column("stopped_phase", screening_phase, nullable=True))
    op.add_column("applications", sa.Column("stop_code", sa.String(length=40), nullable=True))
    op.add_column("applications", sa.Column("stop_reason", sa.Text(), nullable=True))
    op.add_column(
        "applications",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "applications", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        "ix_applications_job_id_current_phase", "applications", ["job_id", "current_phase"]
    )

    # Backfill: before this revision only the resume phase existed.
    op.execute(
        "UPDATE applications SET current_phase = 'resume' "
        "WHERE status IN ('scored', 'refused', 'failed')"
    )
    op.execute(
        "UPDATE applications AS a SET stopped_phase = 'resume', stop_code = 'not_resume', "
        "stop_reason = COALESCE("
        "(SELECT e.refusal_reason FROM evaluations AS e WHERE e.application_id = a.id), "
        "'Not recognized as a resume') "
        "WHERE a.status = 'refused'"
    )
    op.execute(
        "UPDATE applications SET stopped_phase = 'resume', stop_code = 'scoring_failed', "
        "stop_reason = 'Scoring failed' "
        "WHERE status = 'failed'"
    )
    # Rows still in flight restart from the beginning; give the stuck sweep a start time.
    op.execute(
        "UPDATE applications SET processing_started_at = created_at WHERE status = 'processing'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_applications_job_id_current_phase", table_name="applications")
    op.drop_column("applications", "reviewed_at")
    op.drop_column("applications", "processing_started_at")
    op.drop_column("applications", "stop_reason")
    op.drop_column("applications", "stop_code")
    op.drop_column("applications", "stopped_phase")
    op.drop_column("applications", "current_phase")
    op.drop_index("ix_phase_results_application_id_created_at", table_name="phase_results")
    op.drop_table("phase_results")
    bind = op.get_bind()
    phase_outcome.drop(bind, checkfirst=True)
    screening_phase.drop(bind, checkfirst=True)
