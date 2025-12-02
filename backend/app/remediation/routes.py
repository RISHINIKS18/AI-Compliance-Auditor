"""Remediation API routes."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.audit import Violation, AuditDocument
from app.models.rule import ComplianceRule
from app.models.policy import PolicyChunk
from app.remediation.service import remediation_service
from app.remediation.schemas import RemediationResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/remediation", tags=["remediation"])


@router.post("/generate/{violation_id}", response_model=RemediationResponse)
async def generate_remediation(
    violation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Generate or regenerate remediation suggestion for a specific violation.
    
    - Allows manual regeneration of remediation suggestions
    - Requires the violation to belong to the user's organization
    - Returns the updated remediation text
    """
    # Fetch the violation
    violation = db.query(Violation).filter(
        Violation.id == violation_id
    ).first()
    
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found"
        )
    
    # Verify the violation belongs to the user's organization
    audit = db.query(AuditDocument).filter(
        AuditDocument.id == violation.audit_document_id,
        AuditDocument.organization_id == current_user.organization_id
    ).first()
    
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found or access denied"
        )
    
    # Fetch the associated rule
    rule = db.query(ComplianceRule).filter(
        ComplianceRule.id == violation.rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated compliance rule not found"
        )
    
    # Get the document excerpt (policy chunk content)
    # Since we don't store audit chunks, we'll use the rule's source chunk as context
    document_excerpt = ""
    if rule.source_chunk_id:
        policy_chunk = db.query(PolicyChunk).filter(
            PolicyChunk.id == rule.source_chunk_id
        ).first()
        if policy_chunk:
            document_excerpt = policy_chunk.content
    
    # If no policy chunk found, use a generic excerpt message
    if not document_excerpt:
        document_excerpt = "Document content not available for this violation."
    
    logger.info(
        "generating_remediation_for_violation",
        violation_id=str(violation_id),
        rule_id=str(rule.id),
        org_id=str(current_user.organization_id)
    )
    
    try:
        # Generate remediation suggestion
        remediation_text = remediation_service.generate_suggestion(
            violation=violation,
            rule=rule,
            document_excerpt=document_excerpt
        )
        
        # Update the violation with new remediation
        violation.remediation = remediation_text
        db.commit()
        db.refresh(violation)
        
        logger.info(
            "remediation_regenerated",
            violation_id=str(violation_id),
            org_id=str(current_user.organization_id)
        )
        
        return RemediationResponse(
            violation_id=violation.id,
            remediation=violation.remediation,
            message="Remediation suggestion generated successfully"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(
            "remediation_generation_failed",
            violation_id=str(violation_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate remediation suggestion: {str(e)}"
        )
