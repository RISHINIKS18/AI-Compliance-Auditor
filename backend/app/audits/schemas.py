"""Audit schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid


class AuditUploadResponse(BaseModel):
    """Response schema for audit document upload."""
    
    audit_id: uuid.UUID
    filename: str
    status: str
    message: str
    
    class Config:
        from_attributes = True


class AuditResponse(BaseModel):
    """Response schema for audit document details."""
    
    id: uuid.UUID
    organization_id: uuid.UUID
    filename: str
    upload_date: datetime
    status: str
    
    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    """Response schema for audit list."""
    
    audits: list[AuditResponse]
    total: int


class ViolationResponse(BaseModel):
    """Response schema for violation details."""
    
    id: uuid.UUID
    audit_document_id: uuid.UUID
    rule_id: uuid.UUID
    chunk_id: Optional[uuid.UUID] = None
    severity: str
    explanation: Optional[str] = None
    remediation: Optional[str] = None
    detected_at: datetime
    
    class Config:
        from_attributes = True


class AuditSummaryResponse(BaseModel):
    """Response schema for audit summary."""
    
    audit: AuditResponse
    violations_count: int
    compliant: bool
    violations: list[ViolationResponse]


class ViolationListResponse(BaseModel):
    """Response schema for violations list."""
    
    violations: list[ViolationResponse]
    total: int
