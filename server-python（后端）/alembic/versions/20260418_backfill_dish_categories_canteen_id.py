"""backfill canteen_id for dish_categories from dishes

Revision ID: backfill_cat_ct
Revises: cat_canteen_fk
Create Date: 2026-04-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'backfill_cat_ct'
down_revision = 'cat_canteen_fk'
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, 'dish_categories', 'canteen_id'):
        return

    op.execute(
        sa.text(
            """
            UPDATE dish_categories dc
            JOIN (
                SELECT
                    d.category_id,
                    MIN(d.canteen_id) AS canteen_id
                FROM dishes d
                WHERE d.category_id IS NOT NULL
                  AND d.canteen_id IS NOT NULL
                GROUP BY d.category_id
                HAVING COUNT(DISTINCT d.canteen_id) = 1
            ) t ON t.category_id = dc.category_id
            SET dc.canteen_id = t.canteen_id
            WHERE dc.canteen_id IS NULL
            """
        )
    )


def downgrade() -> None:
    pass

