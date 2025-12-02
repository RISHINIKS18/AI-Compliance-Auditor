"""
Embedding service for generating vector embeddings using OpenAI API.
"""
import os
import time
from typing import List, Dict, Any
import openai
import structlog

logger = structlog.get_logger()


class EmbeddingService:
    """
    Service for generating embeddings with batch processing and retry logic.
    """
    
    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
        self.max_retries = 3
        self.base_delay = 1  # seconds
        
        logger.info(
            "embedding_service_initialized",
            model=self.model,
            batch_size=self.batch_size
        )
    
    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with batch processing.
        
        Args:
            texts: List of text strings to embed
            batch_size: Optional batch size override
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        batch_size = batch_size or self.batch_size
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            logger.info(
                "processing_batch",
                batch_num=batch_num,
                total_batches=total_batches,
                batch_size=len(batch)
            )
            
            batch_embeddings = self._generate_batch_with_retry(batch)
            all_embeddings.extend(batch_embeddings)
        
        logger.info(
            "embeddings_generated",
            total_count=len(all_embeddings)
        )
        
        return all_embeddings
    
    def _generate_batch_with_retry(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch with exponential backoff retry logic.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                
                # Extract embeddings from response
                embeddings = [item.embedding for item in response.data]
                
                return embeddings
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        "rate_limit_hit_retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "rate_limit_max_retries_exceeded",
                        error=str(e)
                    )
                    raise
                    
            except openai.APIError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        "api_error_retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "api_error_max_retries_exceeded",
                        error=str(e)
                    )
                    raise
                    
            except Exception as e:
                logger.error(
                    "embedding_generation_failed",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception("Failed to generate embeddings after all retries")
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
