"""Policy and PolicyChunk models."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Policy(Base):
    """Policy document model."""
    
    __tablename__ = "policies"
    
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
    file_size = Column(Integer)


class PolicyChunk(Base):
    """Policy document chunk model."""
    
    __tablename__ = "policy_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
