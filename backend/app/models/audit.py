"""AuditDocument and Violation models."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class AuditDocument(Base):
    """Audit document model."""
    
    __tablename__ = "audit_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename = Column(String(255), nullable=False)
    s3_path = Column(String(512), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="processing")


class Violation(Base):
    """Violation model."""
    
    __tablename__ = "violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audit_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rules.id", ondelete="CASCADE"),
        nullable=False
    )
    chunk_id = Column(UUID(as_uuid=True))
    severity = Column(String(20), index=True)
    explanation = Column(Text)
    remediation = Column(Text)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
