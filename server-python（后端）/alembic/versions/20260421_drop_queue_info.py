"""drop queue_info table

Revision ID: 20260421_drop_queue_info
Revises: merge_20260421_b
Create Date: 2026-04-21 23:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260421_drop_queue_info'
down_revision = 'merge_20260421_b'
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(idx['name'] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, 'queue_info'):
        return

    if _has_index(inspector, 'queue_info', 'ix_queue_info_queue_id'):
        op.drop_index('ix_queue_info_queue_id', table_name='queue_info')

    op.drop_table('queue_info')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, 'queue_info'):
        return

    op.create_table(
        'queue_info',
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('canteen_id', sa.Integer(), nullable=False),
        sa.Column('current_queue_number', sa.Integer(), nullable=True),
        sa.Column('estimated_wait_time', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('update_time', sa.DateTime(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['canteen_id'], ['canteens.canteen_id']),
        sa.PrimaryKeyConstraint('queue_id')
    )
    op.create_index('ix_queue_info_queue_id', 'queue_info', ['queue_id'], unique=False)

