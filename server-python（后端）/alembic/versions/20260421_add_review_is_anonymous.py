"""add review is_anonymous field

Revision ID: 20260421_add_review_is_anonymous
Revises: merge_20260421_b
Create Date: 2026-04-21 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260421_add_review_is_anonymous'
down_revision = 'merge_20260421_b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'reviews',
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default=sa.text('1'))
    )


def downgrade() -> None:
    op.drop_column('reviews', 'is_anonymous')

