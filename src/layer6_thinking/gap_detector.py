"""
Gap Detection Module

Detects missing coverage in retrieval results.
"""

from typing import List, Optional, Set
import logging

from src.models.query import QueryPlan
from src.models.retrieval import RetrievalResult, ScoredChunk

logger = logging.getLogger(__name__)


class GapDetector:
    """
    Detects gaps in retrieval coverage.

    Identifies:
    - Missing years when year is specified
    - Missing categories when category is specified
    - Insufficient coverage for synthesis queries
    - Topic relevance gaps (year-matched but topically irrelevant)
    """

    # Semantic relevance threshold for topic relevance checks
    MIN_RELEVANCE_THRESHOLD = 0.3

    def __init__(
        self,
        available_years: List[int],
        available_categories: List[str],
        min_coverage_ratio: float = 0.3,
        min_relevance_threshold: float = None,
    ):
        """
        Initialize gap detector.

        Args:
            available_years: Years available in corpus
            available_categories: Categories available in corpus
            min_coverage_ratio: Minimum coverage ratio for synthesis
            min_relevance_threshold: Minimum semantic score for topic relevance
        """
        self.available_years = set(available_years)
        self.available_categories = set(available_categories)
        self.min_coverage_ratio = min_coverage_ratio
        self.min_relevance_threshold = min_relevance_threshold or self.MIN_RELEVANCE_THRESHOLD

    def detect_gaps(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> List[str]:
        """
        Detect coverage gaps in retrieval result.

        Args:
            result: Retrieval result
            plan: Query plan

        Returns:
            List of gap descriptions
        """
        gaps = []

        # Check year coverage
        year_gaps = self._detect_year_gaps(result, plan)
        gaps.extend(year_gaps)

        # Check category coverage
        category_gaps = self._detect_category_gaps(result, plan)
        gaps.extend(category_gaps)

        # Check synthesis coverage
        if plan.query_type.value == "synthesis":
            synthesis_gaps = self._detect_synthesis_gaps(result, plan)
            gaps.extend(synthesis_gaps)

        if gaps:
            logger.debug(f"Detected {len(gaps)} coverage gaps")

        return gaps

    def _detect_year_gaps(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> List[str]:
        """
        Detect missing year coverage and topic relevance gaps.

        CRITICAL FIX: Also checks if year-matched chunks are topically relevant.
        Having documents from the target year is not enough - they must also
        be semantically relevant to the query topic.
        """
        gaps = []

        if plan.year_filter:
            year_matched = [c for c in result.candidates if c.year_matched]
            year_matched_count = len(year_matched)

            if year_matched_count == 0:
                # Check if year exists in corpus
                if plan.year_filter in self.available_years:
                    gaps.append(
                        f"No documents from {plan.year_filter} matched the query. "
                        f"Results include documents from other years."
                    )
                else:
                    gaps.append(
                        f"Year {plan.year_filter} is not available in the corpus. "
                        f"Available years: {sorted(self.available_years)}"
                    )
            else:
                # CRITICAL FIX: Check if year-matched chunks are topically relevant
                relevant_year_matched = [
                    c for c in year_matched
                    if c.vector_score >= self.min_relevance_threshold
                ]

                if year_matched and not relevant_year_matched:
                    # Found year-matched docs but none are topically relevant
                    logger.warning(
                        f"Found {year_matched_count} documents from {plan.year_filter}, "
                        f"but none are topically relevant (vector_score < {self.min_relevance_threshold})"
                    )
                    gaps.append(
                        f"Found {year_matched_count} documents from {plan.year_filter}, "
                        f"but none appear topically relevant to the query. "
                        f"The content from {plan.year_filter} may not cover this topic."
                    )
                elif len(relevant_year_matched) < len(year_matched):
                    # Some year-matched docs are relevant, some aren't
                    irrelevant_count = year_matched_count - len(relevant_year_matched)
                    logger.debug(
                        f"{len(relevant_year_matched)} of {year_matched_count} year-matched "
                        f"chunks are topically relevant"
                    )
                    if irrelevant_count > len(relevant_year_matched):
                        gaps.append(
                            f"Only {len(relevant_year_matched)} of {year_matched_count} "
                            f"documents from {plan.year_filter} appear topically relevant."
                        )

        return gaps

    def _detect_category_gaps(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> List[str]:
        """Detect missing category coverage."""
        gaps = []

        if plan.category_filter:
            category_matched = sum(1 for c in result.candidates if c.category_matched)

            if category_matched == 0:
                if plan.category_filter in self.available_categories:
                    gaps.append(
                        f"No documents from category '{plan.category_filter}' matched. "
                        f"Results include documents from other categories."
                    )
                else:
                    gaps.append(
                        f"Category '{plan.category_filter}' not found. "
                        f"Available: {sorted(self.available_categories)}"
                    )

        return gaps

    def _detect_synthesis_gaps(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> List[str]:
        """Detect gaps for synthesis queries."""
        gaps = []

        # Check year distribution
        years_covered = set(c.year for c in result.candidates)
        year_coverage = len(years_covered) / len(self.available_years) if self.available_years else 0

        if year_coverage < self.min_coverage_ratio:
            missing_years = self.available_years - years_covered
            if missing_years:
                gaps.append(
                    f"Limited temporal coverage. Missing perspectives from years: "
                    f"{sorted(missing_years)[:5]}"
                )

        # Check category distribution
        categories_covered = set(c.category for c in result.candidates)
        category_coverage = len(categories_covered) / len(self.available_categories) if self.available_categories else 0

        if category_coverage < self.min_coverage_ratio:
            missing_cats = self.available_categories - categories_covered
            if missing_cats:
                gaps.append(
                    f"Limited category coverage. Missing: {sorted(missing_cats)[:3]}"
                )

        return gaps

    def get_missing_years(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> List[int]:
        """Get list of years not covered in results."""
        covered_years = set(c.year for c in result.candidates)

        if plan.year_filter:
            # Check if specific year is missing
            if plan.year_filter not in covered_years:
                return [plan.year_filter]

        # For synthesis, return missing years
        missing = self.available_years - covered_years
        return sorted(missing)


def create_gap_detector(
    available_years: List[int],
    available_categories: List[str],
) -> GapDetector:
    """Factory function to create gap detector."""
    return GapDetector(
        available_years=available_years,
        available_categories=available_categories,
    )
