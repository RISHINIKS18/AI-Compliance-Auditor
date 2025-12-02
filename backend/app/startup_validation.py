"""Startup validation for required environment variables and service connections."""
import os
import sys
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.database import engine

logger = structlog.get_logger()


class StartupValidator:
    """Validator for application startup requirements."""
    
    # Required environment variables
    REQUIRED_ENV_VARS = [
        "DATABASE_URL",
        "JWT_SECRET",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_S3_BUCKET",
        "OPENAI_API_KEY",
    ]
    
    # Optional environment variables with defaults
    OPTIONAL_ENV_VARS = {
        "AWS_REGION": "us-east-1",
        "CHROMA_HOST": "localhost",
        "CHROMA_PORT": "8001",
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_MINUTES": "60",
    }
    
    def __init__(self):
        """Initialize startup validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_environment_variables(self) -> bool:
        """
        Validate that all required environment variables are set.
        
        Returns:
            True if all required variables are set, False otherwise
        """
        logger.info("validating_environment_variables")
        
        missing_vars = []
        
        for var in self.REQUIRED_ENV_VARS:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                logger.error("missing_required_env_var", variable=var)
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            self.errors.append(error_msg)
            return False
        
        # Log optional variables that are using defaults
        for var, default in self.OPTIONAL_ENV_VARS.items():
            value = os.getenv(var)
            if not value:
                logger.info(
                    "using_default_env_var",
                    variable=var,
                    default=default
                )
        
        logger.info("environment_variables_validated")
        return True
    
    def validate_database_connection(self) -> bool:
        """
        Test database connection on startup.
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("validating_database_connection")
        
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info("database_connection_validated")
            return True
        except SQLAlchemyError as e:
            error_msg = f"Database connection failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error("database_connection_failed", error=str(e))
            return False
        except Exception as e:
            error_msg = f"Unexpected database error: {str(e)}"
            self.errors.append(error_msg)
            logger.error("database_validation_error", error=str(e))
            return False
    
    def validate_chromadb_connection(self) -> bool:
        """
        Test ChromaDB connection on startup.
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("validating_chromadb_connection")
        
        try:
            from app.embeddings.vector_store import VectorStore
            
            vector_store = VectorStore()
            vector_store.client.heartbeat()
            
            logger.info("chromadb_connection_validated")
            return True
        except Exception as e:
            error_msg = f"ChromaDB connection failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error("chromadb_connection_failed", error=str(e))
            return False
    
    def validate_s3_connection(self) -> bool:
        """
        Test S3 connection on startup.
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("validating_s3_connection")
        
        try:
            from app.services.s3 import S3Service
            
            s3_service = S3Service()
            s3_service.s3_client.head_bucket(Bucket=s3_service.bucket_name)
            
            logger.info("s3_connection_validated", bucket=s3_service.bucket_name)
            return True
        except Exception as e:
            error_msg = f"S3 connection failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error("s3_connection_failed", error=str(e))
            return False
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all validations pass, False otherwise
        """
        logger.info("startup_validation_started")
        
        results = []
        
        # Validate environment variables first
        results.append(self.validate_environment_variables())
        
        # Only validate connections if environment variables are valid
        if results[0]:
            results.append(self.validate_database_connection())
            results.append(self.validate_chromadb_connection())
            results.append(self.validate_s3_connection())
        
        all_valid = all(results)
        
        if all_valid:
            logger.info("startup_validation_passed")
        else:
            logger.error(
                "startup_validation_failed",
                errors=self.errors,
                warnings=self.warnings
            )
        
        return all_valid
    
    def fail_fast(self) -> None:
        """
        Print errors and exit if validation fails.
        """
        if self.errors:
            print("\n" + "="*80)
            print("STARTUP VALIDATION FAILED")
            print("="*80)
            print("\nThe following errors were encountered:\n")
            
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
            
            print("\n" + "="*80)
            print("Please fix the above errors and restart the application.")
            print("="*80 + "\n")
            
            sys.exit(1)


def run_startup_validation() -> None:
    """
    Run startup validation and fail fast if any checks fail.
    """
    validator = StartupValidator()
    
    if not validator.validate_all():
        validator.fail_fast()
