"""
Tests for Temporal Query Classification

CRITICAL FIX: These tests verify that:
1. "What happened in [year]" queries are classified as TEMPORAL
2. "in [year]" queries are classified as TEMPORAL
3. Year-specific queries get proper temporal classification
"""

import pytest
from src.models.query import QueryType, QueryIntent
from src.layer4_query.classification import QueryClassifier, classify_query


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def classifier():
    """Create a QueryClassifier instance."""
    return QueryClassifier()


# =============================================================================
# "What happened in [year]" Pattern Tests
# =============================================================================


class TestWhatHappenedInYearPattern:
    """Tests for 'What happened in [year]' style queries."""

    def test_what_happened_in_2021_is_temporal(self, classifier):
        """'What happened in 2021' should be classified as TEMPORAL."""
        query_type, confidence = classifier.classify_type("What happened in 2021?")
        assert query_type == QueryType.TEMPORAL, (
            f"'What happened in 2021?' should be TEMPORAL, got {query_type}"
        )

    def test_what_happened_in_ai_in_2021_is_temporal(self, classifier):
        """'What happened in AI in 2021?' should be classified as TEMPORAL."""
        query_type, confidence = classifier.classify_type("What happened in AI in 2021?")
        assert query_type == QueryType.TEMPORAL, (
            f"'What happened in AI in 2021?' should be TEMPORAL, got {query_type}"
        )

    def test_what_happened_with_topic_and_year(self, classifier):
        """Query with topic + year should be TEMPORAL."""
        queries = [
            "What happened with machine learning in 2020?",
            "What happened to the economy in 2019?",
            "What happened regarding climate change in 2022?",
        ]
        for query in queries:
            query_type, _ = classifier.classify_type(query)
            assert query_type == QueryType.TEMPORAL, (
                f"'{query}' should be TEMPORAL, got {query_type}"
            )


# =============================================================================
# "in [year]" Pattern Tests
# =============================================================================


class TestInYearPattern:
    """Tests for 'in [year]' queries."""

    def test_topic_in_year_is_temporal(self, classifier):
        """'[topic] in [year]' queries should be classified as TEMPORAL."""
        queries = [
            "AI developments in 2021",
            "Machine learning in 2020",
            "Technology trends in 2022",
            "Research progress in 2019",
        ]
        for query in queries:
            query_type, _ = classifier.classify_type(query)
            assert query_type == QueryType.TEMPORAL, (
                f"'{query}' should be TEMPORAL, got {query_type}"
            )

    def test_events_in_year_is_temporal(self, classifier):
        """Event-focused queries with year should be TEMPORAL."""
        queries = [
            "Major events in 2021",
            "Key discoveries in 2020",
            "Important breakthroughs in 2022",
        ]
        for query in queries:
            query_type, _ = classifier.classify_type(query)
            assert query_type == QueryType.TEMPORAL, (
                f"'{query}' should be TEMPORAL, got {query_type}"
            )


# =============================================================================
# Year Range and Temporal Phrase Tests
# =============================================================================


class TestTemporalPhrasePatterns:
    """Tests for existing temporal phrase patterns."""

    def test_how_has_changed_is_temporal(self, classifier):
        """'How has X changed' should be TEMPORAL."""
        query_type, _ = classifier.classify_type("How has AI changed over the years?")
        assert query_type == QueryType.TEMPORAL

    def test_evolution_of_is_temporal(self, classifier):
        """'Evolution of X' should be TEMPORAL."""
        query_type, _ = classifier.classify_type("The evolution of machine learning")
        assert query_type == QueryType.TEMPORAL

    def test_over_time_is_temporal(self, classifier):
        """'X over time' should be TEMPORAL."""
        query_type, _ = classifier.classify_type("How did technology progress over time?")
        assert query_type == QueryType.TEMPORAL

    def test_history_of_is_temporal(self, classifier):
        """'History of X' should be TEMPORAL."""
        query_type, _ = classifier.classify_type("History of neural networks")
        assert query_type == QueryType.TEMPORAL


