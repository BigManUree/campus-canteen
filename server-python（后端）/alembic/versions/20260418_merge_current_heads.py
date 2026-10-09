"""merge current alembic heads

Revision ID: merge_20260418_heads
Revises: ct_canteen_extra_fd, cat_ct_not_null, add_review_reply_fields
Create Date: 2026-04-18 00:20:00.000000
"""

from alembic import op


revision = 'merge_20260418_heads'
down_revision = ('ct_canteen_extra_fd', 'cat_ct_not_null', 'add_review_reply_fields')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

