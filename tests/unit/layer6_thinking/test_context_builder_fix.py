"""
Tests for Context Builder Bug Fix

TDD tests for Phase C: Answer Generation Bug Fixes.
CRITICAL: Tests that year-matched chunks are NEVER truncated.
"""

import pytest
from typing import List

from src.models.chunk import Chunk
from src.models.query import QueryPlan, QueryType, QueryFilters, QueryExpansion
from src.models.retrieval import ScoredChunk, RetrievalResult, RetrievalConfidence


class TestYearMatchedChunksNeverTruncated:
    """
    CRITICAL: Year-matched chunks must NEVER be truncated from context.

    This is the core bug fix - when context is truncated for length,
    year-matched chunks should always be preserved.
    """

    @pytest.fixture
    def small_context_builder(self):
        """Create context builder with small limit for truncation tests."""
        from src.layer6_thinking.context_builder import ContextBuilder
        # Very small limit to force truncation
        return ContextBuilder(max_context_length=2000)

    @pytest.fixture
    def chunks_with_years(self, make_chunk) -> List[Chunk]:
        """Create chunks with different years."""
        # Generate substantial text to force truncation
        base_text = "This is substantial content. " * 30  # ~720 chars each

        return [
            make_chunk(chunk_id="c1", year=2021, text=f"[2021-1] {base_text}"),
            make_chunk(chunk_id="c2", year=2021, text=f"[2021-2] {base_text}"),
            make_chunk(chunk_id="c3", year=2021, text=f"[2021-3] {base_text}"),
            make_chunk(chunk_id="c4", year=2020, text=f"[2020-1] {base_text}"),
            make_chunk(chunk_id="c5", year=2020, text=f"[2020-2] {base_text}"),
            make_chunk(chunk_id="c6", year=2022, text=f"[2022-1] {base_text}"),
            make_chunk(chunk_id="c7", year=2022, text=f"[2022-2] {base_text}"),
        ]

    @pytest.fixture
    def scored_chunks_2021(self, chunks_with_years, make_scored_chunk) -> List[ScoredChunk]:
        """Scored chunks with year matching for 2021."""
        scored = []
        for i, chunk in enumerate(chunks_with_years):
            year_matched = chunk.year == 2021
            scored.append(make_scored_chunk(
                chunk=chunk,
                year_matched=year_matched,
                final_score=0.9 - (i * 0.05),
                rank=i,
            ))
        return scored

    @pytest.fixture
    def retrieval_result_2021(self, scored_chunks_2021) -> RetrievalResult:
        """Retrieval result with 2021 year filter."""
        return RetrievalResult(
            candidates=scored_chunks_2021,
            query="What happened in AI in 2021?",
            year_filter=2021,
            confidence=RetrievalConfidence.YEAR_MATCHED,
        )

    @pytest.fixture
    def query_plan_2021(self, make_query_plan) -> QueryPlan:
        """Query plan with 2021 year filter."""
        return make_query_plan(
            query="What happened in AI in 2021?",
            query_type=QueryType.TEMPORAL,
            year_filter=2021,
        )

    def test_year_matched_chunks_never_truncated(
        self,
        small_context_builder,
        retrieval_result_2021,
        query_plan_2021,
    ):
        """CRITICAL: Year-matched chunks should NEVER be truncated."""
        context = small_context_builder.build_context(
            retrieval_result_2021,
            query_plan_2021,
        )

        # All 3 year-matched chunks (2021) must be present
        # They are indexed [1], [2], [3] in the context
        assert "[2021-1]" in context, "First 2021 chunk missing"
        assert "[2021-2]" in context, "Second 2021 chunk missing"
        assert "[2021-3]" in context, "Third 2021 chunk missing"

    def test_citation_indices_match_actual_context(
        self,
        small_context_builder,
        retrieval_result_2021,
        query_plan_2021,
    ):
        """Citation indices must match chunks actually in context."""
        context, index_map = small_context_builder.build_indexed_context(
            retrieval_result_2021,
            query_plan_2021,
        )

        valid_indices = small_context_builder.get_valid_citation_indices(
            retrieval_result_2021,
            query_plan_2021,
        )

        # Every valid citation index should be in the index map
        for idx in valid_indices:
            assert idx in index_map, f"Citation index {idx} not in index_map"
            # And the chunk should actually be present in context
            assert f"[{idx}]" in context, f"Citation [{idx}] not in context"

    def test_truncation_only_affects_other_year_chunks(
        self,
        small_context_builder,
        retrieval_result_2021,
        query_plan_2021,
    ):
        """When truncation occurs, only other-year chunks should be affected."""
        context = small_context_builder.build_context(
            retrieval_result_2021,
            query_plan_2021,
        )

        # Count year occurrences in context
        year_2021_count = context.count("Year: 2021")
        year_2020_count = context.count("Year: 2020")
        year_2022_count = context.count("Year: 2022")

        # All 3 year-matched chunks must be preserved
        assert year_2021_count == 3, f"Expected 3 year-2021 chunks, found {year_2021_count}"

        # Other years may be truncated (total of 4 other-year chunks)
        # At least some should be truncated given small context
        total_other = year_2020_count + year_2022_count
        assert total_other < 4, "Truncation should have removed some other-year chunks"

    def test_context_separates_year_matched_first(
        self,
        small_context_builder,
        retrieval_result_2021,
        query_plan_2021,
    ):
        """Year-matched sources should appear before other-year sources."""
        context = small_context_builder.build_context(
            retrieval_result_2021,
            query_plan_2021,
        )

        # Find positions of year-matched vs other-year content
        first_2021_pos = context.find("Year: 2021")
        first_2020_pos = context.find("Year: 2020")
        first_2022_pos = context.find("Year: 2022")

        # 2021 content should come first
        assert first_2021_pos >= 0, "Should have 2021 content"

        if first_2020_pos >= 0:
            assert first_2021_pos < first_2020_pos, "2021 should come before 2020"

        if first_2022_pos >= 0:
            assert first_2021_pos < first_2022_pos, "2021 should come before 2022"


