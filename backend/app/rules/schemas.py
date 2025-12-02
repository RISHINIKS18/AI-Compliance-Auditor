"""Compliance rule schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ComplianceRuleResponse(BaseModel):
    """Response schema for compliance rule details."""
    
    id: uuid.UUID
    organization_id: uuid.UUID
    policy_id: uuid.UUID
    rule_text: str
    category: Optional[str] = None
    severity: Optional[str] = None
    source_chunk_id: Optional[uuid.UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ComplianceRuleListResponse(BaseModel):
    """Response schema for compliance rule list."""
    
    rules: list[ComplianceRuleResponse]
    total: int


class RuleExtractionResponse(BaseModel):
    """Response schema for rule extraction."""
    
    policy_id: uuid.UUID
    rules_extracted: int
    status: str
    message: str
