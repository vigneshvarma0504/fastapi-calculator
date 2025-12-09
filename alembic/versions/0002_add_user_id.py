"""Add user_id to calculations table

Revision ID: 0002_add_user_id
Revises: 0001_initial
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_add_user_id'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column to calculations table
    # Note: This migration assumes that there might be existing data
    # If there are existing calculations without user_id, we need to handle them
    
    # Add the column as nullable first
    op.add_column('calculations', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # Create a foreign key constraint
    op.create_foreign_key(
        'fk_calculations_user_id',
        'calculations',
        'users',
        ['user_id'],
        ['id']
    )
    
    # If you need to assign existing calculations to a default user or delete them,
    # uncomment and adjust the following:
    # from sqlalchemy import text
    # op.execute(text("UPDATE calculations SET user_id = 1 WHERE user_id IS NULL"))
    
    # After handling existing data, make the column non-nullable
    # op.alter_column('calculations', 'user_id', nullable=False)
    
    # Create an index on user_id for better query performance
    op.create_index('ix_calculations_user_id', 'calculations', ['user_id'])


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_calculations_user_id', table_name='calculations')
    
    # Drop the foreign key constraint
    op.drop_constraint('fk_calculations_user_id', 'calculations', type_='foreignkey')
    
    # Drop the column
    op.drop_column('calculations', 'user_id')
