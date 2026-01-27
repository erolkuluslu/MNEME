"""
MNEME Answer Quality Evaluation Test Suite

10-question test suite to validate:
- Year extraction accuracy
- Year match rate in citations
- Hallucination prevention
- Confidence correctness

Run with: python -m pytest tests/evaluation/test_answer_quality.py -v
"""

import pytest
from typing import Optional, List, Tuple
from dataclasses import dataclass

from src.layer4_query.filters import FilterExtractor
from src.layer7_generation.confidence import determine_confidence, ConfidenceAssessor
from src.models.retrieval import RetrievalConfidence, ScoredChunk
from src.models.chunk import Chunk


# =============================================================================
# Test Data Structures
# =============================================================================

@dataclass
class EvaluationCase:
    """A single evaluation test case."""
    query: str
    expected_year_filter: Optional[int]
    expected_year_range: Optional[Tuple[int, int]]
    description: str
    is_comparison_query: bool = False


# =============================================================================
# 10-Question Evaluation Suite
# =============================================================================

EVALUATION_CASES = [
    # Case 1: Standard year query
    EvaluationCase(
        query="What happened in AI in 2021?",
        expected_year_filter=2021,
        expected_year_range=None,
        description="Standard year query - should extract 2021",
    ),
    # Case 2: Personal thoughts query
    EvaluationCase(
        query="Tell me about my thoughts in 2020",
        expected_year_filter=2020,
        expected_year_range=None,
        description="Personal query with year - should extract 2020",
    ),
    # Case 3: Learning notes query
    EvaluationCase(
        query="Summarize learning notes from 2022",
        expected_year_filter=2022,
        expected_year_range=None,
        description="Learning notes query - should extract 2022",
    ),
    # Case 4: Ideas query with future year
    EvaluationCase(
        query="What ideas did I have in 2025?",
        expected_year_filter=2025,
        expected_year_range=None,
        description="Ideas query with year - should extract 2025",
    ),
    # Case 5: Comparison query (two years)
    EvaluationCase(
        query="Compare 2020 and 2021 experiences",
        expected_year_filter=2020,  # First year extracted
        expected_year_range=(2020, 2021),
        description="Comparison query - should extract range 2020-2021",
        is_comparison_query=True,
    ),
    # Case 6: No year filter query
    EvaluationCase(
        query="What are my saved notes?",
        expected_year_filter=None,
        expected_year_range=None,
        description="No year query - year_filter should be None",
    ),
    # Case 7: Historical year query
    EvaluationCase(
        query="Tell me about 1999",
        expected_year_filter=1999,
        expected_year_range=None,
        description="Historical year query - should extract 1999",
    ),
    # Case 8: Year in review query
    EvaluationCase(
        query="Summarize my 2023 year in review",
        expected_year_filter=2023,
        expected_year_range=None,
        description="Year in review query - should extract 2023",
    ),
    # Case 9: Specific month query
    EvaluationCase(
        query="What happened in December 2024?",
        expected_year_filter=2024,
        expected_year_range=None,
        description="Month-specific query - should extract 2024",
    ),
    # Case 10: Philosophy query
    EvaluationCase(
        query="My philosophy in 2025",
        expected_year_filter=2025,
        expected_year_range=None,
        description="Philosophy query with year - should extract 2025",
    ),
]


# =============================================================================
# Year Extraction Tests
# =============================================================================

class TestYearExtraction:
    """Tests for year extraction accuracy."""

    @pytest.fixture
    def filter_extractor(self):
        """Create a FilterExtractor instance."""
        return FilterExtractor()

    @pytest.mark.parametrize("case", EVALUATION_CASES, ids=[c.description for c in EVALUATION_CASES])
    def test_year_extraction(self, filter_extractor, case: EvaluationCase):
        """Test that years are correctly extracted from queries."""
        filters = filter_extractor.extract(case.query)

        assert filters.year_filter == case.expected_year_filter, (
            f"Query: '{case.query}'\n"
            f"Expected year_filter: {case.expected_year_filter}\n"
            f"Got: {filters.year_filter}"
        )

    @pytest.mark.parametrize("case", [c for c in EVALUATION_CASES if c.is_comparison_query],
                             ids=[c.description for c in EVALUATION_CASES if c.is_comparison_query])
    def test_year_range_extraction(self, filter_extractor, case: EvaluationCase):
        """Test that year ranges are correctly extracted for comparison queries."""
        filters = filter_extractor.extract(case.query)

        if case.expected_year_range:
            assert filters.year_range is not None, (
                f"Query: '{case.query}'\n"
                f"Expected year_range: {case.expected_year_range}\n"
                f"Got: None"
            )
            assert filters.year_range == case.expected_year_range, (
                f"Query: '{case.query}'\n"
                f"Expected year_range: {case.expected_year_range}\n"
                f"Got: {filters.year_range}"
            )


