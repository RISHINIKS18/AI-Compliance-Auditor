"""
API routes for embedding and semantic search operations.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.embeddings.schemas import SearchRequest, SearchResponse, SearchResultItem
from app.embeddings.service import EmbeddingService
from app.embeddings.vector_store import VectorStore
from app.embeddings.pipeline import embedding_pipeline

logger = structlog.get_logger()

router = APIRouter(prefix="/api/embeddings", tags=["embeddings"])


@router.post("/search", response_model=SearchResponse)
async def search_embeddings(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search across policy chunks.
    
    Args:
        request: Search request with query text and parameters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Search results with similar policy chunks
    """
    try:
        logger.info(
            "semantic_search_requested",
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            query_length=len(request.query),
            n_results=request.n_results
        )
        
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        
        # Generate embedding for query
        query_embedding = embedding_service.generate_single_embedding(request.query)
        
        if not query_embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding"
            )
        
        # Build metadata filter if policy_id is provided
        where_filter = None
        if request.policy_id:
            where_filter = {"policy_id": request.policy_id}
        
        # Search in ChromaDB
        results = vector_store.search(
            organization_id=str(current_user.organization_id),
            query_embedding=query_embedding,
            n_results=request.n_results,
            where=where_filter
        )
        
        # Format results
        search_results = []
        
        if results and results.get('ids') and results['ids'][0]:
            ids = results['ids'][0]
            distances = results.get('distances', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            documents = results.get('documents', [[]])[0]
            
            for i, chunk_id in enumerate(ids):
                # Remove 'chunk_' prefix from ID
                clean_chunk_id = chunk_id.replace('chunk_', '')
                
                result_item = SearchResultItem(
                    chunk_id=clean_chunk_id,
                    policy_id=metadatas[i].get('policy_id', ''),
                    chunk_index=metadatas[i].get('chunk_index', 0),
                    content=documents[i] if i < len(documents) else '',
                    distance=distances[i] if i < len(distances) else 0.0,
                    metadata=metadatas[i] if i < len(metadatas) else {}
                )
                search_results.append(result_item)
        
        logger.info(
            "semantic_search_completed",
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            results_count=len(search_results)
        )
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "semantic_search_failed",
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/generate/{policy_id}")
async def generate_policy_embeddings(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger embedding generation for a policy.
    
    Args:
        policy_id: UUID of the policy
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        logger.info(
            "manual_embedding_generation_requested",
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            policy_id=policy_id
        )
        
        # Verify policy belongs to user's organization
        from app.models.policy import Policy
        policy = db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.organization_id == current_user.organization_id
        ).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        # Generate embeddings
        success = embedding_pipeline.process_policy_embeddings(policy_id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate embeddings"
            )
        
        logger.info(
            "manual_embedding_generation_completed",
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            policy_id=policy_id
        )
        
        return {
            "message": "Embeddings generated successfully",
            "policy_id": policy_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "manual_embedding_generation_failed",
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            policy_id=policy_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )
