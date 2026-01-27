"""
Confidence Assessment Module

CRITICAL FIX: Content-based confidence scoring.
"""

from typing import Optional, List
import logging

from src.models.retrieval import RetrievalConfidence, ScoredChunk

logger = logging.getLogger(__name__)


class ConfidenceAssessor:
    """
    Assesses confidence based on retrieval content.

    CRITICAL FIX: Uses content-based confidence rather than
    score-based. Key insight: if we have year-matched documents,
    we should report high confidence regardless of similarity scores.
    """

    def __init__(
        self,
        min_year_matched_for_high: int = 1,
        min_results_for_good: int = 3,
    ):
        """
        Initialize confidence assessor.

        Args:
            min_year_matched_for_high: Min year-matched for high confidence
            min_results_for_good: Min results for good confidence
        """
        self.min_year_matched_for_high = min_year_matched_for_high
        self.min_results_for_good = min_results_for_good

    def assess(
        self,
        candidates: List[ScoredChunk],
        year_filter: Optional[int],
    ) -> RetrievalConfidence:
        """
        Assess retrieval confidence.

        CRITICAL FIX: Year-filter-aware content-based logic:
        1. If year filter is set AND we have year-matched docs → YEAR_MATCHED
        2. If year filter is set BUT no matches → PARTIAL_MATCH (not GOOD_MATCH!)
        3. If no year filter → standard count-based confidence

        Args:
            candidates: Retrieved chunks
            year_filter: Requested year

        Returns:
            RetrievalConfidence level
        """
        if not candidates:
            return RetrievalConfidence.NO_RESULTS

        year_matched_count = sum(1 for c in candidates if c.year_matched)
        total_count = len(candidates)

        # Case 1: Year filter was set
        if year_filter is not None:
            if year_matched_count >= self.min_year_matched_for_high:
                logger.debug(
                    f"YEAR_MATCHED: {year_matched_count} docs from {year_filter}"
                )
                return RetrievalConfidence.YEAR_MATCHED
            else:
                # Year filter was set but no/insufficient matches found
                logger.debug(
                    f"PARTIAL_MATCH: Year {year_filter} requested, "
                    f"only {year_matched_count} matched, {total_count} total"
                )
                return RetrievalConfidence.PARTIAL_MATCH

        # Case 2: No year filter - standard count-based confidence
        if total_count >= self.min_results_for_good:
            return RetrievalConfidence.GOOD_MATCH

        return RetrievalConfidence.LOW_MATCH

    def get_confidence_message(
        self,
        confidence: RetrievalConfidence,
        year_filter: Optional[int],
        year_matched_count: int,
    ) -> str:
        """
        Generate human-readable confidence message.

        Args:
            confidence: Confidence level
            year_filter: Requested year
            year_matched_count: Number of year-matched docs

        Returns:
            Confidence message string
        """
        if confidence == RetrievalConfidence.YEAR_MATCHED:
            return (
                f"High confidence: {year_matched_count} source(s) "
                f"from {year_filter} found."
            )

        elif confidence == RetrievalConfidence.GOOD_MATCH:
            return "Good confidence: Relevant sources found."

        elif confidence == RetrievalConfidence.PARTIAL_MATCH:
            return (
                f"Partial match: No sources from {year_filter} found. "
                f"Results include other years."
            )

        elif confidence == RetrievalConfidence.LOW_MATCH:
            return "Low confidence: Limited relevant sources found."

        else:
            return "No relevant sources found for this query."


def determine_confidence(
    year_matched_count: int,
    year_filter: Optional[int],
    other_year_count: int,
) -> RetrievalConfidence:
    """
    Convenience function for confidence determination.

    CRITICAL FIX: Year-filter-aware content-based logic.
    Key insight: GOOD_MATCH should ONLY be returned when no year filter was set.
    If a year filter was set but not satisfied, it's PARTIAL_MATCH at best.

    Args:
        year_matched_count: Docs matching requested year
        year_filter: Requested year (or None)
        other_year_count: Docs from other years

    Returns:
        RetrievalConfidence
    """
    # Case 1: Year filter was set
    if year_filter is not None:
        if year_matched_count >= 1:
            # We have documents from the requested year
            logger.debug(f"YEAR_MATCHED: {year_matched_count} docs from {year_filter}")
            return RetrievalConfidence.YEAR_MATCHED
        elif other_year_count > 0:
            # Year filter was set but NO documents match - only other years available
            logger.debug(
                f"PARTIAL_MATCH: Year {year_filter} requested, 0 matched, "
                f"{other_year_count} from other years"
            )
            return RetrievalConfidence.PARTIAL_MATCH
        else:
            # No results at all
            return RetrievalConfidence.NO_RESULTS

    # Case 2: No year filter was set - standard confidence scoring
    total_count = year_matched_count + other_year_count
    if total_count >= 3:
        return RetrievalConfidence.GOOD_MATCH
    elif total_count > 0:
        return RetrievalConfidence.LOW_MATCH
    else:
        return RetrievalConfidence.NO_RESULTS
