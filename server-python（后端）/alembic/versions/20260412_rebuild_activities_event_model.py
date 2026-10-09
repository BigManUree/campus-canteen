"""rebuild activities for production event management

Revision ID: 20260412_rebuild_activities_event_model
Revises: 20260411_merge_heads
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '20260412_evt_model'
down_revision = '20260411_merge_heads'
branch_labels = None
depends_on = None


OLD_COLUMNS = {
    'description',
    'activity_type',
    'discount_type',
    'discount_value',
    'target_dish_ids',
    'image',
    'images',
    'registration_required',
    'participant_limit',
    'publish_scope',
    'target_canteen_ids',
    'signup_start_time',
    'signup_end_time',
}

NEW_TEXT_COLUMNS = {
    'subtitle': 255,
    'cover_image': 255,
    'organizer': 100,
    'location': 255,
    'contact_name': 50,
    'contact_phone': 30,
}


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_column(inspector, 'activities', 'description') and not _has_column(inspector, 'activities', 'content'):
        op.alter_column('activities', 'description', new_column_name='content', existing_type=sa.Text(), existing_nullable=True)

    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_column(inspector, 'activities', 'image') and not _has_column(inspector, 'activities', 'cover_image'):
        op.alter_column('activities', 'image', new_column_name='cover_image', existing_type=sa.String(length=255), existing_nullable=True)

    bind = op.get_bind()
    inspector = inspect(bind)

    for name, length in NEW_TEXT_COLUMNS.items():
        if not _has_column(inspector, 'activities', name):
            op.add_column('activities', sa.Column(name, sa.String(length), nullable=True))

    if not _has_column(inspector, 'activities', 'sort_order'):
        op.add_column('activities', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('activities')}
    for column_name in OLD_COLUMNS:
        if column_name in existing_columns:
            op.drop_column('activities', column_name)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, 'activities', 'description') and _has_column(inspector, 'activities', 'content'):
        op.alter_column('activities', 'content', new_column_name='description', existing_type=sa.Text(), existing_nullable=True)

    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, 'activities', 'image') and _has_column(inspector, 'activities', 'cover_image'):
        op.alter_column('activities', 'cover_image', new_column_name='image', existing_type=sa.String(length=255), existing_nullable=True)

    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, 'activities', 'activity_type'):
        op.add_column('activities', sa.Column('activity_type', sa.Enum('seckill', 'discount', 'full_reduction', 'package', 'gift', 'other'), nullable=True))
    if not _has_column(inspector, 'activities', 'discount_type'):
        op.add_column('activities', sa.Column('discount_type', sa.String(length=50), nullable=True))
    if not _has_column(inspector, 'activities', 'discount_value'):
        op.add_column('activities', sa.Column('discount_value', sa.DECIMAL(10, 2), nullable=True))
    if not _has_column(inspector, 'activities', 'target_dish_ids'):
        op.add_column('activities', sa.Column('target_dish_ids', sa.Text(), nullable=True))
    if not _has_column(inspector, 'activities', 'images'):
        op.add_column('activities', sa.Column('images', sa.Text(), nullable=True))

    for name in ['subtitle', 'organizer', 'location', 'contact_name', 'contact_phone', 'sort_order']:
        bind = op.get_bind()
        inspector = inspect(bind)
        if _has_column(inspector, 'activities', name):
            op.drop_column('activities', name)
