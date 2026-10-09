"""fix cart price type

Revision ID: fix_cart_price_type
Revises: e43b01e412bb
Create Date: 2026-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fix_cart_price_type'
down_revision = 'e43b01e412bb'
branch_labels = None
depends_on = None


def upgrade():
    """修复购物车价格字段类型，从 INT 改为 DECIMAL(10,2)"""
    # 修改 cart_items 表的 price 字段类型
    op.alter_column('cart_items', 'price',
                    existing_type=mysql.INTEGER(),
                    type_=sa.DECIMAL(precision=10, scale=2),
                    existing_nullable=False,
                    comment='单价（以元为单位，与菜品表保持一致）')


def downgrade():
    """回滚到 INT 类型"""
    op.alter_column('cart_items', 'price',
                    existing_type=sa.DECIMAL(precision=10, scale=2),
                    type_=mysql.INTEGER(),
                    existing_nullable=False,
                    comment='单价（以分为单位）')

