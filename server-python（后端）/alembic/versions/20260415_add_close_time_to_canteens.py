"""add close_time to canteens

Revision ID: ct_canteen_close_tm
Revises: 20260412_rebuild_activities_event_model
Create Date: 2026-04-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ct_canteen_close_tm'
down_revision = '20260412_evt_model'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('canteens', sa.Column('close_time', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('canteens', 'close_time')
