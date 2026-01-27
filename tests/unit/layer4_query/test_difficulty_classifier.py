"""
Tests for Query Difficulty Classifier

TDD tests for Phase A: Adaptive Query Routing.
Tests classify query difficulty based on complexity_score.
"""

import pytest

from src.models.query import QueryPlan, QueryType, QueryIntent, QueryFilters, QueryExpansion


class TestDifficultyClassifier:
    """Tests for DifficultyClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create a DifficultyClassifier instance."""
        from src.layer4_query.difficulty import DifficultyClassifier
        return DifficultyClassifier()

    @pytest.fixture
    def make_plan_with_complexity(self, make_query_plan):
        """Factory for creating plans with specific complexity."""
        def _make(complexity_score: float, query_type: QueryType = QueryType.SPECIFIC) -> QueryPlan:
            plan = make_query_plan(
                query="Test query",
                query_type=query_type,
                complexity_score=complexity_score,
            )
            return plan
        return _make

    # =========================================================================
    # Easy Classification Tests (complexity < 0.3)
    # =========================================================================

    def test_classify_easy_query_low_complexity(self, classifier, make_plan_with_complexity):
        """Test that complexity_score < 0.3 returns EASY."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.1)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.EASY

    def test_classify_easy_query_mid_low_complexity(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.2 returns EASY."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.2)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.EASY

    def test_classify_easy_query_near_boundary(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.29 returns EASY."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.29)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.EASY

    # =========================================================================
    # Medium Classification Tests (0.3 <= complexity <= 0.6)
    # =========================================================================

    def test_classify_medium_query_at_lower_boundary(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.3 returns MEDIUM (boundary)."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.3)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.MEDIUM

    def test_classify_medium_query_middle(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.45 returns MEDIUM."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.45)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.MEDIUM

    def test_classify_medium_query_at_upper_boundary(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.6 returns MEDIUM (boundary)."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.6)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.MEDIUM

    # =========================================================================
    # Hard Classification Tests (complexity > 0.6)
    # =========================================================================

    def test_classify_hard_query_just_above_boundary(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.61 returns HARD."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.61)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.HARD

    def test_classify_hard_query_high_complexity(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.75 returns HARD."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.75)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.HARD

    def test_classify_hard_query_max_complexity(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 1.0 returns HARD."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(1.0)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.HARD

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_classify_zero_complexity(self, classifier, make_plan_with_complexity):
        """Test that complexity_score = 0.0 returns EASY."""
        from src.layer4_query.difficulty import QueryDifficulty

        plan = make_plan_with_complexity(0.0)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.EASY

    def test_classify_handles_query_type_factor(self, classifier, make_plan_with_complexity):
        """Test classification considers query type in addition to raw score."""
        from src.layer4_query.difficulty import QueryDifficulty

        # A SYNTHESIS query at medium complexity should still classify correctly
        plan = make_plan_with_complexity(0.5, QueryType.SYNTHESIS)
        result = classifier.classify(plan)
        assert result == QueryDifficulty.MEDIUM


class TestDifficultyFactors:
    """Tests for getting difficulty factors."""

    @pytest.fixture
    def classifier(self):
        """Create a DifficultyClassifier instance."""
        from src.layer4_query.difficulty import DifficultyClassifier
        return DifficultyClassifier()

    def test_get_difficulty_factors_returns_dict(self, classifier, make_query_plan):
        """Test that get_difficulty_factors returns a dictionary."""
        plan = make_query_plan(complexity_score=0.5)
        factors = classifier.get_difficulty_factors(plan)

        assert isinstance(factors, dict)
        assert "complexity_score" in factors

    def test_get_difficulty_factors_includes_query_type(self, classifier, make_query_plan):
        """Test that factors include query type contribution."""
        plan = make_query_plan(
            query_type=QueryType.SYNTHESIS,
            complexity_score=0.5,
        )
        factors = classifier.get_difficulty_factors(plan)

        assert "query_type_factor" in factors

    def test_get_difficulty_factors_includes_constraint_count(self, classifier, make_query_plan):
        """Test that factors include constraint count."""
        plan = make_query_plan(
            year_filter=2021,
            category_filter="ai_ml",
            complexity_score=0.5,
        )
        factors = classifier.get_difficulty_factors(plan)

        assert "constraint_count" in factors
        assert factors["constraint_count"] >= 2  # Year + category
