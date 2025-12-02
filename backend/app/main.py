from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.auth.routes import router as auth_router
from app.policies.routes import router as policies_router
from app.embeddings.routes import router as embeddings_router
from app.rules.routes import router as rules_router
from app.audits.routes import router as audits_router
from app.remediation.routes import router as remediation_router
from app.exports.routes import router as exports_router
from app.logging_config import configure_logging, get_logger
from app.startup_validation import run_startup_validation
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
from app.exception_handlers import (
    document_parsing_error_handler,
    embedding_generation_error_handler,
    llm_api_error_handler,
    vector_store_error_handler,
    s3_storage_error_handler,
    rule_extraction_error_handler,
    violation_detection_error_handler,
    remediation_generation_error_handler,
    export_generation_error_handler,
    compliance_auditor_exception_handler,
    sqlalchemy_error_handler,
    validation_error_handler,
    generic_exception_handler
)

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Run startup validation - fail fast if services unavailable
run_startup_validation()

app = FastAPI(title="AI Compliance Auditor API", version="1.0.0")

# Register exception handlers
app.add_exception_handler(DocumentParsingError, document_parsing_error_handler)
app.add_exception_handler(EmbeddingGenerationError, embedding_generation_error_handler)
app.add_exception_handler(LLMAPIError, llm_api_error_handler)
app.add_exception_handler(VectorStoreError, vector_store_error_handler)
app.add_exception_handler(S3StorageError, s3_storage_error_handler)
app.add_exception_handler(RuleExtractionError, rule_extraction_error_handler)
app.add_exception_handler(ViolationDetectionError, violation_detection_error_handler)
app.add_exception_handler(RemediationGenerationError, remediation_generation_error_handler)
app.add_exception_handler(ExportGenerationError, export_generation_error_handler)
app.add_exception_handler(ComplianceAuditorException, compliance_auditor_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(policies_router)
app.include_router(embeddings_router)
app.include_router(rules_router)
app.include_router(audits_router)
app.include_router(remediation_router)
app.include_router(exports_router)

@app.on_event("startup")
async def startup_event():
    logger.info("application_startup", message="AI Compliance Auditor API starting up")

@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies all system dependencies.
    
    Returns:
        Overall health status and individual service statuses
    """
    from app.health import health_check_service
    
    logger.debug("health_check_requested")
    return health_check_service.get_overall_health()

@app.get("/")
async def root():
    return {"message": "AI Compliance Auditor API"}
