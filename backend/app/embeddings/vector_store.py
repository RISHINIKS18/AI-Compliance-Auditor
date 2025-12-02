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
    Now uses local persistent ChromaDB instead of HTTP server.
    """

    def __init__(self):
        """Initialize local ChromaDB persistent client."""

        # Directory where ChromaDB data will be stored
        chroma_path = os.getenv("CHROMA_DB_PATH", "chroma_data")

        # Local persistent client (NO server required)
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )

        logger.info("chromadb_local_client_initialized", path=chroma_path)

    def get_collection_name(self, organization_id: str) -> str:
        """Generate organization-scoped collection name."""
        return f"org_{organization_id}_policies"

    def get_or_create_collection(self, organization_id: str):
        """Get or create a collection for an organization."""
        collection_name = self.get_collection_name(organization_id)

        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"organization_id": str(organization_id)},
                embedding_function=None  # We provide embeddings manually
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

        collection = self.get_or_create_collection(organization_id)

        try:
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

        collection = self.get_or_create_collection(organization_id)

        try:
            collection.delete(where={"policy_id": str(policy_id)})

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

        collection = self.get_or_create_collection(organization_id)
        return collection.count()
