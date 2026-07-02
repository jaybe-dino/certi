"""add intake document types

Revision ID: a1b2c3d4e5f6
Revises: d97ad5c881ba
Create Date: 2026-07-02

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "d97ad5c881ba"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_VALUES = [
    "biz_registration",
    "factory_registration",
    "business_card",
    "product_brief",
    "ingredient_sheet",
]


def upgrade() -> None:
    # Postgres 12+: ADD VALUE is allowed outside an explicit transaction block.
    # IF NOT EXISTS makes this idempotent.
    for value in _NEW_VALUES:
        op.execute(f"ALTER TYPE document_type ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres cannot drop individual enum values; no-op.
    pass
