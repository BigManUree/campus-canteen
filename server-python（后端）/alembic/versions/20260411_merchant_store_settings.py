"""为商家店铺设置与库存预警补充字段

Revision ID: 20260411_merchant_store_settings
Revises: unify_user_roles_v2
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260411_merchant_store_settings"
down_revision = "unify_user_roles_v2"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "canteens", "avatar"):
        op.add_column("canteens", sa.Column("avatar", sa.String(length=255), nullable=True))
    if not _has_column(inspector, "canteens", "notice"):
        op.add_column("canteens", sa.Column("notice", sa.Text(), nullable=True))
    if not _has_column(inspector, "canteens", "notice_enabled"):
        op.add_column("canteens", sa.Column("notice_enabled", sa.Integer(), nullable=True, server_default="1"))
    if not _has_column(inspector, "canteens", "location"):
        op.add_column("canteens", sa.Column("location", sa.String(length=255), nullable=True))
    if not _has_column(inspector, "canteens", "business_hours"):
        op.add_column("canteens", sa.Column("business_hours", sa.String(length=100), nullable=True))
    if not _has_column(inspector, "canteens", "avg_price"):
        op.add_column("canteens", sa.Column("avg_price", sa.DECIMAL(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for column_name in ["avg_price", "business_hours", "location", "notice_enabled", "notice", "avatar"]:
        if _has_column(inspector, "canteens", column_name):
            op.drop_column("canteens", column_name)

