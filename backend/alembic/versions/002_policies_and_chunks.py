"""Create policies and policy_chunks tables

Revision ID: 002
Revises: 001
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create policies table
    op.create_table(
        'policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('s3_path', sa.String(length=512), nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on organization_id for policies
    op.create_index(op.f('ix_policies_organization_id'), 'policies', ['organization_id'], unique=False)

    # Create policy_chunks table
    op.create_table(
        'policy_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on policy_id for policy_chunks
    op.create_index(op.f('ix_policy_chunks_policy_id'), 'policy_chunks', ['policy_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_policy_chunks_policy_id'), table_name='policy_chunks')
    op.drop_table('policy_chunks')
    op.drop_index(op.f('ix_policies_organization_id'), table_name='policies')
    op.drop_table('policies')
