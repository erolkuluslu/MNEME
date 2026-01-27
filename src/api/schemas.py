"""
API Schemas

Pydantic models for API request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    question: str = Field(..., description="The question to answer")
    year_filter: Optional[int] = Field(None, description="Filter by specific year")
    category_filter: Optional[str] = Field(None, description="Filter by category")
    max_results: Optional[int] = Field(10, description="Maximum number of results")


class CitationSchema(BaseModel):
    """Schema for a citation."""

    index: int
    doc_id: str
    year: int
    category: str
    title: Optional[str] = None
    relevance_score: float
    year_matched: bool
    excerpt: str

    @classmethod
    def from_citation(cls, citation) -> "CitationSchema":
        """Create from Citation model."""
        return cls(
            index=citation.index,
            doc_id=citation.doc_id,
            year=citation.year,
            category=citation.category,
            title=citation.title,
            relevance_score=citation.relevance_score,
            year_matched=citation.year_matched,
            excerpt=citation.excerpt,
        )


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    answer: str
    citations: List[CitationSchema]
    confidence: str
    quality: str
    latency_ms: float
    query_type: str
    year_filter: Optional[int] = None
    category_filter: Optional[str] = None
    num_sources: int
    years_covered: List[int]
    categories_covered: List[str]
    coverage_gaps: List[str]


class StatsResponse(BaseModel):
    """Response model for stats endpoint."""

    num_chunks: int
    num_nodes: int
    num_edges: int
    available_years: List[int]
    available_categories: List[str]
    embedding_dimension: int


class IndexRequest(BaseModel):
    """Request model for index endpoint."""

    directory: str = Field(..., description="Directory path to index")
    rebuild: bool = Field(False, description="Force rebuild if exists")


class IndexResponse(BaseModel):
    """Response model for index endpoint."""

    success: bool
    message: str
    num_documents: int = 0
    num_chunks: int = 0


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str = "1.0.0"
    llm_available: bool
    embedding_available: bool
