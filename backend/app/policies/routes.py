"""Policy management API routes."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.models.policy import Policy
from app.policies.schemas import (
    PolicyUploadResponse,
    PolicyResponse,
    PolicyListResponse,
    PolicyDeleteResponse
)
from app.services.s3 import s3_service

logger = structlog.get_logger()

router = APIRouter(prefix="/api/policies", tags=["policies"])

# File validation constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_CONTENT_TYPES = ["application/pdf"]
ALLOWED_EXTENSIONS = [".pdf"]


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


@router.post("/upload", response_model=PolicyUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_policy(
    file: Annotated[UploadFile, File(description="PDF policy document")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Upload a policy document.
    
    - Accepts PDF files only
    - Maximum file size: 50MB
    - Files are stored in S3 with organization-scoped paths
    - Metadata is saved to PostgreSQL
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
    s3_path = s3_service.generate_policy_path(
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
            "policy_upload_failed",
            filename=file.filename,
            org_id=str(current_user.organization_id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )
    
    # Save policy metadata to database
    policy = Policy(
        id=file_id,
        organization_id=current_user.organization_id,
        filename=file.filename,
        s3_path=s3_path,
        status="processing",
        file_size=file_size
    )
    
    try:
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        logger.info(
            "policy_uploaded",
            policy_id=str(policy.id),
            filename=file.filename,
            org_id=str(current_user.organization_id),
            file_size=file_size
        )
        
        return PolicyUploadResponse(
            policy_id=policy.id,
            filename=policy.filename,
            status=policy.status,
            message="Policy uploaded successfully"
        )
    
    except Exception as e:
        db.rollback()
        # Clean up S3 file if database save fails
        s3_service.delete_file(s3_path)
        logger.error(
            "policy_metadata_save_failed",
            filename=file.filename,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save policy metadata"
        )


@router.get("", response_model=PolicyListResponse)
async def get_policies(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get all policies for the current user's organization.
    
    Returns list of policies with metadata, filtered by organization.
    """
    policies = db.query(Policy).filter(
        Policy.organization_id == current_user.organization_id
    ).order_by(Policy.upload_date.desc()).all()
    
    logger.info(
        "policies_retrieved",
        org_id=str(current_user.organization_id),
        count=len(policies)
    )
    
    return PolicyListResponse(
        policies=[PolicyResponse.model_validate(p) for p in policies],
        total=len(policies)
    )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get a specific policy by ID.
    
    Returns policy details if it belongs to the user's organization.
    """
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.organization_id == current_user.organization_id
    ).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    logger.info(
        "policy_retrieved",
        policy_id=str(policy_id),
        org_id=str(current_user.organization_id)
    )
    
    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}", response_model=PolicyDeleteResponse)
async def delete_policy(
    policy_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Delete a policy and its associated S3 file.
    
    Removes both the database record and the S3 file.
    Policy chunks are automatically deleted via CASCADE.
    """
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.organization_id == current_user.organization_id
    ).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Delete from S3
    s3_path = policy.s3_path
    s3_delete_success = s3_service.delete_file(s3_path)
    
    if not s3_delete_success:
        logger.warning(
            "s3_delete_failed_but_continuing",
            policy_id=str(policy_id),
            s3_path=s3_path
        )
    
    # Delete from database (will cascade to policy_chunks)
    try:
        db.delete(policy)
        db.commit()
        
        logger.info(
            "policy_deleted",
            policy_id=str(policy_id),
            org_id=str(current_user.organization_id),
            filename=policy.filename
        )
        
        return PolicyDeleteResponse(
            policy_id=policy_id,
            message="Policy deleted successfully"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(
            "policy_delete_failed",
            policy_id=str(policy_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete policy"
        )
