"""add review reply fields

Revision ID: add_review_reply_fields
Revises: 90d17b7035e9
Create Date: 2026-04-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_review_reply_fields'
down_revision = '90d17b7035e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('reviews', sa.Column('reply_content', sa.Text(), nullable=True))
    op.add_column('reviews', sa.Column('reply_time', sa.DateTime(), nullable=True))
    op.add_column('reviews', sa.Column('reply_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_reviews_reply_user_id_users',
        'reviews',
        'users',
        ['reply_user_id'],
        ['user_id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_reviews_reply_user_id_users', 'reviews', type_='foreignkey')
    op.drop_column('reviews', 'reply_user_id')
    op.drop_column('reviews', 'reply_time')
    op.drop_column('reviews', 'reply_content')

