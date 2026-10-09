"""make dish_categories.canteen_id not null

Revision ID: cat_ct_not_null
Revises: backfill_cat_ct
Create Date: 2026-04-18 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = 'cat_ct_not_null'
down_revision = 'backfill_cat_ct'
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, 'dish_categories', 'canteen_id'):
        return

    remaining_null = bind.execute(
        text("SELECT COUNT(*) FROM dish_categories WHERE canteen_id IS NULL")
    ).scalar()

    if remaining_null and remaining_null > 0:
        raise RuntimeError(
            f"Cannot set dish_categories.canteen_id to NOT NULL, still has {remaining_null} NULL rows"
        )

    op.alter_column('dish_categories', 'canteen_id', existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_column(inspector, 'dish_categories', 'canteen_id'):
        op.alter_column('dish_categories', 'canteen_id', existing_type=sa.Integer(), nullable=True)

