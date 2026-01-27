"""
API Routes

FastAPI route definitions for the MNEME API.
"""

from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from .schemas import (
    QueryRequest,
    QueryResponse,
    CitationSchema,
    StatsResponse,
    HealthResponse,
)
from .dependencies import get_mneme, get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["mneme"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_available=True,  # Would check actual availability
        embedding_available=True,
    )


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    mneme=Depends(get_mneme),
):
    """
    Query the MNEME system.

    Takes a question and optional filters, returns an answer with citations.
    """
    try:
        # Call MNEME
        result = mneme.query(request.question)

        # Convert citations
        citations = [
            CitationSchema.from_citation(c) for c in result.citations
        ]

        return QueryResponse(
            answer=result.answer,
            citations=citations,
            confidence=result.confidence,
            quality=result.quality.value,
            latency_ms=result.latency_ms,
            query_type=result.query_type,
            year_filter=result.year_filter,
            category_filter=result.category_filter,
            num_sources=result.num_sources_used,
            years_covered=result.years_covered,
            categories_covered=result.categories_covered,
            coverage_gaps=result.coverage_gaps,
        )

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(mneme=Depends(get_mneme)):
    """Get system statistics."""
    try:
        stats = mneme.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/years")
async def get_available_years(mneme=Depends(get_mneme)):
    """Get list of available years in the corpus."""
    return {"years": mneme.retrieval_engine.get_available_years()}


@router.get("/categories")
async def get_available_categories(mneme=Depends(get_mneme)):
    """Get list of available categories in the corpus."""
    return {"categories": mneme.retrieval_engine.get_available_categories()}


def create_app():
    """Create FastAPI application."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="MNEME RAG API",
        description="7-Layer MNEME RAG System API",
        version="1.0.0",
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include router
    app.include_router(router)

    return app
