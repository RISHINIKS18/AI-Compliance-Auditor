"""Remediation API schemas."""
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RemediationResponse(BaseModel):
    """Response schema for remediation generation."""
    
    violation_id: UUID
    remediation: Optional[str] = None
    message: str
    
    model_config = ConfigDict(from_attributes=True)
