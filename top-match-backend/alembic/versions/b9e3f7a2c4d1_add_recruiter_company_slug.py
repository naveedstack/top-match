"""add recruiter company_slug

Revision ID: b9e3f7a2c4d1
Revises: c8d2e4f6a1b3
Create Date: 2026-10-03 13:56:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.slugs import numbered_slug, reserved_or_base_slug

revision: str = "b9e3f7a2c4d1"
down_revision: str | Sequence[str] | None = "c8d2e4f6a1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recruiters", sa.Column("company_slug", sa.String(length=80), nullable=True))
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, company_name FROM recruiters")).mappings().all()
    taken: set[str] = set()
    for row in rows:
        base = reserved_or_base_slug(row["company_name"])
        n = 1
        while True:
            candidate = numbered_slug(base, n)
            if candidate not in taken:
                taken.add(candidate)
                conn.execute(
                    sa.text("UPDATE recruiters SET company_slug = :slug WHERE id = :id"),
                    {"slug": candidate, "id": row["id"]},
                )
                break
            n += 1
    op.alter_column(
        "recruiters", "company_slug", existing_type=sa.String(length=80), nullable=False
    )
    op.create_unique_constraint(op.f("uq_recruiters_company_slug"), "recruiters", ["company_slug"])


def downgrade() -> None:
    op.drop_constraint(op.f("uq_recruiters_company_slug"), "recruiters", type_="unique")
    op.drop_column("recruiters", "company_slug")
