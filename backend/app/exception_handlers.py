"""Global exception handlers for FastAPI application."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.exceptions import (
    ComplianceAuditorException,
    DocumentParsingError,
    EmbeddingGenerationError,
    LLMAPIError,
    VectorStoreError,
    S3StorageError,
    RuleExtractionError,
    ViolationDetectionError,
    RemediationGenerationError,
    ExportGenerationError
)

logger = structlog.get_logger(__name__)


def create_error_response(
    error_code: str,
    message: str,
    details: str = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error_code: Error code identifier
        message: Human-readable error message
        details: Optional additional details
        status_code: HTTP status code
        
    Returns:
        JSONResponse with standardized error format
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def document_parsing_error_handler(
    request: Request,
    exc: DocumentParsingError
) -> JSONResponse:
    """Handle document parsing errors."""
    logger.error(
        "document_parsing_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="DOCUMENT_PARSING_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def embedding_generation_error_handler(
    request: Request,
    exc: EmbeddingGenerationError
) -> JSONResponse:
    """Handle embedding generation errors."""
    logger.error(
        "embedding_generation_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="EMBEDDING_GENERATION_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def llm_api_error_handler(
    request: Request,
    exc: LLMAPIError
) -> JSONResponse:
    """Handle LLM API errors."""
    logger.error(
        "llm_api_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="LLM_API_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )


async def vector_store_error_handler(
    request: Request,
    exc: VectorStoreError
) -> JSONResponse:
    """Handle vector store errors."""
    logger.error(
        "vector_store_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="VECTOR_STORE_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def s3_storage_error_handler(
    request: Request,
    exc: S3StorageError
) -> JSONResponse:
    """Handle S3 storage errors."""
    logger.error(
        "s3_storage_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="S3_STORAGE_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def rule_extraction_error_handler(
    request: Request,
    exc: RuleExtractionError
) -> JSONResponse:
    """Handle rule extraction errors."""
    logger.error(
        "rule_extraction_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="RULE_EXTRACTION_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def violation_detection_error_handler(
    request: Request,
    exc: ViolationDetectionError
) -> JSONResponse:
    """Handle violation detection errors."""
    logger.error(
        "violation_detection_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="VIOLATION_DETECTION_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def remediation_generation_error_handler(
    request: Request,
    exc: RemediationGenerationError
) -> JSONResponse:
    """Handle remediation generation errors."""
    logger.error(
        "remediation_generation_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="REMEDIATION_GENERATION_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def export_generation_error_handler(
    request: Request,
    exc: ExportGenerationError
) -> JSONResponse:
    """Handle export generation errors."""
    logger.error(
        "export_generation_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details
    )
    
    return create_error_response(
        error_code="EXPORT_GENERATION_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def compliance_auditor_exception_handler(
    request: Request,
    exc: ComplianceAuditorException
) -> JSONResponse:
    """Handle generic compliance auditor exceptions."""
    logger.error(
        "compliance_auditor_error",
        path=request.url.path,
        message=exc.message,
        details=exc.details,
        exception_type=type(exc).__name__
    )
    
    return create_error_response(
        error_code="COMPLIANCE_AUDITOR_ERROR",
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    logger.error(
        "database_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__
    )
    
    return create_error_response(
        error_code="DATABASE_ERROR",
        message="A database error occurred",
        details=str(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=exc.errors()
    )
    
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details=str(exc.errors()),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__
    )
    
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details=str(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
