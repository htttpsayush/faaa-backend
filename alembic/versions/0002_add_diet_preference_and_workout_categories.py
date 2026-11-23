"""Add diet_preference to users, category and exercises to workouts

Revision ID: 0002_categories_diet
Revises: 0001_initial_schema
Create Date: 2026-11-21 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_categories_diet'
down_revision: Union[str, Sequence[str], None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add diet_preference to users
    op.add_column(
        'users',
        sa.Column('diet_preference', sa.String(length=20), nullable=False, server_default='any')
    )

    # 2. Add category and exercises to workouts
    op.add_column(
        'workouts',
        sa.Column('category', sa.String(length=50), nullable=False, server_default='gym')
    )
    op.create_index(op.f('ix_workouts_category'), 'workouts', ['category'], unique=False)
    op.add_column(
        'workouts',
        sa.Column('exercises', sa.JSON(), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('workouts', 'exercises')
    op.drop_index(op.f('ix_workouts_category'), table_name='workouts')
    op.drop_column('workouts', 'category')
    op.drop_column('users', 'diet_preference')
