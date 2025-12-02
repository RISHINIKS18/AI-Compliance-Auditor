"""Text chunker for splitting documents into token-sized chunks."""
from typing import List, Dict
import tiktoken
import numpy as np
import structlog

logger = structlog.get_logger()


class TextChunk:
    """Represents a chunk of text with metadata."""
    
    def __init__(self, content: str, chunk_index: int, token_count: int):
        self.content = content
        self.chunk_index = chunk_index
        self.token_count = token_count
    
    def to_dict(self) -> Dict:
        """Convert chunk to dictionary."""
        return {
            "content": self.content,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count
        }


class TextChunker:
    """Chunker for splitting text into token-sized windows with overlap."""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target size of each chunk in tokens (default: 500)
            chunk_overlap: Number of tokens to overlap between chunks (default: 50)
            encoding_name: Tiktoken encoding to use (default: cl100k_base for GPT-3.5/4)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize tiktoken encoder
        try:
            self.encoder = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(
                "tiktoken_encoding_failed",
                encoding_name=encoding_name,
                error=str(e)
            )
            # Fallback to a default encoding
            self.encoder = tiktoken.get_encoding("cl100k_base")
        
        logger.info(
            "text_chunker_initialized",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            encoding=encoding_name
        )
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Split text into chunks of approximately chunk_size tokens with overlap.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            logger.warning("empty_text_provided_for_chunking")
            return []
        
        # Encode the entire text into tokens
        tokens = self.encoder.encode(text)
        total_tokens = len(tokens)
        
        logger.info(
            "chunking_text",
            total_tokens=total_tokens,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # If text is smaller than chunk size, return as single chunk
        if total_tokens <= self.chunk_size:
            return [TextChunk(
                content=text,
                chunk_index=0,
                token_count=total_tokens
            )]
        
        # Calculate chunk positions using NumPy for efficiency
        chunks = []
        chunk_index = 0
        start_idx = 0
        
        while start_idx < total_tokens:
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, total_tokens)
            
            # Extract tokens for this chunk
            chunk_tokens = tokens[start_idx:end_idx]
            
            # Decode tokens back to text
            chunk_text = self.encoder.decode(chunk_tokens)
            
            # Create chunk object
            chunk = TextChunk(
                content=chunk_text,
                chunk_index=chunk_index,
                token_count=len(chunk_tokens)
            )
            chunks.append(chunk)
            
            # Move to next chunk position with overlap
            # If this is the last chunk, break
            if end_idx >= total_tokens:
                break
            
            # Calculate next start position (with overlap)
            start_idx = end_idx - self.chunk_overlap
            chunk_index += 1
        
        logger.info(
            "text_chunked",
            total_chunks=len(chunks),
            total_tokens=total_tokens,
            avg_chunk_size=np.mean([c.token_count for c in chunks]) if chunks else 0
        )
        
        return chunks
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        tokens = self.encoder.encode(text)
        return len(tokens)
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict:
        """
        Calculate statistics about chunks using NumPy.
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_tokens": 0,
                "avg_tokens_per_chunk": 0,
                "min_tokens": 0,
                "max_tokens": 0,
                "std_tokens": 0
            }
        
        token_counts = np.array([chunk.token_count for chunk in chunks])
        
        return {
            "total_chunks": len(chunks),
            "total_tokens": int(np.sum(token_counts)),
            "avg_tokens_per_chunk": float(np.mean(token_counts)),
            "min_tokens": int(np.min(token_counts)),
            "max_tokens": int(np.max(token_counts)),
            "std_tokens": float(np.std(token_counts))
        }


# Create a singleton instance for easy import
text_chunker = TextChunker()
