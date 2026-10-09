"""add canteen_id to dish_categories

Revision ID: cat_canteen_fk
Revises: ct_canteen_close_tm
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cat_canteen_fk'
down_revision = 'ct_canteen_close_tm'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name'] for col in inspector.get_columns('dish_categories')}

    if 'canteen_id' not in columns:
        op.add_column('dish_categories', sa.Column('canteen_id', sa.Integer(), nullable=True))
        columns.add('canteen_id')

    indexes = {idx['name'] for idx in inspector.get_indexes('dish_categories')}
    if 'ix_dish_categories_canteen_id' not in indexes:
        op.create_index('ix_dish_categories_canteen_id', 'dish_categories', ['canteen_id'], unique=False)

    foreign_keys = {fk['name'] for fk in inspector.get_foreign_keys('dish_categories') if fk.get('name')}
    if 'fk_dish_categories_canteen_id_canteens' not in foreign_keys:
        op.create_foreign_key(
            'fk_dish_categories_canteen_id_canteens',
            'dish_categories',
            'canteens',
            ['canteen_id'],
            ['canteen_id'],
        )


def downgrade() -> None:
    op.drop_constraint('fk_dish_categories_canteen_id_canteens', 'dish_categories', type_='foreignkey')
    op.drop_index('ix_dish_categories_canteen_id', table_name='dish_categories')
    op.drop_column('dish_categories', 'canteen_id')

