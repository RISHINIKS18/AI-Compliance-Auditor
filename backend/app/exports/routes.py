"""Export routes for generating audit reports."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.exports.service import ExportService


router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.get("/csv/{audit_id}")
async def export_csv(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export audit violations to CSV format.
    
    Args:
        audit_id: UUID of the audit document
        current_user: Authenticated user
        db: Database session
        
    Returns:
        StreamingResponse with CSV file
        
    Raises:
        HTTPException: If audit not found or export fails
    """
    try:
        export_service = ExportService(db)
        buffer, filename = await export_service.generate_csv(
            audit_id=audit_id,
            organization_id=str(current_user.organization_id)
        )
        
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CSV export: {str(e)}"
        )


@router.get("/pdf/{audit_id}")
async def export_pdf(
    audit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export audit violations to PDF format.
    
    Args:
        audit_id: UUID of the audit document
        current_user: Authenticated user
        db: Database session
        
    Returns:
        StreamingResponse with PDF file
        
    Raises:
        HTTPException: If audit not found or export fails
    """
    try:
        export_service = ExportService(db)
        buffer, filename = await export_service.generate_pdf(
            audit_id=audit_id,
            organization_id=str(current_user.organization_id)
        )
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF export: {str(e)}"
        )
