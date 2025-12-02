"""
Embedding pipeline for generating and storing embeddings for policy chunks.
"""
from typing import List
import numpy as np
from sqlalchemy.orm import Session
import structlog

from app.models.policy import Policy, PolicyChunk
from app.embeddings.service import EmbeddingService
from app.embeddings.vector_store import VectorStore

logger = structlog.get_logger()


class EmbeddingPipeline:
    """
    Pipeline for generating embeddings and storing them in ChromaDB.
    """
    
    def __init__(self):
        """Initialize embedding service and vector store."""
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
    
    def process_policy_embeddings(self, policy_id: str, db: Session) -> bool:
        """
        Generate and store embeddings for all chunks of a policy.
        
        Args:
            policy_id: UUID of the policy
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        # Fetch policy from database
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        
        if not policy:
            logger.error("policy_not_found", policy_id=policy_id)
            return False
        
        # Fetch all chunks for this policy
        chunks = db.query(PolicyChunk).filter(
            PolicyChunk.policy_id == policy_id
        ).order_by(PolicyChunk.chunk_index).all()
        
        if not chunks:
            logger.error(
                "no_chunks_found",
                policy_id=policy_id
            )
            return False
        
        logger.info(
            "generating_embeddings_for_policy",
            policy_id=str(policy_id),
            organization_id=str(policy.organization_id),
            chunk_count=len(chunks)
        )
        
        try:
            # Extract text content from chunks
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.embedding_service.generate_embeddings(texts)
            
            if len(embeddings) != len(chunks):
                raise ValueError(
                    f"Embedding count mismatch: {len(embeddings)} != {len(chunks)}"
                )
            
            # Verify embeddings using NumPy
            embeddings_array = np.array(embeddings)
            logger.info(
                "embeddings_generated",
                policy_id=str(policy_id),
                count=len(embeddings),
                embedding_dim=embeddings_array.shape[1],
                mean_magnitude=float(np.mean(np.linalg.norm(embeddings_array, axis=1)))
            )
            
            # Prepare metadata for ChromaDB
            chunk_ids = [str(chunk.id) for chunk in chunks]
            metadatas = [
                {
                    "chunk_id": str(chunk.id),
                    "policy_id": str(policy.id),
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "content_preview": chunk.content[:200]
                }
                for chunk in chunks
            ]
            documents = texts  # Store full text for retrieval
            
            # Store embeddings in ChromaDB
            self.vector_store.add_embeddings(
                organization_id=str(policy.organization_id),
                embeddings=embeddings,
                chunk_ids=chunk_ids,
                metadatas=metadatas,
                documents=documents
            )
            
            # Verify storage with cosine similarity check
            self._verify_embeddings(
                organization_id=str(policy.organization_id),
                sample_embedding=embeddings[0],
                expected_chunk_id=chunk_ids[0]
            )
            
            logger.info(
                "embeddings_stored_successfully",
                policy_id=str(policy_id),
                organization_id=str(policy.organization_id),
                count=len(embeddings)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "embedding_pipeline_failed",
                policy_id=str(policy_id),
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    def _verify_embeddings(
        self,
        organization_id: str,
        sample_embedding: List[float],
        expected_chunk_id: str
    ) -> None:
        """
        Verify embeddings were stored correctly using cosine similarity.
        
        Args:
            organization_id: UUID of the organization
            sample_embedding: Sample embedding to verify
            expected_chunk_id: Expected chunk ID to find
        """
        try:
            # Search for the sample embedding
            results = self.vector_store.search(
                organization_id=organization_id,
                query_embedding=sample_embedding,
                n_results=1
            )
            
            if not results or not results.get('ids') or not results['ids'][0]:
                raise ValueError("No results returned from verification search")
            
            # Check if the expected chunk is the top result
            top_result_id = results['ids'][0][0]
            expected_id = f"chunk_{expected_chunk_id}"
            
            if top_result_id == expected_id:
                # Calculate cosine similarity using NumPy
                if results.get('distances'):
                    distance = results['distances'][0][0]
                    # ChromaDB returns L2 distance, convert to similarity
                    similarity = 1 / (1 + distance)
                    logger.info(
                        "embedding_verification_passed",
                        organization_id=organization_id,
                        similarity=float(similarity)
                    )
                else:
                    logger.info(
                        "embedding_verification_passed",
                        organization_id=organization_id
                    )
            else:
                logger.warning(
                    "embedding_verification_mismatch",
                    expected=expected_id,
                    actual=top_result_id
                )
                
        except Exception as e:
            logger.warning(
                "embedding_verification_failed",
                organization_id=organization_id,
                error=str(e)
            )
    
    def delete_policy_embeddings(self, policy_id: str, organization_id: str) -> bool:
        """
        Delete all embeddings for a policy.
        
        Args:
            policy_id: UUID of the policy
            organization_id: UUID of the organization
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.vector_store.delete_by_policy(
                organization_id=str(organization_id),
                policy_id=str(policy_id)
            )
            
            logger.info(
                "policy_embeddings_deleted",
                policy_id=str(policy_id),
                organization_id=str(organization_id)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "policy_embeddings_deletion_failed",
                policy_id=str(policy_id),
                organization_id=str(organization_id),
                error=str(e)
            )
            return False


# Create a singleton instance for easy import
embedding_pipeline = EmbeddingPipeline()
