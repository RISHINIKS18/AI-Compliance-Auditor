"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str
    organization_name: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: str
    organization_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    id: UUID
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