class TestIndexedContextMapping:
    """Tests for indexed context with proper citation mapping."""

    @pytest.fixture
    def context_builder(self):
        """Create standard context builder."""
        from src.layer6_thinking.context_builder import ContextBuilder
        return ContextBuilder()

    def test_build_indexed_context_returns_correct_types(
        self,
        context_builder,
        retrieval_result_with_year_match,
        temporal_query_plan_2021,
    ):
        """build_indexed_context should return (str, dict) tuple."""
        result = context_builder.build_indexed_context(
            retrieval_result_with_year_match,
            temporal_query_plan_2021,
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # context
        assert isinstance(result[1], dict)  # index_map

    def test_index_map_contains_all_context_chunks(
        self,
        context_builder,
        retrieval_result_with_year_match,
        temporal_query_plan_2021,
    ):
        """Index map should contain entries for all chunks in context."""
        context, index_map = context_builder.build_indexed_context(
            retrieval_result_with_year_match,
            temporal_query_plan_2021,
        )

        # Count citation markers in context
        citation_count = sum(1 for i in range(1, 20) if f"[{i}]" in context)

        # Index map should have at least as many entries as citations in context
        assert len(index_map) >= citation_count

    def test_index_map_values_are_chunks(
        self,
        context_builder,
        retrieval_result_with_year_match,
        temporal_query_plan_2021,
    ):
        """Index map values should be Chunk objects."""
        _, index_map = context_builder.build_indexed_context(
            retrieval_result_with_year_match,
            temporal_query_plan_2021,
        )

        for idx, chunk in index_map.items():
            assert isinstance(chunk, Chunk), f"Index {idx} value is not a Chunk"


class TestValidCitationIndices:
    """Tests for valid citation index calculation."""

    @pytest.fixture
    def context_builder(self):
        """Create standard context builder."""
        from src.layer6_thinking.context_builder import ContextBuilder
        return ContextBuilder()

    def test_valid_indices_with_year_filter_only_year_matched(
        self,
        context_builder,
        retrieval_result_with_year_match,
    ):
        """With year filter and require_year_match, only year-matched indices valid."""
        # Create plan that requires year match
        plan = QueryPlan(
            original_query="Test",
            query_type=QueryType.TEMPORAL,
            intent=pytest.importorskip("src.models.query").QueryIntent.FACTUAL,
            filters=QueryFilters(year_filter=2021, require_year_match=True),
            expansion=QueryExpansion(original_query="Test"),
        )

        valid_indices = context_builder.get_valid_citation_indices(
            retrieval_result_with_year_match,
            plan,
        )

        # Should only include year-matched chunks
        for idx in valid_indices:
            chunk_idx = idx - 1  # Convert to 0-based
            assert retrieval_result_with_year_match.candidates[chunk_idx].year_matched

    def test_valid_indices_without_year_filter_includes_all(
        self,
        context_builder,
        make_retrieval_result,
    ):
        """Without year filter, all indices should be valid."""
        result = make_retrieval_result(year_filter=None)

        plan = QueryPlan(
            original_query="Test",
            query_type=QueryType.SPECIFIC,
            intent=pytest.importorskip("src.models.query").QueryIntent.FACTUAL,
            filters=QueryFilters(year_filter=None, require_year_match=False),
            expansion=QueryExpansion(original_query="Test"),
        )

        valid_indices = context_builder.get_valid_citation_indices(result, plan)

        # All indices should be valid
        assert len(valid_indices) == len(result.candidates)


class TestContextBuilderEdgeCases:
    """Edge case tests for context builder."""

    @pytest.fixture
    def context_builder(self):
        """Create standard context builder."""
        from src.layer6_thinking.context_builder import ContextBuilder
        return ContextBuilder()

    def test_empty_candidates_returns_empty_string(
        self,
        context_builder,
        make_retrieval_result,
        make_query_plan,
    ):
        """Empty candidates should return empty context."""
        result = make_retrieval_result(candidates=[])
        plan = make_query_plan()

        context = context_builder.build_context(result, plan)
        assert context == ""

    def test_no_year_matched_chunks_still_returns_context(
        self,
        context_builder,
        make_scored_chunk,
        make_retrieval_result,
        make_query_plan,
    ):
        """When no chunks match year, should still return other chunks."""
        # All chunks from 2020, filter for 2021
        scored_chunks = [
            make_scored_chunk(year=2020, year_matched=False, final_score=0.8),
            make_scored_chunk(year=2020, year_matched=False, final_score=0.7),
        ]

        result = make_retrieval_result(candidates=scored_chunks, year_filter=2021)
        plan = make_query_plan(year_filter=2021)

        context = context_builder.build_context(result, plan)

        # Should still have content from the 2020 chunks
        assert len(context) > 0
        assert "Year: 2020" in context
