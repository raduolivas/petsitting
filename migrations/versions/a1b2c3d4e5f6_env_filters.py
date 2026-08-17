"""add environment filter fields

Revision ID: a1b2c3d4e5f6
Revises: 3096fbd01973
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '3096fbd01973'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('sitter_profile') as batch:
        batch.add_column(sa.Column('has_fenced_yard', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('owns_dog', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('owns_cat', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('one_client_only', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('has_children', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('accepts_unspayed_female', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('accepts_intact_male', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('offers_grooming', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('is_star_sitter', sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table('sitter_profile') as batch:
        for col in [
            'has_fenced_yard', 'owns_dog', 'owns_cat', 'one_client_only', 'has_children',
            'accepts_unspayed_female', 'accepts_intact_male', 'offers_grooming', 'is_star_sitter',
        ]:
            batch.drop_column(col)
