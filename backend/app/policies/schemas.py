"""Policy schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class PolicyUploadResponse(BaseModel):
    """Response schema for policy upload."""
    
    policy_id: uuid.UUID
    filename: str
    status: str
    message: str
    
    class Config:
        from_attributes = True


class PolicyResponse(BaseModel):
    """Response schema for policy details."""
    
    id: uuid.UUID
    organization_id: uuid.UUID
    filename: str
    upload_date: datetime
    status: str
    file_size: Optional[int] = None
    
    class Config:
        from_attributes = True


class PolicyListResponse(BaseModel):
    """Response schema for policy list."""
    
    policies: list[PolicyResponse]
    total: int


class PolicyDeleteResponse(BaseModel):
    """Response schema for policy deletion."""
    
    policy_id: uuid.UUID
    message: str
