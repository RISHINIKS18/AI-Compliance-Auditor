"""Processing pipeline for policy documents."""
from typing import Optional
from sqlalchemy.orm import Session
import structlog

from app.models.policy import Policy, PolicyChunk
from app.processing.parser import document_parser, DocumentParsingError
from app.processing.chunker import text_chunker
from app.services.s3 import s3_service

logger = structlog.get_logger()

# Import embedding pipeline (lazy import to avoid circular dependencies)
_embedding_pipeline = None

def get_embedding_pipeline():
    """Lazy load embedding pipeline to avoid circular imports."""
    global _embedding_pipeline
    if _embedding_pipeline is None:
        from app.embeddings.pipeline import embedding_pipeline
        _embedding_pipeline = embedding_pipeline
    return _embedding_pipeline


class ProcessingPipeline:
    """Pipeline for processing policy documents: parse, chunk, and store."""
    
    def process_policy(self, policy_id: str, db: Session) -> bool:
        """
        Process a policy document: download from S3, parse, chunk, and store chunks.
        
        Args:
            policy_id: UUID of the policy to process
            db: Database session
            
        Returns:
            True if processing succeeded, False otherwise
        """
        # Fetch policy from database
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        
        if not policy:
            logger.error("policy_not_found", policy_id=policy_id)
            return False
        
        logger.info(
            "processing_policy_started",
            policy_id=str(policy.id),
            filename=policy.filename,
            org_id=str(policy.organization_id)
        )
        
        try:
            # Update status to processing
            policy.status = "processing"
            db.commit()
            
            # Step 1: Download file from S3
            file_bytes = s3_service.download_file(policy.s3_path)
            
            if not file_bytes:
                raise Exception("Failed to download file from S3")
            
            logger.info(
                "policy_downloaded_from_s3",
                policy_id=str(policy.id),
                s3_path=policy.s3_path,
                file_size=len(file_bytes)
            )
            
            # Step 2: Parse PDF and extract text
            try:
                text_content = document_parser.extract_text_from_bytes(
                    file_bytes=file_bytes,
                    filename=policy.filename
                )
            except DocumentParsingError as e:
                logger.error(
                    "document_parsing_failed",
                    policy_id=str(policy.id),
                    error=str(e)
                )
                policy.status = "failed"
                db.commit()
                return False
            
            if not text_content or len(text_content.strip()) == 0:
                logger.error(
                    "no_text_extracted",
                    policy_id=str(policy.id)
                )
                policy.status = "failed"
                db.commit()
                return False
            
            logger.info(
                "text_extracted",
                policy_id=str(policy.id),
                text_length=len(text_content)
            )
            
            # Step 3: Chunk the text
            chunks = text_chunker.chunk_text(text_content)
            
            if not chunks:
                logger.error(
                    "no_chunks_created",
                    policy_id=str(policy.id)
                )
                policy.status = "failed"
                db.commit()
                return False
            
            # Get chunk statistics
            stats = text_chunker.get_chunk_statistics(chunks)
            logger.info(
                "text_chunked",
                policy_id=str(policy.id),
                **stats
            )
            
            # Step 4: Store chunks in database
            # First, delete any existing chunks for this policy (in case of reprocessing)
            db.query(PolicyChunk).filter(PolicyChunk.policy_id == policy.id).delete()
            
            # Insert new chunks
            for chunk in chunks:
                policy_chunk = PolicyChunk(
                    policy_id=policy.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count
                )
                db.add(policy_chunk)
            
            # Update policy status to completed
            policy.status = "completed"
            db.commit()
            
            logger.info(
                "policy_processing_completed",
                policy_id=str(policy.id),
                chunks_stored=len(chunks),
                status="completed"
            )
            
            # Step 5: Generate and store embeddings
            try:
                embedding_pipeline = get_embedding_pipeline()
                embedding_success = embedding_pipeline.process_policy_embeddings(
                    policy_id=str(policy.id),
                    db=db
                )
                
                if embedding_success:
                    logger.info(
                        "embeddings_generated_successfully",
                        policy_id=str(policy.id)
                    )
                else:
                    logger.warning(
                        "embeddings_generation_failed_but_policy_completed",
                        policy_id=str(policy.id)
                    )
            except Exception as e:
                logger.error(
                    "embeddings_generation_error",
                    policy_id=str(policy.id),
                    error=str(e)
                )
                # Don't fail the entire pipeline if embeddings fail
            
            return True
            
        except Exception as e:
            # Rollback any database changes
            db.rollback()
            
            # Update policy status to failed
            try:
                policy.status = "failed"
                db.commit()
            except Exception as commit_error:
                logger.error(
                    "failed_to_update_policy_status",
                    policy_id=str(policy.id),
                    error=str(commit_error)
                )
            
            logger.error(
                "policy_processing_failed",
                policy_id=str(policy.id),
                error=str(e),
                error_type=type(e).__name__
            )
            
            return False
    
    def reprocess_policy(self, policy_id: str, db: Session) -> bool:
        """
        Reprocess an existing policy (useful for failed policies or updates).
        
        Args:
            policy_id: UUID of the policy to reprocess
            db: Database session
            
        Returns:
            True if reprocessing succeeded, False otherwise
        """
        logger.info("reprocessing_policy", policy_id=policy_id)
        return self.process_policy(policy_id, db)


# Create a singleton instance for easy import
processing_pipeline = ProcessingPipeline()
