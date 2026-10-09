"""add images field to activities

Revision ID: 6c2f8f9a1b3e
Revises: merge_sync_and_message_heads
Create Date: 2026-04-10 16:20:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c2f8f9a1b3e'
down_revision = 'merge_sync_and_message_heads'
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_column(inspector, 'activities', 'images'):
        op.add_column('activities', sa.Column('images', sa.Text(), nullable=True, comment='活动轮播图列表(JSON格式)'))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _has_column(inspector, 'activities', 'images'):
        op.drop_column('activities', 'images')

