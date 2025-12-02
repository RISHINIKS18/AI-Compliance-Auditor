"""
Pydantic schemas for embedding endpoints.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request schema for semantic search."""
    query: str = Field(..., description="Query text to search for")
    n_results: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    policy_id: Optional[str] = Field(None, description="Optional policy ID to filter results")


class SearchResultItem(BaseModel):
    """Individual search result item."""
    chunk_id: str
    policy_id: str
    chunk_index: int
    content: str
    distance: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response schema for semantic search."""
    query: str
    results: List[SearchResultItem]
    count: int
