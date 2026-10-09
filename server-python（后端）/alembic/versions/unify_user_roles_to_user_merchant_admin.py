"""统一用户角色值为 user / merchant / admin

Revision ID: unify_user_roles_v2
Revises: merge_sync_and_message_heads
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'unify_user_roles_v2'
down_revision = 'merge_sync_and_message_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    bind.execute(sa.text("UPDATE users SET role = 'user' WHERE role IN ('student', 'user')"))
    bind.execute(sa.text("UPDATE users SET role = 'merchant' WHERE role IN ('canteen_admin', 'merchant')"))
    bind.execute(sa.text("UPDATE users SET role = 'admin' WHERE role IN ('sys_admin', 'admin')"))

    op.execute(
        "ALTER TABLE users MODIFY COLUMN role ENUM('user','merchant','admin') DEFAULT 'user'"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role ENUM('student','merchant','admin','user','canteen_admin','sys_admin') DEFAULT 'student'"
    )