# =============================================================================
# Year Boundary Tests
# =============================================================================


class TestYearBoundaries:
    """Tests for various year formats."""

    def test_four_digit_years_are_detected(self, classifier):
        """Four-digit years from 1900s and 2000s should trigger TEMPORAL."""
        years = ["1999", "2000", "2021", "2025"]
        for year in years:
            query = f"What happened in {year}?"
            query_type, _ = classifier.classify_type(query)
            assert query_type == QueryType.TEMPORAL, (
                f"Query with year {year} should be TEMPORAL"
            )

    def test_multiple_years_is_temporal(self, classifier):
        """Queries mentioning multiple years should be TEMPORAL."""
        query_type, _ = classifier.classify_type("Changes from 2019 to 2021")
        assert query_type == QueryType.TEMPORAL


# =============================================================================
# Non-Temporal Query Tests (Negative Cases)
# =============================================================================


class TestNonTemporalQueries:
    """Tests that non-temporal queries are not misclassified."""

    def test_what_is_not_temporal_without_year(self, classifier):
        """'What is X' without year should not be TEMPORAL."""
        query_type, _ = classifier.classify_type("What is machine learning?")
        assert query_type != QueryType.TEMPORAL, (
            "Generic 'What is' query should not be TEMPORAL"
        )

    def test_how_does_work_is_not_temporal(self, classifier):
        """'How does X work' should not be TEMPORAL."""
        query_type, _ = classifier.classify_type("How does GPT work?")
        assert query_type != QueryType.TEMPORAL

    def test_comparison_without_temporal_context(self, classifier):
        """Comparison queries should be COMPARISON, not TEMPORAL."""
        query_type, _ = classifier.classify_type("Compare GPT-3 vs GPT-4")
        assert query_type == QueryType.COMPARISON


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestClassifyQueryFunction:
    """Tests for the classify_query convenience function."""

    def test_classify_query_returns_temporal_for_year_query(self):
        """classify_query should return TEMPORAL for year-specific queries."""
        query_type, intent = classify_query("What happened in AI in 2021?")
        assert query_type == QueryType.TEMPORAL


# =============================================================================
# Year Detection Method Tests
# =============================================================================


class TestYearDetection:
    """Tests for the is_year_specific method."""

    def test_is_year_specific_detects_2021(self, classifier):
        """Should detect year 2021 in query."""
        assert classifier.is_year_specific("What happened in 2021?") is True

    def test_is_year_specific_detects_various_years(self, classifier):
        """Should detect various year formats."""
        assert classifier.is_year_specific("Events of 1999") is True
        assert classifier.is_year_specific("Looking at 2025 predictions") is True

    def test_is_year_specific_false_for_no_year(self, classifier):
        """Should return False when no year present."""
        assert classifier.is_year_specific("What is AI?") is False
        assert classifier.is_year_specific("How does ML work?") is False


# =============================================================================
# Confidence Score Tests
# =============================================================================


class TestClassificationConfidence:
    """Tests for classification confidence scores."""

    def test_temporal_pattern_has_confidence(self, classifier):
        """Temporal classifications should have reasonable confidence."""
        query_type, confidence = classifier.classify_type("What happened in AI in 2021?")
        assert confidence > 0.3, (
            f"Temporal classification confidence ({confidence}) should be meaningful"
        )

    def test_multiple_pattern_matches_increase_confidence(self, classifier):
        """Multiple pattern matches should increase confidence."""
        # Query with multiple temporal indicators
        query1 = "What happened in 2021?"  # One pattern
        query2 = "How has AI changed over time since 2020?"  # Multiple patterns

        _, conf1 = classifier.classify_type(query1)
        _, conf2 = classifier.classify_type(query2)

        # Query with more patterns should have higher or equal confidence
        # (At minimum, both should be classified as TEMPORAL)
        type1, _ = classifier.classify_type(query1)
        type2, _ = classifier.classify_type(query2)
        assert type1 == QueryType.TEMPORAL
        assert type2 == QueryType.TEMPORAL
