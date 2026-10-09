"""add message and canteen fields

Revision ID: add_message_fields
Revises: fix_cart_price_type
Create Date: 2026-03-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_message_fields'
down_revision = 'fix_cart_price_type'
branch_labels = None
depends_on = None


def upgrade():
    # 给 messages 表添加新字段
    try:
        op.add_column('messages', sa.Column('title', sa.String(100), server_default='系统通知'))
    except Exception:
        pass  # 字段已存在
    
    try:
        op.add_column('messages', sa.Column('message_type', sa.String(20), server_default='system'))
    except Exception:
        pass
    
    try:
        op.add_column('messages', sa.Column('read_time', sa.DateTime(), nullable=True))
    except Exception:
        pass
    
    # 给 canteens 表添加商家用户ID字段
    try:
        op.add_column('canteens', sa.Column('merchant_user_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_canteens_merchant_user', 'canteens', 'users', ['merchant_user_id'], ['user_id'])
        op.create_index('idx_canteens_merchant_user_id', 'canteens', ['merchant_user_id'])
    except Exception:
        pass


def downgrade():
    # 删除添加的字段
    try:
        op.drop_constraint('fk_canteens_merchant_user', 'canteens', type_='foreignkey')
        op.drop_index('idx_canteens_merchant_user_id', 'canteens')
        op.drop_column('canteens', 'merchant_user_id')
    except Exception:
        pass
    
    try:
        op.drop_column('messages', 'read_time')
        op.drop_column('messages', 'message_type')
        op.drop_column('messages', 'title')
    except Exception:
        pass

