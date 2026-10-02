"""add evaluations

Revision ID: e5f9b2d1c8a4
Revises: d4e8a1c0b7f3
Create Date: 2026-10-02 15:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e5f9b2d1c8a4"
down_revision: str | Sequence[str] | None = "d4e8a1c0b7f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("key_strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("citations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_resume", sa.Boolean(), nullable=False),
        sa.Column("refusal_reason", sa.Text(), nullable=True),
        sa.Column("injection_suspected", sa.Boolean(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_evaluations_application_id_applications"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluations")),
        sa.UniqueConstraint("application_id", name=op.f("uq_evaluations_application_id")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("evaluations")
