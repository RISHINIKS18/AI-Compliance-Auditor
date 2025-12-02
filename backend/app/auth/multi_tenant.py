"""Multi-tenant utilities and dependencies."""
from uuid import UUID
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session, Query

from app.auth.dependencies import get_current_user
from app.auth.models import User


def get_organization_id(current_user: User = Depends(get_current_user)) -> UUID:
    """
    Dependency to extract organization_id from the current authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Organization ID of the current user
    """
    return current_user.organization_id


class OrganizationFilter:
    """
    Helper class for filtering database queries by organization_id.
    
    Ensures multi-tenant data isolation by automatically filtering queries.
    """
    
    def __init__(self, organization_id: UUID):
        """
        Initialize the organization filter.
        
        Args:
            organization_id: Organization ID to filter by
        """
        self.organization_id = organization_id
    
    def filter_query(self, query: Query, model_class) -> Query:
        """
        Apply organization filter to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            model_class: Model class with organization_id attribute
            
        Returns:
            Filtered query
        """
        if hasattr(model_class, 'organization_id'):
            return query.filter(model_class.organization_id == self.organization_id)
        return query


def get_organization_filter(
    organization_id: UUID = Depends(get_organization_id)
) -> OrganizationFilter:
    """
    Dependency to get an OrganizationFilter instance.
    
    Args:
        organization_id: Organization ID from current user
        
    Returns:
        OrganizationFilter instance
    """
    return OrganizationFilter(organization_id)


def filter_by_organization(
    query: Query,
    model_class,
    organization_id: UUID
) -> Query:
    """
    Utility function to filter a query by organization_id.
    
    Args:
        query: SQLAlchemy query object
        model_class: Model class with organization_id attribute
        organization_id: Organization ID to filter by
        
    Returns:
        Filtered query
    """
    if hasattr(model_class, 'organization_id'):
        return query.filter(model_class.organization_id == organization_id)
    return query
