"""Audit management API routes."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.audit import AuditDocument, Violation
from app.audits.schemas import (
    AuditUploadResponse,
    AuditResponse,
    AuditListResponse,
    AuditSummaryResponse,
    ViolationListResponse,
    ViolationResponse
)
from app.services.s3 import s3_service

logger = structlog.get_logger()

router = APIRouter(prefix="/api/audits", tags=["audits"])

# File validation constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_CONTENT_TYPES = ["application/pdf"]
ALLOWED_EXTENSIONS = [".pdf"]


def process_audit_background(audit_id: str):
    """
    Background task to process audit document.
    
    Args:
        audit_id: UUID of the audit document to process
    """
    from app.database import SessionLocal
    from app.audits.service import audit_service
    
    db = SessionLocal()
    try:
        logger.info("audit_processing_started", audit_id=audit_id)
        success = audit_service.process_audit(audit_id, db)
        
        if success:
            logger.info("audit_processing_completed", audit_id=audit_id)
        else:
            logger.error("audit_processing_failed", audit_id=audit_id)
    except Exception as e:
        logger.error(
            "audit_processing_exception",
            audit_id=audit_id,
            error=str(e),
            error_type=type(e).__name__
        )
    finally:
        db.close()


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded file is a PDF and within size limits.
    
    Args:
        file: Uploaded file object
        
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file.content_type}"
        )
    
    # Check file extension
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension. Only .pdf files are allowed."
        )


@router.post("/upload", response_model=AuditUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audit_document(
    file: Annotated[UploadFile, File(description="PDF document to audit")],
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Upload a document for compliance auditing.
    
    - Accepts PDF files only
    - Maximum file size: 50MB
    - Files are stored in S3 with organization-scoped paths
    - Metadata is saved to PostgreSQL
    - Triggers background processing for violation detection
    """
    # Validate file
    validate_pdf_file(file)
    
    # Read file content and check size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
    
    # Generate unique file ID and S3 path
    file_id = uuid.uuid4()
    s3_path = s3_service.generate_audit_path(
        organization_id=current_user.organization_id,
        file_id=file_id,
        filename=file.filename
    )
    
    # Upload to S3
    from io import BytesIO
    file_obj = BytesIO(file_content)
    
    upload_success = s3_service.upload_file(
        file_obj=file_obj,
        s3_path=s3_path,
        content_type=file.content_type
    )
    
    if not upload_success:
        logger.error(
            "audit_upload_failed",
            filename=file.filename,
            org_id=str(current_user.organization_id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )
    
    # Save audit document metadata to database
    audit_document = AuditDocument(
        id=file_id,
        organization_id=current_user.organization_id,
        filename=file.filename,
        s3_path=s3_path,
        status="processing"
    )
    
    try:
        db.add(audit_document)
        db.commit()
        db.refresh(audit_document)
        
        logger.info(
            "audit_uploaded",
            audit_id=str(audit_document.id),
            filename=file.filename,
            org_id=str(current_user.organization_id),
            file_size=file_size
        )
        
        # Trigger background processing (parse, chunk, detect violations)
        background_tasks.add_task(
            process_audit_background,
            audit_id=str(audit_document.id)
        )
        
        return AuditUploadResponse(
            audit_id=audit_document.id,
            filename=audit_document.filename,
            status=audit_document.status,
            message="Audit document uploaded successfully and processing started"
        )
    
    except Exception as e:
        db.rollback()
        # Clean up S3 file if database save fails
        s3_service.delete_file(s3_path)
        logger.error(
            "audit_metadata_save_failed",
            filename=file.filename,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save audit document metadata"
        )


@router.get("", response_model=AuditListResponse)
async def get_audits(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get all audit documents for the current user's organization.
    
    Returns list of audit documents with metadata, filtered by organization.
    """
    audits = db.query(AuditDocument).filter(
        AuditDocument.organization_id == current_user.organization_id
    ).order_by(AuditDocument.upload_date.desc()).all()
    
    logger.info(
        "audits_retrieved",
        org_id=str(current_user.organization_id),
        count=len(audits)
    )
    
    return AuditListResponse(
        audits=[AuditResponse.model_validate(a) for a in audits],
        total=len(audits)
    )


@router.get("/{audit_id}", response_model=AuditSummaryResponse)
async def get_audit(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get a specific audit document by ID with summary.
    
    Returns audit details with violations count and compliant status.
    """
    audit = db.query(AuditDocument).filter(
        AuditDocument.id == audit_id,
        AuditDocument.organization_id == current_user.organization_id
    ).first()
    
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit document not found"
        )
    
    # Get violations for this audit
    violations = db.query(Violation).filter(
        Violation.audit_document_id == audit_id
    ).all()
    
    violations_count = len(violations)
    compliant = violations_count == 0
    
    logger.info(
        "audit_retrieved",
        audit_id=str(audit_id),
        org_id=str(current_user.organization_id),
        violations_count=violations_count,
        compliant=compliant
    )
    
    return AuditSummaryResponse(
        audit=AuditResponse.model_validate(audit),
        violations_count=violations_count,
        compliant=compliant,
        violations=[ViolationResponse.model_validate(v) for v in violations]
    )


@router.get("/violations", response_model=ViolationListResponse)
async def get_all_violations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get all violations across all audit documents for the current user's organization.
    
    Returns list of all violations with enriched data including document name and rule description.
    """
    from app.models.rule import ComplianceRule
    
    # Get all audits for the organization
    audit_ids = db.query(AuditDocument.id).filter(
        AuditDocument.organization_id == current_user.organization_id
    ).all()
    
    audit_id_list = [audit_id[0] for audit_id in audit_ids]
    
    # Get all violations for these audits with joined data
    violations = db.query(Violation).filter(
        Violation.audit_document_id.in_(audit_id_list)
    ).order_by(Violation.detected_at.desc()).all()
    
    # Enrich violations with document name and rule description
    enriched_violations = []
    for violation in violations:
        # Get audit document
        audit = db.query(AuditDocument).filter(
            AuditDocument.id == violation.audit_document_id
        ).first()
        
        # Get rule
        rule = db.query(ComplianceRule).filter(
            ComplianceRule.id == violation.rule_id
        ).first()
        
        # Create enriched response
        violation_dict = {
            "id": violation.id,
            "audit_document_id": violation.audit_document_id,
            "rule_id": violation.rule_id,
            "chunk_id": violation.chunk_id,
            "severity": violation.severity,
            "explanation": violation.explanation,
            "remediation": violation.remediation,
            "detected_at": violation.detected_at,
            "document_name": audit.filename if audit else "Unknown",
            "rule_description": rule.rule_text if rule else "Unknown rule",
            "policy_excerpt": None,  # TODO: Add policy excerpt from chunk
            "document_excerpt": None,  # TODO: Add document excerpt from chunk
        }
        enriched_violations.append(violation_dict)
    
    logger.info(
        "all_violations_retrieved",
        org_id=str(current_user.organization_id),
        count=len(violations)
    )
    
    return {
        "violations": enriched_violations,
        "total": len(enriched_violations)
    }


@router.get("/{audit_id}/violations", response_model=ViolationListResponse)
async def get_audit_violations(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get all violations for a specific audit document.
    
    Returns list of violations detected during the audit.
    """
    # Verify audit belongs to user's organization
    audit = db.query(AuditDocument).filter(
        AuditDocument.id == audit_id,
        AuditDocument.organization_id == current_user.organization_id
    ).first()
    
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit document not found"
        )
    
    # Get violations
    violations = db.query(Violation).filter(
        Violation.audit_document_id == audit_id
    ).order_by(Violation.detected_at.desc()).all()
    
    logger.info(
        "audit_violations_retrieved",
        audit_id=str(audit_id),
        org_id=str(current_user.organization_id),
        count=len(violations)
    )
    
    return ViolationListResponse(
        violations=[ViolationResponse.model_validate(v) for v in violations],
        total=len(violations)
    )
