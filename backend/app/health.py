"""Health check service for monitoring system dependencies."""
import os
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.database import engine
from app.embeddings.vector_store import VectorStore
from app.services.s3 import S3Service

logger = structlog.get_logger()


class HealthCheckService:
    """Service for checking health of system dependencies."""
    
    def __init__(self):
        """Initialize health check service."""
        self.vector_store = None
        self.s3_service = None
    
    def check_database(self) -> Dict[str, Any]:
        """
        Check PostgreSQL database connection.
        
        Returns:
            Dictionary with status and details
        """
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            
            logger.debug("database_health_check_passed")
            return {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except SQLAlchemyError as e:
            logger.error("database_health_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
        except Exception as e:
            logger.error("database_health_check_error", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def check_chromadb(self) -> Dict[str, Any]:
        """
        Check ChromaDB connection.
        
        Returns:
            Dictionary with status and details
        """
        try:
            if self.vector_store is None:
                self.vector_store = VectorStore()
            
            # Test connection by calling heartbeat
            self.vector_store.client.heartbeat()
            
            logger.debug("chromadb_health_check_passed")
            return {
                "status": "healthy",
                "message": "ChromaDB connection successful"
            }
        except Exception as e:
            logger.error("chromadb_health_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"ChromaDB connection failed: {str(e)}"
            }
    
    def check_s3(self) -> Dict[str, Any]:
        """
        Check AWS S3 connection.
        
        Returns:
            Dictionary with status and details
        """
        try:
            if self.s3_service is None:
                self.s3_service = S3Service()
            
            # Test connection by checking if bucket exists
            self.s3_service.s3_client.head_bucket(Bucket=self.s3_service.bucket_name)
            
            logger.debug("s3_health_check_passed", bucket=self.s3_service.bucket_name)
            return {
                "status": "healthy",
                "message": f"S3 connection successful (bucket: {self.s3_service.bucket_name})"
            }
        except Exception as e:
            logger.error("s3_health_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"S3 connection failed: {str(e)}"
            }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health status.
        
        Returns:
            Dictionary with overall status and individual service statuses
        """
        logger.info("health_check_started")
        
        # Check all services
        database_health = self.check_database()
        chromadb_health = self.check_chromadb()
        s3_health = self.check_s3()
        
        # Determine overall status
        all_healthy = all([
            database_health["status"] == "healthy",
            chromadb_health["status"] == "healthy",
            s3_health["status"] == "healthy"
        ])
        
        overall_status = "healthy" if all_healthy else "unhealthy"
        
        result = {
            "status": overall_status,
            "services": {
                "database": database_health,
                "chromadb": chromadb_health,
                "s3": s3_health
            }
        }
        
        logger.info("health_check_completed", overall_status=overall_status)
        
        return result


# Singleton instance
health_check_service = HealthCheckService()
