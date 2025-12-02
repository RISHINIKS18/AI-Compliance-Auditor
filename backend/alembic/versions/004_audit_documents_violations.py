"""Create audit_documents and violations tables

Revision ID: 004
Revises: 003
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_documents table
    op.create_table(
        'audit_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('s3_path', sa.String(length=512), nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on organization_id for audit_documents
    op.create_index(op.f('ix_audit_documents_organization_id'), 'audit_documents', ['organization_id'], unique=False)

    # Create violations table
    op.create_table(
        'violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('audit_document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['audit_document_id'], ['audit_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['compliance_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_violations_audit_document_id'), 'violations', ['audit_document_id'], unique=False)
    op.create_index(op.f('ix_violations_severity'), 'violations', ['severity'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_violations_severity'), table_name='violations')
    op.drop_index(op.f('ix_violations_audit_document_id'), table_name='violations')
    op.drop_table('violations')
    op.drop_index(op.f('ix_audit_documents_organization_id'), table_name='audit_documents')
    op.drop_table('audit_documents')
