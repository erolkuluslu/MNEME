"""
Shared Test Fixtures for MNEME Test Suite

Provides common fixtures for unit and integration tests.
"""

import pytest
from typing import List
from dataclasses import replace

from src.models.chunk import Chunk
from src.models.query import (
    QueryPlan,
    QueryType,
    QueryIntent,
    QueryFilters,
    QueryExpansion,
)
from src.models.retrieval import (
    ScoredChunk,
    RetrievalResult,
    RetrievalConfidence,
)
from src.config import MNEMEConfig


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def test_config() -> MNEMEConfig:
    """Create a test configuration."""
    return MNEMEConfig.for_testing()


@pytest.fixture
def small_context_config() -> MNEMEConfig:
    """Config with small context limit for truncation tests."""
    config = MNEMEConfig.for_testing()
    return config


# =============================================================================
# Chunk Fixtures
# =============================================================================


@pytest.fixture
def make_chunk():
    """Factory fixture for creating Chunk instances."""
    def _make_chunk(
        chunk_id: str = "test_chunk",
        doc_id: str = "test_doc",
        text: str = "Test content for the chunk.",
        year: int = 2021,
        category: str = "test",
        chunk_index: int = 0,
    ) -> Chunk:
        return Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            text=text,
            year=year,
            category=category,
            chunk_index=chunk_index,
        )
    return _make_chunk


@pytest.fixture
def chunk_2021(make_chunk) -> Chunk:
    """A chunk from year 2021."""
    return make_chunk(
        chunk_id="chunk_2021_1",
        doc_id="doc_2021",
        text="AI developments in 2021 were significant, including GPT-3 applications.",
        year=2021,
        category="ai_ml",
    )


@pytest.fixture
def chunk_2020(make_chunk) -> Chunk:
    """A chunk from year 2020."""
    return make_chunk(
        chunk_id="chunk_2020_1",
        doc_id="doc_2020",
        text="In 2020, the pandemic changed how we work with technology.",
        year=2020,
        category="technology",
    )


@pytest.fixture
def chunk_2022(make_chunk) -> Chunk:
    """A chunk from year 2022."""
    return make_chunk(
        chunk_id="chunk_2022_1",
        doc_id="doc_2022",
        text="2022 saw the rise of large language models and ChatGPT.",
        year=2022,
        category="ai_ml",
    )


@pytest.fixture
def multi_year_chunks(make_chunk) -> List[Chunk]:
    """Collection of chunks from multiple years."""
    return [
        make_chunk(chunk_id="c1", year=2020, text="Content from 2020"),
        make_chunk(chunk_id="c2", year=2020, text="More content from 2020"),
        make_chunk(chunk_id="c3", year=2021, text="Content from 2021"),
        make_chunk(chunk_id="c4", year=2021, text="More content from 2021"),
        make_chunk(chunk_id="c5", year=2021, text="Even more from 2021"),
        make_chunk(chunk_id="c6", year=2022, text="Content from 2022"),
        make_chunk(chunk_id="c7", year=2022, text="More content from 2022"),
        make_chunk(chunk_id="c8", year=2023, text="Content from 2023"),
    ]


# =============================================================================
# ScoredChunk Fixtures
# =============================================================================


@pytest.fixture
def make_scored_chunk(make_chunk):
    """Factory fixture for creating ScoredChunk instances."""
    def _make_scored_chunk(
        chunk: Chunk = None,
        year_matched: bool = False,
        category_matched: bool = False,
        final_score: float = 0.5,
        year: int = None,
        **kwargs,
    ) -> ScoredChunk:
        if chunk is None:
            if year is not None:
                chunk = make_chunk(year=year)
            else:
                chunk = make_chunk()

        return ScoredChunk(
            chunk=chunk,
            vector_score=kwargs.get("vector_score", 0.5),
            bm25_score=kwargs.get("bm25_score", 1.0),
            combined_score=kwargs.get("combined_score", final_score),
            final_score=final_score,
            year_boost=0.5 if year_matched else 0.0,
            category_boost=0.2 if category_matched else 0.0,
            year_matched=year_matched,
            category_matched=category_matched,
            rank=kwargs.get("rank", 0),
        )
    return _make_scored_chunk


