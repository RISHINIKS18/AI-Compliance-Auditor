"""
Vector store implementation using ChromaDB for semantic search.
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import structlog

logger = structlog.get_logger()


class VectorStore:
    """
    Wrapper class for ChromaDB operations with organization-scoped collections.
    """
    
    def __init__(self):
        """Initialize ChromaDB client."""
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8001"))
        
        # Initialize ChromaDB client
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        logger.info("chromadb_client_initialized", host=chroma_host, port=chroma_port)
    
    def get_collection_name(self, organization_id: str) -> str:
        """
        Generate organization-scoped collection name.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            Collection name in format: org_{org_id}_policies
        """
        return f"org_{organization_id}_policies"
    
    def get_or_create_collection(self, organization_id: str):
        """
        Get or create a collection for an organization.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            ChromaDB collection object
        """
        collection_name = self.get_collection_name(organization_id)
        
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"organization_id": str(organization_id)}
            )
            logger.info(
                "collection_retrieved",
                collection_name=collection_name,
                organization_id=organization_id
            )
            return collection
        except Exception as e:
            logger.error(
                "collection_creation_failed",
                collection_name=collection_name,
                organization_id=organization_id,
                error=str(e)
            )
            raise
    
    def add_embeddings(
        self,
        organization_id: str,
        embeddings: List[List[float]],
        chunk_ids: List[str],
        metadatas: List[Dict[str, Any]],
        documents: List[str]
    ) -> None:
        """
        Add embeddings to the organization's collection.
        
        Args:
            organization_id: UUID of the organization
            embeddings: List of embedding vectors
            chunk_ids: List of chunk IDs
            metadatas: List of metadata dictionaries
            documents: List of document text content
        """
        collection = self.get_or_create_collection(organization_id)
        
        try:
            # Format IDs with chunk_ prefix
            ids = [f"chunk_{chunk_id}" for chunk_id in chunk_ids]
            
            collection.add(
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
                documents=documents
            )
            
            logger.info(
                "embeddings_added",
                organization_id=organization_id,
                count=len(embeddings)
            )
        except Exception as e:
            logger.error(
                "embeddings_add_failed",
                organization_id=organization_id,
                error=str(e)
            )
            raise
    
    def search(
        self,
        organization_id: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar embeddings in the organization's collection.
        
        Args:
            organization_id: UUID of the organization
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with search results
        """
        collection = self.get_or_create_collection(organization_id)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            logger.info(
                "search_completed",
                organization_id=organization_id,
                n_results=n_results
            )
            
            return results
        except Exception as e:
            logger.error(
                "search_failed",
                organization_id=organization_id,
                error=str(e)
            )
            raise
    
    def delete_by_policy(self, organization_id: str, policy_id: str) -> None:
        """
        Delete all embeddings for a specific policy.
        
        Args:
            organization_id: UUID of the organization
            policy_id: UUID of the policy
        """
        collection = self.get_or_create_collection(organization_id)
        
        try:
            collection.delete(
                where={"policy_id": str(policy_id)}
            )
            
            logger.info(
                "policy_embeddings_deleted",
                organization_id=organization_id,
                policy_id=policy_id
            )
        except Exception as e:
            logger.error(
                "policy_embeddings_delete_failed",
                organization_id=organization_id,
                policy_id=policy_id,
                error=str(e)
            )
            raise
    
    def get_collection_count(self, organization_id: str) -> int:
        """
        Get the number of embeddings in an organization's collection.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            Count of embeddings
        """
        collection = self.get_or_create_collection(organization_id)
        return collection.count()
