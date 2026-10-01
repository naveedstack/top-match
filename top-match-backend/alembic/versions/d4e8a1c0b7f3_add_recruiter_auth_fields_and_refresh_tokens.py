"""add recruiter auth fields and refresh tokens

Revision ID: d4e8a1c0b7f3
Revises: ba104e4775b2
Create Date: 2026-10-01 19:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e8a1c0b7f3"
down_revision: str | Sequence[str] | None = "ba104e4775b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Existing stub accounts cannot log in with this placeholder.


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("recruiters", sa.Column("company_name", sa.String(length=200), nullable=True))
    op.add_column("recruiters", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.execute(sa.text("UPDATE recruiters SET company_name = name WHERE company_name IS NULL"))
    op.execute(sa.text("UPDATE recruiters SET password_hash = '!' WHERE password_hash IS NULL"))
    op.alter_column(
        "recruiters",
        "company_name",
        existing_type=sa.String(length=200),
        nullable=False,
    )
    op.alter_column(
        "recruiters",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recruiter_id", sa.Uuid(), nullable=False),
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recruiter_id"],
            ["recruiters.id"],
            name=op.f("fk_refresh_tokens_recruiter_id_recruiters"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("jti", name=op.f("uq_refresh_tokens_jti")),
    )
    op.create_index(
        op.f("ix_refresh_tokens_recruiter_id"), "refresh_tokens", ["recruiter_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_refresh_tokens_recruiter_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_column("recruiters", "password_hash")
    op.drop_column("recruiters", "company_name")
