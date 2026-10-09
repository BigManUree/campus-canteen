"""rename dish_categories to windows and category fields to window fields

Revision ID: rename_windows_20260418
Revises: merge_20260418_heads
Create Date: 2026-04-18 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'rename_windows_20260418'
down_revision = 'merge_20260418_heads'
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(idx['name'] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, 'dish_categories') and not _has_table(inspector, 'windows'):
        op.rename_table('dish_categories', 'windows')
        inspector = inspect(bind)

    if _has_table(inspector, 'windows'):
        if _has_column(inspector, 'windows', 'category_id') and not _has_column(inspector, 'windows', 'window_id'):
            op.alter_column(
                'windows',
                'category_id',
                new_column_name='window_id',
                existing_type=sa.Integer(),
                existing_nullable=False,
                nullable=False,
                autoincrement=True,
            )
        if _has_column(inspector, 'windows', 'category_name') and not _has_column(inspector, 'windows', 'window_name'):
            op.alter_column('windows', 'category_name', new_column_name='window_name', existing_type=sa.String(length=50))

    inspector = inspect(bind)
    if _has_table(inspector, 'dishes'):
        if _has_column(inspector, 'dishes', 'category_id') and not _has_column(inspector, 'dishes', 'window_id'):
            op.alter_column(
                'dishes',
                'category_id',
                new_column_name='window_id',
                existing_type=sa.Integer(),
                existing_nullable=True,
                nullable=True,
            )

    inspector = inspect(bind)
    if _has_table(inspector, 'windows'):
        if _has_index(inspector, 'windows', 'ix_dish_categories_canteen_id'):
            op.drop_index('ix_dish_categories_canteen_id', table_name='windows')
        if not _has_index(inspector, 'windows', 'ix_windows_canteen_id'):
            op.create_index('ix_windows_canteen_id', 'windows', ['canteen_id'], unique=False)
        if not _has_index(inspector, 'windows', 'ix_windows_window_id'):
            op.create_index('ix_windows_window_id', 'windows', ['window_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, 'dishes'):
        if _has_column(inspector, 'dishes', 'window_id') and not _has_column(inspector, 'dishes', 'category_id'):
            op.alter_column(
                'dishes',
                'window_id',
                new_column_name='category_id',
                existing_type=sa.Integer(),
                existing_nullable=True,
                nullable=True,
            )

    inspector = inspect(bind)
    if _has_table(inspector, 'windows'):
        if _has_index(inspector, 'windows', 'ix_windows_window_id'):
            op.drop_index('ix_windows_window_id', table_name='windows')
        if _has_index(inspector, 'windows', 'ix_windows_canteen_id'):
            op.drop_index('ix_windows_canteen_id', table_name='windows')
        if not _has_index(inspector, 'windows', 'ix_dish_categories_canteen_id'):
            op.create_index('ix_dish_categories_canteen_id', 'windows', ['canteen_id'], unique=False)
        if _has_column(inspector, 'windows', 'window_name') and not _has_column(inspector, 'windows', 'category_name'):
            op.alter_column('windows', 'window_name', new_column_name='category_name', existing_type=sa.String(length=50))
        if _has_column(inspector, 'windows', 'window_id') and not _has_column(inspector, 'windows', 'category_id'):
            op.alter_column(
                'windows',
                'window_id',
                new_column_name='category_id',
                existing_type=sa.Integer(),
                existing_nullable=False,
                nullable=False,
                autoincrement=True,
            )

    inspector = inspect(bind)
    if _has_table(inspector, 'windows') and not _has_table(inspector, 'dish_categories'):
        op.rename_table('windows', 'dish_categories')

