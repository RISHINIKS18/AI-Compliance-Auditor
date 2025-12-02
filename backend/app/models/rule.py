"""ComplianceRule model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ComplianceRule(Base):
    """Compliance rule model."""
    
    __tablename__ = "compliance_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rule_text = Column(Text, nullable=False)
    category = Column(String(100))
    severity = Column(String(20))
    source_chunk_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policy_chunks.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
