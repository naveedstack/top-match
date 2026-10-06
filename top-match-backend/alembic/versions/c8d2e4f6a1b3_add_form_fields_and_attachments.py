"""add form fields and application attachments

Revision ID: c8d2e4f6a1b3
Revises: a7b1c4d5e6f0
Create Date: 2026-10-03 13:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c8d2e4f6a1b3"
down_revision: str | Sequence[str] | None = "a7b1c4d5e6f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "form_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "applications",
        sa.Column(
            "answers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_table(
        "application_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=200), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_application_attachments_application_id_applications"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_attachments")),
        sa.UniqueConstraint(
            "application_id",
            "field_id",
            name="uq_application_attachments_application_id_field_id",
        ),
        sa.UniqueConstraint("storage_key", name=op.f("uq_application_attachments_storage_key")),
    )
    op.create_index(
        op.f("ix_application_attachments_application_id"),
        "application_attachments",
        ["application_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_application_attachments_application_id"),
        table_name="application_attachments",
    )
    op.drop_table("application_attachments")
    op.drop_column("applications", "answers")
    op.drop_column("jobs", "form_fields")