class TestYearExtractionEdgeCases:
    """Edge case tests for year extraction."""

    @pytest.fixture
    def filter_extractor(self):
        return FilterExtractor()

    def test_year_at_start_of_query(self, filter_extractor):
        """Year at the start of the query."""
        filters = filter_extractor.extract("2021 was a great year")
        assert filters.year_filter == 2021

    def test_year_at_end_of_query(self, filter_extractor):
        """Year at the end of the query."""
        filters = filter_extractor.extract("Tell me about events in 2021")
        assert filters.year_filter == 2021

    def test_multiple_same_years(self, filter_extractor):
        """Multiple occurrences of the same year."""
        filters = filter_extractor.extract("In 2021, the events of 2021 were significant")
        assert filters.year_filter == 2021
        assert filters.year_range is None  # Same year, no range

    def test_year_with_punctuation(self, filter_extractor):
        """Year followed by punctuation."""
        filters = filter_extractor.extract("What happened in 2021?")
        assert filters.year_filter == 2021

    def test_year_in_sentence_middle(self, filter_extractor):
        """Year in the middle of a sentence."""
        filters = filter_extractor.extract("The year 2021 marked a turning point")
        assert filters.year_filter == 2021

    def test_no_year_returns_none(self, filter_extractor):
        """Query without year returns None."""
        filters = filter_extractor.extract("Tell me about AI developments")
        assert filters.year_filter is None
        assert filters.year_range is None

    def test_year_with_preposition_in(self, filter_extractor):
        """Year with 'in' preposition."""
        filters = filter_extractor.extract("in 2021 we saw changes")
        assert filters.year_filter == 2021

    def test_year_with_preposition_from(self, filter_extractor):
        """Year with 'from' preposition."""
        filters = filter_extractor.extract("from 2020 onwards")
        assert filters.year_filter == 2020

    def test_year_outside_valid_range(self, filter_extractor):
        """Year outside valid range (1990-2030)."""
        filters = filter_extractor.extract("Tell me about 1885")
        assert filters.year_filter is None  # 1885 is outside 1990-2030

    def test_year_2000(self, filter_extractor):
        """Year 2000 edge case."""
        filters = filter_extractor.extract("What happened in 2000?")
        assert filters.year_filter == 2000

    def test_year_1990(self, filter_extractor):
        """Year 1990 boundary."""
        filters = filter_extractor.extract("Events in 1990")
        assert filters.year_filter == 1990


# =============================================================================
# Confidence Scoring Tests
# =============================================================================

class TestConfidenceScoring:
    """Tests for confidence scoring accuracy."""

    def test_year_matched_confidence(self):
        """When year filter is set and documents match, confidence is YEAR_MATCHED."""
        confidence = determine_confidence(
            year_matched_count=3,
            year_filter=2021,
            other_year_count=2,
        )
        assert confidence == RetrievalConfidence.YEAR_MATCHED

    def test_partial_match_when_year_not_found(self):
        """When year filter is set but no documents match, confidence is PARTIAL_MATCH."""
        confidence = determine_confidence(
            year_matched_count=0,
            year_filter=2021,
            other_year_count=5,
        )
        assert confidence == RetrievalConfidence.PARTIAL_MATCH, (
            "Should be PARTIAL_MATCH when year filter is set but no docs match"
        )

    def test_good_match_only_without_year_filter(self):
        """GOOD_MATCH should only be returned when no year filter is set."""
        confidence = determine_confidence(
            year_matched_count=0,
            year_filter=None,
            other_year_count=5,
        )
        assert confidence == RetrievalConfidence.GOOD_MATCH

    def test_no_results_when_nothing_found(self):
        """NO_RESULTS when no documents are found at all."""
        confidence = determine_confidence(
            year_matched_count=0,
            year_filter=2021,
            other_year_count=0,
        )
        assert confidence == RetrievalConfidence.NO_RESULTS

    def test_low_match_without_year_filter(self):
        """LOW_MATCH when no year filter and few results."""
        confidence = determine_confidence(
            year_matched_count=0,
            year_filter=None,
            other_year_count=2,
        )
        assert confidence == RetrievalConfidence.LOW_MATCH


