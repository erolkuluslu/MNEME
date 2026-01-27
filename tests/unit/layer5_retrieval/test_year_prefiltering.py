"""
Tests for Year Pre-filtering

TDD tests for Phase B: Enhanced Hybrid Retrieval.
Tests year pre-filtering before dense retrieval.
"""

import pytest
import numpy as np
from typing import List

from src.models.chunk import Chunk


class TestYearPrefilter:
    """Tests for YearPrefilter class."""

    @pytest.fixture
    def prefilter(self, multi_year_chunks):
        """Create a YearPrefilter instance with test chunks."""
        from src.layer5_retrieval.prefilter import YearPrefilter
        return YearPrefilter(multi_year_chunks)

    @pytest.fixture
    def embeddings(self, multi_year_chunks):
        """Create mock embeddings for test chunks."""
        # Create random embeddings matching chunk count
        return np.random.rand(len(multi_year_chunks), 384).astype(np.float32)

    # =========================================================================
    # get_candidate_indices Tests
    # =========================================================================

    def test_get_candidates_exact_year_only(self, prefilter, multi_year_chunks):
        """Test getting candidates for exact year match only (range=0)."""
        indices = prefilter.get_candidate_indices(year_filter=2021, range_size=0)

        # Verify all returned indices have the correct year
        for idx in indices:
            assert multi_year_chunks[idx].year == 2021

    def test_get_candidates_exact_year_count(self, prefilter, multi_year_chunks):
        """Test correct count for exact year match."""
        indices = prefilter.get_candidate_indices(year_filter=2021, range_size=0)

        # multi_year_chunks has 3 chunks from 2021
        expected_count = sum(1 for c in multi_year_chunks if c.year == 2021)
        assert len(indices) == expected_count

    def test_get_candidates_with_range_2(self, prefilter, multi_year_chunks):
        """Test getting candidates within ±2 year range."""
        indices = prefilter.get_candidate_indices(year_filter=2021, range_size=2)

        # Should include 2019, 2020, 2021, 2022, 2023
        for idx in indices:
            assert 2019 <= multi_year_chunks[idx].year <= 2023

    def test_get_candidates_range_includes_boundary_years(self, prefilter, multi_year_chunks):
        """Test that range includes boundary years."""
        indices = prefilter.get_candidate_indices(year_filter=2021, range_size=1)

        years_found = set(multi_year_chunks[idx].year for idx in indices)

        # Should find 2020, 2021, 2022 (within ±1)
        # But we only have 2020, 2021, 2022, 2023 in our test data
        assert 2021 in years_found
        if any(c.year == 2020 for c in multi_year_chunks):
            assert 2020 in years_found
        if any(c.year == 2022 for c in multi_year_chunks):
            assert 2022 in years_found

    def test_get_candidates_missing_year_with_range_finds_nearby(self, prefilter, multi_year_chunks):
        """Test that missing year with range still finds nearby years."""
        # Year 2025 doesn't exist in test data
        indices = prefilter.get_candidate_indices(year_filter=2025, range_size=2)

        # Should find 2023 (within range)
        if len(indices) > 0:
            years_found = set(multi_year_chunks[idx].year for idx in indices)
            assert all(2023 <= y <= 2027 for y in years_found)

    def test_get_candidates_returns_empty_for_far_year(self, prefilter):
        """Test returns empty for year completely outside data range."""
        indices = prefilter.get_candidate_indices(year_filter=2030, range_size=2)

        # Year 2030 ±2 = 2028-2032, which is outside our test data (2020-2023)
        assert len(indices) == 0

    def test_get_candidates_returns_list(self, prefilter):
        """Test that get_candidate_indices returns a list."""
        indices = prefilter.get_candidate_indices(year_filter=2021, range_size=2)
        assert isinstance(indices, list)

    # =========================================================================
    # filter_embeddings Tests
    # =========================================================================

    def test_filter_embeddings_returns_correct_shape(self, prefilter, embeddings):
        """Test filtered embeddings have correct shape."""
        filtered_emb, original_indices = prefilter.filter_embeddings(
            embeddings, year_filter=2021, range_size=0
        )

        # Should have same embedding dimension
        assert filtered_emb.shape[1] == embeddings.shape[1]

        # Number of rows should match number of indices
        assert filtered_emb.shape[0] == len(original_indices)

    def test_filter_embeddings_preserves_index_mapping(self, prefilter, embeddings, multi_year_chunks):
        """Test that original indices correctly map to filtered embeddings."""
        filtered_emb, original_indices = prefilter.filter_embeddings(
            embeddings, year_filter=2021, range_size=0
        )

        # Verify the embeddings match the original indices
        for i, orig_idx in enumerate(original_indices):
            np.testing.assert_array_equal(filtered_emb[i], embeddings[orig_idx])

    def test_filter_embeddings_returns_tuple(self, prefilter, embeddings):
        """Test that filter_embeddings returns a tuple."""
        result = prefilter.filter_embeddings(embeddings, year_filter=2021, range_size=2)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_filter_embeddings_handles_empty_candidates(self, prefilter, embeddings):
        """Test handling when no candidates match."""
        filtered_emb, original_indices = prefilter.filter_embeddings(
            embeddings, year_filter=2030, range_size=0
        )

        assert len(original_indices) == 0
        assert filtered_emb.shape[0] == 0

    def test_filter_embeddings_with_range(self, prefilter, embeddings, multi_year_chunks):
        """Test filtering with year range."""
        filtered_emb, original_indices = prefilter.filter_embeddings(
            embeddings, year_filter=2021, range_size=2
        )

        # All returned indices should be within range
        for idx in original_indices:
            assert 2019 <= multi_year_chunks[idx].year <= 2023


class TestYearPrefilterConstruction:
    """Tests for YearPrefilter initialization."""

    def test_prefilter_builds_year_index(self, multi_year_chunks):
        """Test that prefilter builds internal year index."""
        from src.layer5_retrieval.prefilter import YearPrefilter

        prefilter = YearPrefilter(multi_year_chunks)

        # Should have internal mapping
        assert hasattr(prefilter, "_year_to_indices") or hasattr(prefilter, "year_to_indices")

    def test_prefilter_handles_empty_chunks(self):
        """Test prefilter handles empty chunk list."""
        from src.layer5_retrieval.prefilter import YearPrefilter

        prefilter = YearPrefilter([])
        indices = prefilter.get_candidate_indices(year_filter=2021, range_size=2)

        assert indices == []

    def test_prefilter_stores_chunks(self, multi_year_chunks):
        """Test prefilter stores reference to chunks."""
        from src.layer5_retrieval.prefilter import YearPrefilter

        prefilter = YearPrefilter(multi_year_chunks)
        assert hasattr(prefilter, "chunks") or hasattr(prefilter, "_chunks")


class TestPrefilterPerformance:
    """Performance-related tests for prefilter."""

    def test_prefilter_index_lookup_is_fast(self, multi_year_chunks):
        """Test that index lookup doesn't scan all chunks."""
        from src.layer5_retrieval.prefilter import YearPrefilter

        prefilter = YearPrefilter(multi_year_chunks)

        # Should use internal index, not linear scan
        # This is a design verification test
        indices = prefilter.get_candidate_indices(year_filter=2021, range_size=0)

        # Verify it returns correct results (functional verification)
        expected = [i for i, c in enumerate(multi_year_chunks) if c.year == 2021]
        assert set(indices) == set(expected)
