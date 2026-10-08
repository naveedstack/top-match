"""add knocked_out application status

Revision ID: c1d5e7f9a2b4
Revises: b9e3f7a2c4d1
Create Date: 2026-10-07 17:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c1d5e7f9a2b4"
down_revision: str | Sequence[str] | None = "b9e3f7a2c4d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_VALUES = "'received', 'processing', 'scored', 'refused', 'failed'"


def upgrade() -> None:
    """Upgrade schema."""
    # A new enum value cannot be used inside the transaction that adds it.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'knocked_out'")


def downgrade() -> None:
    """Downgrade schema.

    Postgres cannot drop an enum value, so the type is rebuilt. Knocked-out
    applications become 'failed' so recruiters can still retry them.
    """
    op.execute("UPDATE applications SET status = 'failed' WHERE status = 'knocked_out'")
    op.execute("ALTER TYPE application_status RENAME TO application_status_old")
    op.execute(f"CREATE TYPE application_status AS ENUM ({_OLD_VALUES})")
    op.execute(
        "ALTER TABLE applications ALTER COLUMN status TYPE application_status "
        "USING status::text::application_status"
    )
    op.execute("DROP TYPE application_status_old")
