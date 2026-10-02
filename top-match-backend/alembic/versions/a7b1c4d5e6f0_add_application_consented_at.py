"""add application consented_at

Revision ID: a7b1c4d5e6f0
Revises: f6a0c3e2d9b5
Create Date: 2026-10-02 16:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7b1c4d5e6f0"
down_revision: str | Sequence[str] | None = "f6a0c3e2d9b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "applications",
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("applications", "consented_at")