class TestConfidenceAssessor:
    """Tests for the ConfidenceAssessor class."""

    @pytest.fixture
    def assessor(self):
        return ConfidenceAssessor()

    @pytest.fixture
    def mock_chunk(self):
        """Create a mock chunk."""
        return Chunk(
            chunk_id="test_chunk",
            doc_id="test_doc",
            text="Test content",
            year=2021,
            category="test",
            chunk_index=0,
        )

    def _create_scored_chunk(self, chunk: Chunk, year_matched: bool) -> ScoredChunk:
        """Helper to create a ScoredChunk."""
        return ScoredChunk(
            chunk=chunk,
            vector_score=0.5,
            bm25_score=1.0,
            combined_score=0.6,
            final_score=0.6,
            year_boost=0.5 if year_matched else 0.0,
            category_boost=0.0,
            year_matched=year_matched,
            category_matched=False,
        )

    def test_assess_year_matched(self, assessor, mock_chunk):
        """Test assess returns YEAR_MATCHED when year-matched docs exist."""
        candidates = [
            self._create_scored_chunk(mock_chunk, year_matched=True),
            self._create_scored_chunk(mock_chunk, year_matched=True),
        ]
        confidence = assessor.assess(candidates, year_filter=2021)
        assert confidence == RetrievalConfidence.YEAR_MATCHED

    def test_assess_partial_match(self, assessor, mock_chunk):
        """Test assess returns PARTIAL_MATCH when year filter set but no match."""
        candidates = [
            self._create_scored_chunk(mock_chunk, year_matched=False),
            self._create_scored_chunk(mock_chunk, year_matched=False),
            self._create_scored_chunk(mock_chunk, year_matched=False),
        ]
        confidence = assessor.assess(candidates, year_filter=2021)
        assert confidence == RetrievalConfidence.PARTIAL_MATCH

    def test_assess_good_match_no_filter(self, assessor, mock_chunk):
        """Test assess returns GOOD_MATCH when no year filter and enough results."""
        candidates = [
            self._create_scored_chunk(mock_chunk, year_matched=False),
            self._create_scored_chunk(mock_chunk, year_matched=False),
            self._create_scored_chunk(mock_chunk, year_matched=False),
        ]
        confidence = assessor.assess(candidates, year_filter=None)
        assert confidence == RetrievalConfidence.GOOD_MATCH

    def test_assess_no_results(self, assessor):
        """Test assess returns NO_RESULTS when no candidates."""
        confidence = assessor.assess([], year_filter=2021)
        assert confidence == RetrievalConfidence.NO_RESULTS


# =============================================================================
# Integration Tests (require full pipeline)
# =============================================================================

