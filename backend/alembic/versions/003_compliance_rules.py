"""Create compliance_rules table

Revision ID: 003
Revises: 002
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create compliance_rules table
    op.create_table(
        'compliance_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('source_chunk_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_chunk_id'], ['policy_chunks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_compliance_rules_organization_id'), 'compliance_rules', ['organization_id'], unique=False)
    op.create_index(op.f('ix_compliance_rules_policy_id'), 'compliance_rules', ['policy_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_compliance_rules_policy_id'), table_name='compliance_rules')
    op.drop_index(op.f('ix_compliance_rules_organization_id'), table_name='compliance_rules')
    op.drop_table('compliance_rules')
