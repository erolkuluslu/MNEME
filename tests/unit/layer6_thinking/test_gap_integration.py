"""
Tests for Gap Integration

TDD tests for Phase D: Iterative Optimization.
Tests gap-aware retrieval (IRCoT-style) when coverage gaps detected.
"""

import pytest
from typing import List

from src.models.retrieval import RetrievalResult, RetrievalConfidence
from src.config import MNEMEConfig


class TestGapEnforcer:
    """Tests for GapEnforcer class."""

    @pytest.fixture
    def enforcer(self):
        """Create a GapEnforcer instance."""
        from src.layer6_thinking.gap_enforcer import GapEnforcer
        return GapEnforcer()

    @pytest.fixture
    def config_with_iterative(self):
        """Config with iterative retrieval enabled."""
        config = MNEMEConfig.for_testing()
        config.enable_iterative_retrieval = True
        return config

    @pytest.fixture
    def config_without_iterative(self):
        """Config with iterative retrieval disabled."""
        config = MNEMEConfig.for_testing()
        config.enable_iterative_retrieval = False
        return config

    # =========================================================================
    # should_warn_about_gaps Tests
    # =========================================================================

    def test_should_warn_when_year_gap(self, enforcer):
        """Should warn when specific year gap detected."""
        gaps = ["No documents from 2021 matched."]
        assert enforcer.should_warn_about_gaps(gaps) is True

    def test_should_warn_when_missing_years_gap(self, enforcer):
        """Should warn when missing years detected."""
        gaps = ["Missing years: [2021, 2022]"]
        assert enforcer.should_warn_about_gaps(gaps) is True

    def test_no_warning_for_empty_gaps(self, enforcer):
        """No warning when gaps list is empty."""
        gaps = []
        assert enforcer.should_warn_about_gaps(gaps) is False

    def test_no_warning_for_minor_synthesis_gaps(self, enforcer):
        """No warning for minor synthesis coverage gaps."""
        gaps = ["Limited coverage. Missing: [2019]"]
        # Minor gaps shouldn't trigger warnings
        assert enforcer.should_warn_about_gaps(gaps) is False

    def test_should_warn_for_critical_category_gap(self, enforcer):
        """Should warn when critical category is missing."""
        gaps = ["No documents from category 'ai_ml' found."]
        assert enforcer.should_warn_about_gaps(gaps) is True

    # =========================================================================
    # get_gap_warning_prompt Tests
    # =========================================================================

    def test_get_gap_warning_prompt_returns_string(self, enforcer):
        """Warning prompt should be a string."""
        gaps = ["No documents from 2021 matched."]
        prompt = enforcer.get_gap_warning_prompt(gaps)
        assert isinstance(prompt, str)

    def test_get_gap_warning_prompt_contains_gap_info(self, enforcer):
        """Warning prompt should contain gap information."""
        gaps = ["No documents from 2021 matched."]
        prompt = enforcer.get_gap_warning_prompt(gaps)
        assert "2021" in prompt

    def test_get_gap_warning_prompt_empty_gaps(self, enforcer):
        """Warning prompt for empty gaps is empty."""
        gaps = []
        prompt = enforcer.get_gap_warning_prompt(gaps)
        assert prompt == "" or len(prompt) == 0

    def test_get_gap_warning_prompt_multiple_gaps(self, enforcer):
        """Warning prompt handles multiple gaps."""
        gaps = ["Missing years: [2021]", "Missing category: [nlp]"]
        prompt = enforcer.get_gap_warning_prompt(gaps)
        assert "2021" in prompt or "nlp" in prompt

    # =========================================================================
    # should_trigger_iterative_retrieval Tests
    # =========================================================================

    def test_trigger_iterative_when_enabled_and_gaps(self, enforcer, config_with_iterative):
        """Should trigger iterative retrieval when enabled and gaps exist."""
        gaps = ["Missing years: [2019, 2020]", "Missing category: [nlp]"]
        assert enforcer.should_trigger_iterative_retrieval(gaps, config_with_iterative) is True

    def test_no_trigger_when_disabled(self, enforcer, config_without_iterative):
        """Should not trigger iterative retrieval when disabled."""
        gaps = ["Missing years: [2019, 2020]", "Missing category: [nlp]"]
        assert enforcer.should_trigger_iterative_retrieval(gaps, config_without_iterative) is False

    def test_no_trigger_when_no_gaps(self, enforcer, config_with_iterative):
        """Should not trigger iterative retrieval when no gaps."""
        gaps = []
        assert enforcer.should_trigger_iterative_retrieval(gaps, config_with_iterative) is False

    def test_no_trigger_for_single_minor_gap(self, enforcer, config_with_iterative):
        """Should not trigger for single minor gap."""
        gaps = ["Limited coverage."]
        assert enforcer.should_trigger_iterative_retrieval(gaps, config_with_iterative) is False

    def test_trigger_for_synthesis_with_multiple_gaps(self, enforcer, config_with_iterative):
        """Should trigger for synthesis queries with multiple significant gaps."""
        gaps = ["Missing years: [2019, 2020, 2021]", "Missing categories: [nlp, cv]"]
        assert enforcer.should_trigger_iterative_retrieval(gaps, config_with_iterative) is True


