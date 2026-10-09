"""add order viewed timestamps to users

Revision ID: ord_viewed_20260421
Revises: merge_20260418_heads
Create Date: 2026-04-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'ord_viewed_20260421'
down_revision = 'merge_20260418_heads'
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, 'users', 'order_viewed_all_at'):
        op.add_column('users', sa.Column('order_viewed_all_at', sa.DateTime(), nullable=True))
    if not _has_column(inspector, 'users', 'order_viewed_pending_at'):
        op.add_column('users', sa.Column('order_viewed_pending_at', sa.DateTime(), nullable=True))
    if not _has_column(inspector, 'users', 'order_viewed_preparing_at'):
        op.add_column('users', sa.Column('order_viewed_preparing_at', sa.DateTime(), nullable=True))
    if not _has_column(inspector, 'users', 'order_viewed_ready_at'):
        op.add_column('users', sa.Column('order_viewed_ready_at', sa.DateTime(), nullable=True))
    if not _has_column(inspector, 'users', 'order_viewed_delivering_at'):
        op.add_column('users', sa.Column('order_viewed_delivering_at', sa.DateTime(), nullable=True))
    if not _has_column(inspector, 'users', 'order_viewed_refund_at'):
        op.add_column('users', sa.Column('order_viewed_refund_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_column(inspector, 'users', 'order_viewed_refund_at'):
        op.drop_column('users', 'order_viewed_refund_at')
    if _has_column(inspector, 'users', 'order_viewed_delivering_at'):
        op.drop_column('users', 'order_viewed_delivering_at')
    if _has_column(inspector, 'users', 'order_viewed_ready_at'):
        op.drop_column('users', 'order_viewed_ready_at')
    if _has_column(inspector, 'users', 'order_viewed_preparing_at'):
        op.drop_column('users', 'order_viewed_preparing_at')
    if _has_column(inspector, 'users', 'order_viewed_pending_at'):
        op.drop_column('users', 'order_viewed_pending_at')
    if _has_column(inspector, 'users', 'order_viewed_all_at'):
        op.drop_column('users', 'order_viewed_all_at')

