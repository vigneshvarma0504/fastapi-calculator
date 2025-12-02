"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-12-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('username', name='uq_users_username'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )

    # operation_type enum
    op.execute("CREATE TYPE operation_type AS ENUM ('Add','Sub','Multiply','Divide')")

    # calculations table
    op.create_table(
        'calculations',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('a', sa.Float(), nullable=False),
        sa.Column('b', sa.Float(), nullable=False),
        sa.Column('type', sa.Enum('Add', 'Sub', 'Multiply', 'Divide', name='operation_type'), nullable=False),
        sa.Column('result', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table('refresh_tokens')
    op.drop_table('calculations')
    # drop enum type if postgres
    try:
        op.execute('DROP TYPE IF EXISTS operation_type')
    except Exception:
        pass
    op.drop_table('users')