class TestGapEnforcerIntegration:
    """Integration tests for GapEnforcer with retrieval results."""

    @pytest.fixture
    def enforcer(self):
        """Create a GapEnforcer instance."""
        from src.layer6_thinking.gap_enforcer import GapEnforcer
        return GapEnforcer()

    @pytest.fixture
    def result_with_gaps(self, make_retrieval_result) -> RetrievalResult:
        """Retrieval result with coverage gaps."""
        result = make_retrieval_result(year_filter=2021)
        result.coverage_gaps = [
            "No documents from 2021 matched.",
            "Missing category: [nlp]",
        ]
        result.missing_years = [2021]
        return result

    @pytest.fixture
    def result_without_gaps(self, make_retrieval_result) -> RetrievalResult:
        """Retrieval result without coverage gaps."""
        result = make_retrieval_result()
        result.coverage_gaps = []
        result.missing_years = []
        return result

    def test_analyze_result_with_gaps(self, enforcer, result_with_gaps):
        """Analyze retrieval result with gaps."""
        analysis = enforcer.analyze_result(result_with_gaps)

        assert "has_critical_gaps" in analysis
        assert "gap_summary" in analysis
        assert analysis["has_critical_gaps"] is True

    def test_analyze_result_without_gaps(self, enforcer, result_without_gaps):
        """Analyze retrieval result without gaps."""
        analysis = enforcer.analyze_result(result_without_gaps)

        assert analysis["has_critical_gaps"] is False

    def test_get_iterative_suggestions(self, enforcer, result_with_gaps):
        """Get suggestions for iterative retrieval."""
        suggestions = enforcer.get_iterative_suggestions(result_with_gaps)

        assert isinstance(suggestions, list)
        # Should suggest expanding year range or relaxing filters


class TestGapClassification:
    """Tests for gap classification and severity."""

    @pytest.fixture
    def enforcer(self):
        """Create a GapEnforcer instance."""
        from src.layer6_thinking.gap_enforcer import GapEnforcer
        return GapEnforcer()

    def test_classify_year_gap_as_critical(self, enforcer):
        """Year gaps are classified as critical."""
        gap = "No documents from 2021 matched."
        severity = enforcer.classify_gap_severity(gap)
        assert severity == "critical" or severity == "high"

    def test_classify_category_gap_as_significant(self, enforcer):
        """Category gaps are classified as significant."""
        gap = "No documents from category 'ai_ml' found."
        severity = enforcer.classify_gap_severity(gap)
        assert severity in ["critical", "high", "significant"]

    def test_classify_coverage_gap_as_minor(self, enforcer):
        """General coverage gaps are classified as minor."""
        gap = "Limited coverage."
        severity = enforcer.classify_gap_severity(gap)
        assert severity in ["minor", "low"]