@pytest.fixture
def year_matched_scored_chunks(make_chunk, make_scored_chunk) -> List[ScoredChunk]:
    """Scored chunks with some matching year 2021."""
    chunks = [
        make_chunk(chunk_id="c1", year=2021, text="First 2021 content"),
        make_chunk(chunk_id="c2", year=2021, text="Second 2021 content"),
        make_chunk(chunk_id="c3", year=2021, text="Third 2021 content"),
        make_chunk(chunk_id="c4", year=2020, text="Content from 2020"),
        make_chunk(chunk_id="c5", year=2022, text="Content from 2022"),
    ]

    return [
        make_scored_chunk(chunk=chunks[0], year_matched=True, final_score=0.9),
        make_scored_chunk(chunk=chunks[1], year_matched=True, final_score=0.85),
        make_scored_chunk(chunk=chunks[2], year_matched=True, final_score=0.8),
        make_scored_chunk(chunk=chunks[3], year_matched=False, final_score=0.7),
        make_scored_chunk(chunk=chunks[4], year_matched=False, final_score=0.65),
    ]


# =============================================================================
# QueryPlan Fixtures
# =============================================================================


@pytest.fixture
def make_query_plan():
    """Factory fixture for creating QueryPlan instances."""
    def _make_query_plan(
        query: str = "Test query",
        query_type: QueryType = QueryType.SPECIFIC,
        intent: QueryIntent = QueryIntent.FACTUAL,
        year_filter: int = None,
        category_filter: str = None,
        complexity_score: float = 0.5,
        min_docs: int = 5,
        max_docs: int = 10,
    ) -> QueryPlan:
        filters = QueryFilters(
            year_filter=year_filter,
            category_filter=category_filter,
            require_year_match=year_filter is not None,
        )

        expansion = QueryExpansion(original_query=query)

        return QueryPlan(
            original_query=query,
            query_type=query_type,
            intent=intent,
            filters=filters,
            expansion=expansion,
            min_docs=min_docs,
            max_docs=max_docs,
            complexity_score=complexity_score,
        )
    return _make_query_plan


@pytest.fixture
def simple_query_plan(make_query_plan) -> QueryPlan:
    """A simple specific query plan."""
    return make_query_plan(
        query="What is GPT?",
        query_type=QueryType.SPECIFIC,
        complexity_score=0.2,
    )


@pytest.fixture
def temporal_query_plan_2021(make_query_plan) -> QueryPlan:
    """A temporal query plan for 2021."""
    return make_query_plan(
        query="What happened in AI in 2021?",
        query_type=QueryType.TEMPORAL,
        year_filter=2021,
        complexity_score=0.45,
    )


@pytest.fixture
def synthesis_query_plan(make_query_plan) -> QueryPlan:
    """A synthesis query plan."""
    return make_query_plan(
        query="Compare AI developments from 2020 to 2023",
        query_type=QueryType.SYNTHESIS,
        complexity_score=0.75,
    )


# =============================================================================
# RetrievalResult Fixtures
# =============================================================================


@pytest.fixture
def make_retrieval_result(make_scored_chunk):
    """Factory fixture for creating RetrievalResult instances."""
    def _make_retrieval_result(
        candidates: List[ScoredChunk] = None,
        year_filter: int = None,
        confidence: RetrievalConfidence = RetrievalConfidence.GOOD_MATCH,
    ) -> RetrievalResult:
        if candidates is None:
            candidates = [make_scored_chunk() for _ in range(5)]

        return RetrievalResult(
            candidates=candidates,
            query="Test query",
            retrieval_strategy="hybrid_rrf",
            year_filter=year_filter,
            confidence=confidence,
        )
    return _make_retrieval_result


@pytest.fixture
def retrieval_result_with_year_match(
    year_matched_scored_chunks,
    make_retrieval_result,
) -> RetrievalResult:
    """Retrieval result with year-matched chunks for 2021."""
    return make_retrieval_result(
        candidates=year_matched_scored_chunks,
        year_filter=2021,
        confidence=RetrievalConfidence.YEAR_MATCHED,
    )


# =============================================================================
# Context/Truncation Test Fixtures
# =============================================================================


@pytest.fixture
def large_text_chunks(make_chunk) -> List[Chunk]:
    """Chunks with large text content for truncation tests."""
    # Create chunks with substantial text (500+ chars each)
    base_text = "This is a chunk of substantial text content. " * 25

    return [
        make_chunk(
            chunk_id=f"large_c{i}",
            year=year,
            text=f"[Year {year}] {base_text}",
            doc_id=f"doc_{year}",
        )
        for i, year in enumerate([2021, 2021, 2021, 2020, 2020, 2022, 2022])
    ]


@pytest.fixture
def scored_large_chunks(large_text_chunks, make_scored_chunk) -> List[ScoredChunk]:
    """Large scored chunks with year matching for 2021."""
    return [
        make_scored_chunk(
            chunk=chunk,
            year_matched=(chunk.year == 2021),
            final_score=0.9 - (i * 0.05),
            rank=i,
        )
        for i, chunk in enumerate(large_text_chunks)
    ]
