"""S3 service for file uploads and management."""
import os
import uuid
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger()


class S3Service:
    """Service for managing S3 file operations."""
    
    def __init__(self):
        """Initialize S3 client."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
        
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET environment variable is required")
    
    def generate_policy_path(self, organization_id: uuid.UUID, file_id: uuid.UUID, filename: str) -> str:
        """
        Generate organization-scoped S3 path for policy files.
        
        Args:
            organization_id: Organization UUID
            file_id: Unique file identifier
            filename: Original filename
            
        Returns:
            S3 path in format: org_id/policies/file_id.pdf
        """
        # Extract file extension
        _, ext = os.path.splitext(filename)
        return f"{organization_id}/policies/{file_id}{ext}"
    
    def generate_audit_path(self, organization_id: uuid.UUID, file_id: uuid.UUID, filename: str) -> str:
        """
        Generate organization-scoped S3 path for audit document files.
        
        Args:
            organization_id: Organization UUID
            file_id: Unique file identifier
            filename: Original filename
            
        Returns:
            S3 path in format: org_id/audits/file_id.pdf
        """
        # Extract file extension
        _, ext = os.path.splitext(filename)
        return f"{organization_id}/audits/{file_id}{ext}"
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        s3_path: str,
        content_type: str = "application/pdf"
    ) -> bool:
        """
        Upload file to S3.
        
        Args:
            file_obj: File object to upload
            s3_path: S3 path for the file
            content_type: MIME type of the file
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_path,
                ExtraArgs={'ContentType': content_type}
            )
            logger.info("file_uploaded_to_s3", s3_path=s3_path, bucket=self.bucket_name)
            return True
        except ClientError as e:
            logger.error("s3_upload_failed", s3_path=s3_path, error=str(e))
            return False
    
    def delete_file(self, s3_path: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            s3_path: S3 path of the file to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_path
            )
            logger.info("file_deleted_from_s3", s3_path=s3_path, bucket=self.bucket_name)
            return True
        except ClientError as e:
            logger.error("s3_delete_failed", s3_path=s3_path, error=str(e))
            return False
    
    def download_file(self, s3_path: str) -> Optional[bytes]:
        """
        Download file from S3 and return as bytes.
        
        Args:
            s3_path: S3 path of the file to download
            
        Returns:
            File content as bytes or None if download fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_path
            )
            file_bytes = response['Body'].read()
            logger.info(
                "file_downloaded_from_s3",
                s3_path=s3_path,
                bucket=self.bucket_name,
                size=len(file_bytes)
            )
            return file_bytes
        except ClientError as e:
            logger.error("s3_download_failed", s3_path=s3_path, error=str(e))
            return None
    
    def get_file_url(self, s3_path: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for file access.
        
        Args:
            s3_path: S3 path of the file
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL or None if generation fails
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_path},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error("presigned_url_generation_failed", s3_path=s3_path, error=str(e))
            return None


# Singleton instance
s3_service = S3Service()
