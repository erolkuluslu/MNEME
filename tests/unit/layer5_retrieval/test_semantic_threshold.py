"""
Tests for Semantic Threshold in Hybrid RRF Strategy

CRITICAL FIX: These tests verify that:
1. Year boost is only applied when semantic relevance meets threshold
2. Multiplicative boosting replaces additive boosting
3. Semantically irrelevant chunks don't dominate due to year boost
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from src.models.chunk import Chunk
from src.models.query import QueryPlan, QueryType, QueryIntent, QueryFilters, QueryExpansion
from src.models.retrieval import ScoredChunk
from src.layer5_retrieval.strategies.hybrid_rrf import HybridRRFStrategy


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def make_ai_chunk():
    """Factory for creating AI-related chunks."""
    def _make_ai_chunk(year: int, chunk_id: str = None, text: str = None) -> Chunk:
        return Chunk(
            chunk_id=chunk_id or f"ai_chunk_{year}",
            doc_id=f"ai_doc_{year}",
            text=text or f"AI and machine learning developments in {year}. Neural networks improved.",
            year=year,
            category="ai_ml",
            chunk_index=0,
        )
    return _make_ai_chunk


@pytest.fixture
def make_personal_chunk():
    """Factory for creating personal/journal chunks (unrelated to AI)."""
    def _make_personal_chunk(year: int, chunk_id: str = None, text: str = None) -> Chunk:
        return Chunk(
            chunk_id=chunk_id or f"personal_chunk_{year}",
            doc_id=f"journal_{year}",
            text=text or f"Personal reflections from {year}. Got vaccinated today. Debugging victory.",
            year=year,
            category="personal",
            chunk_index=0,
        )
    return _make_personal_chunk


@pytest.fixture
def plan_with_year_2021():
    """QueryPlan requesting data from 2021."""
    filters = QueryFilters(year_filter=2021, require_year_match=True)
    expansion = QueryExpansion(original_query="What happened in AI in 2021?")
    return QueryPlan(
        original_query="What happened in AI in 2021?",
        query_type=QueryType.TEMPORAL,
        intent=QueryIntent.FACTUAL,
        filters=filters,
        expansion=expansion,
        min_docs=5,
        max_docs=10,
    )


@pytest.fixture
def mock_embedding_engine():
    """Mock embedding engine that returns predictable embeddings."""
    engine = Mock()
    engine.encode_query = Mock(return_value=np.random.randn(384))
    return engine


@pytest.fixture
def mock_similarity_engine():
    """Mock similarity engine."""
    engine = Mock()
    engine.is_built = True
    engine.find_similar = Mock(return_value=[])
    return engine


# =============================================================================
# Semantic Threshold Tests
# =============================================================================


class TestSemanticThresholdEnforcement:
    """Tests that semantic threshold is enforced before year boosting."""

    def test_low_relevance_chunk_gets_no_year_boost(
        self,
        make_ai_chunk,
        make_personal_chunk,
        mock_embedding_engine,
        mock_similarity_engine,
        plan_with_year_2021,
    ):
        """
        Chunks with low semantic relevance (below threshold) should NOT get year boost.

        This is the CRITICAL FIX: A personal journal from 2021 should not rank higher
        than AI content from 2020 just because it's from the target year.
        """
        # Create chunks: AI from 2020 (relevant) and personal from 2021 (irrelevant)
        ai_chunk_2020 = make_ai_chunk(year=2020, text="AI neural networks breakthroughs in 2020")
        personal_chunk_2021 = make_personal_chunk(year=2021, text="Personal vaccine day 2021")

        chunks = [ai_chunk_2020, personal_chunk_2021]
        embeddings = np.random.randn(2, 384)

        strategy = HybridRRFStrategy(
            chunks=chunks,
            embeddings=embeddings,
            embedding_engine=mock_embedding_engine,
            similarity_engine=mock_similarity_engine,
            year_boost=0.5,
            category_boost=0.2,
        )

        # Simulate combined scores with dense_score (semantic relevance)
        # AI chunk: high semantic relevance (0.65)
        # Personal chunk: low semantic relevance (0.15) - should NOT get year boost
        combined = {
            0: {"rrf_score": 0.35, "dense_score": 0.65, "sparse_score": 0.1},  # AI 2020
            1: {"rrf_score": 0.02, "dense_score": 0.15, "sparse_score": 0.01}, # Personal 2021
        }

        boosted = strategy._apply_boosting(combined, plan_with_year_2021)

        # Find the chunks in results
        ai_result = next(c for c in boosted if c.chunk.chunk_id == ai_chunk_2020.chunk_id)
        personal_result = next(c for c in boosted if c.chunk.chunk_id == personal_chunk_2021.chunk_id)

        # CRITICAL: AI chunk (semantically relevant) should rank HIGHER
        # than personal chunk (year matched but semantically irrelevant)
        assert ai_result.final_score > personal_result.final_score, (
            f"Semantically relevant AI chunk ({ai_result.final_score:.3f}) should rank higher "
            f"than semantically irrelevant personal chunk ({personal_result.final_score:.3f})"
        )

    def test_high_relevance_chunk_gets_year_boost(
        self,
        make_ai_chunk,
        mock_embedding_engine,
        mock_similarity_engine,
        plan_with_year_2021,
    ):
        """
        Chunks with high semantic relevance (above threshold) SHOULD get year boost.
        """
        # Create AI chunks from 2020 and 2021 (both semantically relevant)
        ai_chunk_2020 = make_ai_chunk(year=2020)
        ai_chunk_2021 = make_ai_chunk(year=2021)

        chunks = [ai_chunk_2020, ai_chunk_2021]
        embeddings = np.random.randn(2, 384)

        strategy = HybridRRFStrategy(
            chunks=chunks,
            embeddings=embeddings,
            embedding_engine=mock_embedding_engine,
            similarity_engine=mock_similarity_engine,
            year_boost=0.5,
            category_boost=0.2,
        )

        # Both have high semantic relevance
        combined = {
            0: {"rrf_score": 0.30, "dense_score": 0.60, "sparse_score": 0.1},  # AI 2020
            1: {"rrf_score": 0.28, "dense_score": 0.58, "sparse_score": 0.08}, # AI 2021
        }

        boosted = strategy._apply_boosting(combined, plan_with_year_2021)

        ai_2020_result = next(c for c in boosted if c.chunk.year == 2020)
        ai_2021_result = next(c for c in boosted if c.chunk.year == 2021)

        # 2021 chunk should be boosted and rank higher
        assert ai_2021_result.year_matched is True
        assert ai_2021_result.final_score > ai_2020_result.final_score, (
            f"Year-matched AI chunk from 2021 ({ai_2021_result.final_score:.3f}) should rank higher "
            f"than AI chunk from 2020 ({ai_2020_result.final_score:.3f}) due to year boost"
        )


class TestMultiplicativeBoosting:
    """Tests that boosting is multiplicative, not additive."""

    def test_boost_is_multiplicative_not_additive(
        self,
        make_ai_chunk,
        mock_embedding_engine,
        mock_similarity_engine,
        plan_with_year_2021,
    ):
        """
        Year boost should be multiplicative (amplifies relevance) not additive.

        Multiplicative: final_score = rrf_score * (1 + year_boost)
        Additive (OLD BUG): final_score = rrf_score + year_boost
        """
        chunk = make_ai_chunk(year=2021)
        chunks = [chunk]
        embeddings = np.random.randn(1, 384)

        year_boost_value = 0.5

        strategy = HybridRRFStrategy(
            chunks=chunks,
            embeddings=embeddings,
            embedding_engine=mock_embedding_engine,
            similarity_engine=mock_similarity_engine,
            year_boost=year_boost_value,
            category_boost=0.2,
        )

        rrf_score = 0.30
        dense_score = 0.60  # Above threshold

        combined = {
            0: {"rrf_score": rrf_score, "dense_score": dense_score, "sparse_score": 0.1},
        }

        boosted = strategy._apply_boosting(combined, plan_with_year_2021)
        result = boosted[0]

        # Calculate expected multiplicative score
        expected_multiplicative = rrf_score * (1 + year_boost_value)  # 0.30 * 1.5 = 0.45

        # Calculate what OLD additive score would be
        old_additive = rrf_score + year_boost_value  # 0.30 + 0.5 = 0.80

        # Final score should be multiplicative, not additive
        # Allow small tolerance for floating point
        assert abs(result.final_score - expected_multiplicative) < 0.01, (
            f"Final score ({result.final_score:.3f}) should be multiplicative "
            f"({expected_multiplicative:.3f}), not additive ({old_additive:.3f})"
        )


class TestRelevantOtherYearVsIrrelevantTargetYear:
    """
    Integration tests ensuring relevant content from other years beats
    irrelevant content from the target year.
    """

    def test_relevant_2020_beats_irrelevant_2021_in_ranking(
        self,
        make_ai_chunk,
        make_personal_chunk,
        mock_embedding_engine,
        mock_similarity_engine,
        plan_with_year_2021,
    ):
        """
        Semantic relevance should be the primary factor.

        Query: "What happened in AI in 2021?"
        - AI content from 2020 (relevant topic, wrong year) should rank HIGHER
        - Personal journal from 2021 (irrelevant topic, correct year) should rank LOWER
        """
        # Create test chunks
        chunks = [
            make_ai_chunk(year=2020, chunk_id="ai_2020", text="AI breakthroughs and neural networks in 2020"),
            make_personal_chunk(year=2021, chunk_id="vaccine_2021", text="Got my vaccine today in 2021"),
            make_personal_chunk(year=2021, chunk_id="debug_2021", text="Debugging victory celebration"),
            make_ai_chunk(year=2021, chunk_id="ai_2021", text="AI developments in 2021 were amazing"),
        ]

        embeddings = np.random.randn(4, 384)

        strategy = HybridRRFStrategy(
            chunks=chunks,
            embeddings=embeddings,
            embedding_engine=mock_embedding_engine,
            similarity_engine=mock_similarity_engine,
            year_boost=0.5,
            category_boost=0.2,
        )

        # Simulate realistic scores:
        # - AI chunks have high semantic relevance to "AI in 2021" query
        # - Personal chunks have low semantic relevance
        combined = {
            0: {"rrf_score": 0.35, "dense_score": 0.65, "sparse_score": 0.2},  # AI 2020 - relevant
            1: {"rrf_score": 0.02, "dense_score": 0.12, "sparse_score": 0.01}, # vaccine 2021 - irrelevant
            2: {"rrf_score": 0.02, "dense_score": 0.10, "sparse_score": 0.01}, # debug 2021 - irrelevant
            3: {"rrf_score": 0.32, "dense_score": 0.60, "sparse_score": 0.18}, # AI 2021 - relevant
        }

        boosted = strategy._apply_boosting(combined, plan_with_year_2021)

        # Sort by final_score (as the strategy does)
        boosted.sort(key=lambda x: x.final_score, reverse=True)

        # Get rankings
        ai_2021 = next(c for c in boosted if c.chunk.chunk_id == "ai_2021")
        ai_2020 = next(c for c in boosted if c.chunk.chunk_id == "ai_2020")
        vaccine_2021 = next(c for c in boosted if c.chunk.chunk_id == "vaccine_2021")

        # AI 2021 should be #1 (relevant + year matched)
        assert boosted[0].chunk.chunk_id == "ai_2021", (
            f"AI content from 2021 should rank first, got {boosted[0].chunk.chunk_id}"
        )

        # AI 2020 should rank higher than personal 2021
        assert ai_2020.final_score > vaccine_2021.final_score, (
            f"Relevant AI from 2020 ({ai_2020.final_score:.3f}) should rank higher "
            f"than irrelevant vaccine from 2021 ({vaccine_2021.final_score:.3f})"
        )


class TestSemanticThresholdConfiguration:
    """Tests for semantic threshold configuration."""

    def test_default_semantic_threshold_is_reasonable(
        self,
        make_personal_chunk,
        mock_embedding_engine,
        mock_similarity_engine,
        plan_with_year_2021,
    ):
        """
        Default semantic threshold should filter out clearly irrelevant chunks.
        Typical irrelevant chunks have dense_score < 0.3.
        """
        chunk = make_personal_chunk(year=2021)
        chunks = [chunk]
        embeddings = np.random.randn(1, 384)

        strategy = HybridRRFStrategy(
            chunks=chunks,
            embeddings=embeddings,
            embedding_engine=mock_embedding_engine,
            similarity_engine=mock_similarity_engine,
            year_boost=0.5,
        )

        # Check that strategy has semantic threshold attribute
        assert hasattr(strategy, 'semantic_threshold'), (
            "HybridRRFStrategy should have semantic_threshold attribute"
        )

        # Threshold should be reasonable (0.2-0.4 range)
        assert 0.1 <= strategy.semantic_threshold <= 0.5, (
            f"Semantic threshold ({strategy.semantic_threshold}) should be in reasonable range"
        )


class TestNoBoostBelowThreshold:
    """Tests that chunks below semantic threshold get no boost at all."""

    def test_chunk_below_threshold_keeps_base_score(
        self,
        make_personal_chunk,
        mock_embedding_engine,
        mock_similarity_engine,
        plan_with_year_2021,
    ):
        """
        Chunks below semantic threshold should have final_score == rrf_score (no boost).
        """
        chunk = make_personal_chunk(year=2021)
        chunks = [chunk]
        embeddings = np.random.randn(1, 384)

        strategy = HybridRRFStrategy(
            chunks=chunks,
            embeddings=embeddings,
            embedding_engine=mock_embedding_engine,
            similarity_engine=mock_similarity_engine,
            year_boost=0.5,
        )

        rrf_score = 0.02
        dense_score = 0.15  # Below default threshold of 0.3

        combined = {
            0: {"rrf_score": rrf_score, "dense_score": dense_score, "sparse_score": 0.01},
        }

        boosted = strategy._apply_boosting(combined, plan_with_year_2021)
        result = boosted[0]

        # Final score should be close to rrf_score (no year boost applied)
        assert abs(result.final_score - rrf_score) < 0.01, (
            f"Chunk below threshold should not get boost. "
            f"Final score ({result.final_score:.3f}) should equal rrf_score ({rrf_score:.3f})"
        )

        # Year boost should be 0 (or very small)
        assert result.year_boost < 0.01, (
            f"Year boost ({result.year_boost:.3f}) should be ~0 for chunks below threshold"
        )
