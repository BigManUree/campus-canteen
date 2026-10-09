"""add canteen extra fields

Revision ID: ct_canteen_extra_fd
Revises: ct_canteen_close_tm
Create Date: 2026-04-15 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'ct_canteen_extra_fd'
down_revision = 'ct_canteen_close_tm'
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, 'canteens', 'description'):
        op.add_column('canteens', sa.Column('description', sa.Text(), nullable=True))
    if not _has_column(inspector, 'canteens', 'contact_person'):
        op.add_column('canteens', sa.Column('contact_person', sa.String(length=50), nullable=True))
    if not _has_column(inspector, 'canteens', 'rest_days'):
        op.add_column('canteens', sa.Column('rest_days', sa.String(length=100), nullable=True))
    if not _has_column(inspector, 'canteens', 'sort_order'):
        op.add_column('canteens', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    for column in ['sort_order', 'rest_days', 'contact_person', 'description']:
        bind = op.get_bind()
        inspector = inspect(bind)
        if _has_column(inspector, 'canteens', column):
            op.drop_column('canteens', column)

