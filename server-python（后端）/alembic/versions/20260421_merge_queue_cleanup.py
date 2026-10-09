"""merge review anonymous and drop queue heads

Revision ID: 20260421_merge_queue_cleanup
Revises: 20260421_add_review_is_anonymous, 20260421_drop_queue_info
Create Date: 2026-04-21 23:30:00.000000
"""

# revision identifiers, used by Alembic.
revision = '20260421_merge_queue_cleanup'
down_revision = ('20260421_add_review_is_anonymous', '20260421_drop_queue_info')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