class TestYearFilterIntegration:
    """
    Integration tests that verify the full year filtering pipeline.

    These tests verify that:
    1. Year is correctly extracted from query
    2. Confidence is correctly computed based on year match
    3. The system properly handles missing year data
    """

    @pytest.fixture
    def filter_extractor(self):
        return FilterExtractor()

    @pytest.fixture
    def confidence_assessor(self):
        return ConfidenceAssessor()

    def test_full_pipeline_year_matched(self, filter_extractor, confidence_assessor):
        """Test full pipeline when year-matched documents exist."""
        # Step 1: Extract year
        query = "What happened in AI in 2021?"
        filters = filter_extractor.extract(query)
        assert filters.year_filter == 2021, "Year should be extracted"

        # Step 2: Simulate retrieval with year-matched docs
        mock_chunk = Chunk(
            chunk_id="test", doc_id="doc", text="AI text",
            year=2021, category="ai", chunk_index=0
        )
        candidates = [
            ScoredChunk(
                chunk=mock_chunk, vector_score=0.8, bm25_score=5.0,
                combined_score=0.7, final_score=1.2,
                year_boost=0.5, category_boost=0.0,
                year_matched=True, category_matched=False
            )
        ]

        # Step 3: Assess confidence
        confidence = confidence_assessor.assess(candidates, year_filter=filters.year_filter)
        assert confidence == RetrievalConfidence.YEAR_MATCHED

    def test_full_pipeline_year_unavailable(self, filter_extractor, confidence_assessor):
        """Test full pipeline when year-matched documents don't exist."""
        # Step 1: Extract year
        query = "Tell me about my thoughts in 2021"
        filters = filter_extractor.extract(query)
        assert filters.year_filter == 2021, "Year should be extracted"

        # Step 2: Simulate retrieval with NO year-matched docs
        mock_chunk = Chunk(
            chunk_id="test", doc_id="doc", text="Some text",
            year=2020, category="personal", chunk_index=0  # Wrong year
        )
        candidates = [
            ScoredChunk(
                chunk=mock_chunk, vector_score=0.7, bm25_score=4.0,
                combined_score=0.6, final_score=0.6,
                year_boost=0.0, category_boost=0.0,
                year_matched=False, category_matched=False
            )
        ]

        # Step 3: Assess confidence
        confidence = confidence_assessor.assess(candidates, year_filter=filters.year_filter)
        assert confidence == RetrievalConfidence.PARTIAL_MATCH, (
            "Should be PARTIAL_MATCH when year filter is set but no docs match"
        )


# =============================================================================
# Metrics Tracking
# =============================================================================

class TestMetrics:
    """
    Test suite that tracks key metrics for evaluation.

    Metrics tracked:
    - year_extraction_accuracy: % of queries with correct year extraction
    - confidence_correctness: % of correct confidence assessments
    """

    @pytest.fixture
    def filter_extractor(self):
        return FilterExtractor()

    def test_year_extraction_accuracy(self, filter_extractor):
        """Calculate year extraction accuracy across all test cases."""
        correct = 0
        total = len(EVALUATION_CASES)

        for case in EVALUATION_CASES:
            filters = filter_extractor.extract(case.query)
            if filters.year_filter == case.expected_year_filter:
                correct += 1
            else:
                print(f"FAIL: '{case.query}' - expected {case.expected_year_filter}, got {filters.year_filter}")

        accuracy = correct / total * 100
        print(f"\nYear Extraction Accuracy: {accuracy:.1f}% ({correct}/{total})")

        # Require 100% accuracy
        assert accuracy == 100.0, f"Year extraction accuracy {accuracy}% is below 100%"

    def test_confidence_correctness(self):
        """Test confidence scoring correctness."""
        test_cases = [
            # (year_matched_count, year_filter, other_year_count, expected_confidence)
            (3, 2021, 2, RetrievalConfidence.YEAR_MATCHED),
            (0, 2021, 5, RetrievalConfidence.PARTIAL_MATCH),
            (0, None, 5, RetrievalConfidence.GOOD_MATCH),
            (0, None, 2, RetrievalConfidence.LOW_MATCH),
            (0, 2021, 0, RetrievalConfidence.NO_RESULTS),
            (1, 2021, 0, RetrievalConfidence.YEAR_MATCHED),
        ]

        correct = 0
        for year_matched, year_filter, other_count, expected in test_cases:
            result = determine_confidence(year_matched, year_filter, other_count)
            if result == expected:
                correct += 1
            else:
                print(f"FAIL: ({year_matched}, {year_filter}, {other_count}) - expected {expected}, got {result}")

        accuracy = correct / len(test_cases) * 100
        print(f"\nConfidence Scoring Accuracy: {accuracy:.1f}% ({correct}/{len(test_cases)})")

        assert accuracy == 100.0, f"Confidence scoring accuracy {accuracy}% is below 100%"


# =============================================================================
# Run Evaluation
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
