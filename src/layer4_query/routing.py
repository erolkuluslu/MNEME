"""
Adaptive Router Module

Routes queries to appropriate retrieval parameters based on
query type and difficulty classification.
"""

from dataclasses import dataclass
from typing import Tuple, Dict
import logging

from src.models.query import QueryPlan, QueryType
from .difficulty import DifficultyClassifier, QueryDifficulty

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """
    Routing decision for a query.

    Contains the classified difficulty and recommended retrieval parameters.
    """

    difficulty: QueryDifficulty
    min_docs: int
    max_docs: int
    year_prefilter_range: int  # 0 = no prefilter, 2 = ±2 years


class AdaptiveRouter:
    """
    Routes queries based on type and difficulty.

    Uses a routing table to determine optimal document limits
    for different query type × difficulty combinations.
    """

    # Routing table: (QueryType, QueryDifficulty) -> (min_docs, max_docs)
    ROUTING_TABLE: Dict[Tuple[QueryType, QueryDifficulty], Tuple[int, int]] = {
        # SPECIFIC queries
        (QueryType.SPECIFIC, QueryDifficulty.EASY): (3, 5),
        (QueryType.SPECIFIC, QueryDifficulty.MEDIUM): (5, 8),
        (QueryType.SPECIFIC, QueryDifficulty.HARD): (5, 10),

        # TEMPORAL queries (need more docs for time-based analysis)
        (QueryType.TEMPORAL, QueryDifficulty.EASY): (5, 8),
        (QueryType.TEMPORAL, QueryDifficulty.MEDIUM): (8, 12),
        (QueryType.TEMPORAL, QueryDifficulty.HARD): (10, 15),

        # SYNTHESIS queries (need broad coverage)
        (QueryType.SYNTHESIS, QueryDifficulty.EASY): (6, 10),
        (QueryType.SYNTHESIS, QueryDifficulty.MEDIUM): (8, 12),
        (QueryType.SYNTHESIS, QueryDifficulty.HARD): (10, 15),

        # COMPARISON queries
        (QueryType.COMPARISON, QueryDifficulty.EASY): (6, 10),
        (QueryType.COMPARISON, QueryDifficulty.MEDIUM): (8, 12),
        (QueryType.COMPARISON, QueryDifficulty.HARD): (10, 15),

        # EXPLORATORY queries
        (QueryType.EXPLORATORY, QueryDifficulty.EASY): (5, 8),
        (QueryType.EXPLORATORY, QueryDifficulty.MEDIUM): (8, 12),
        (QueryType.EXPLORATORY, QueryDifficulty.HARD): (10, 15),
    }

    # Default fallback limits
    DEFAULT_LIMITS = (5, 10)

    # Year pre-filter range when year filter is present
    YEAR_PREFILTER_RANGE = 2

    def __init__(self, classifier: DifficultyClassifier = None):
        """
        Initialize adaptive router.

        Args:
            classifier: Optional difficulty classifier (creates default if None)
        """
        self.classifier = classifier or DifficultyClassifier()

    def route(self, plan: QueryPlan) -> RoutingDecision:
        """
        Route a query plan to appropriate retrieval parameters.

        Args:
            plan: Query plan with query_type and complexity_score

        Returns:
            RoutingDecision with difficulty and document limits
        """
        # Classify difficulty
        difficulty = self.classifier.classify(plan)

        # Look up document limits
        key = (plan.query_type, difficulty)
        min_docs, max_docs = self.ROUTING_TABLE.get(key, self.DEFAULT_LIMITS)

        # Determine year pre-filter range
        if plan.filters.year_filter is not None:
            year_prefilter_range = self.YEAR_PREFILTER_RANGE
        else:
            year_prefilter_range = 0

        decision = RoutingDecision(
            difficulty=difficulty,
            min_docs=min_docs,
            max_docs=max_docs,
            year_prefilter_range=year_prefilter_range,
        )

        logger.debug(
            f"Routing decision: type={plan.query_type.value}, "
            f"difficulty={difficulty.value}, "
            f"docs={min_docs}-{max_docs}, "
            f"year_prefilter={year_prefilter_range}"
        )

        return decision

    def get_routing_table(self) -> Dict[Tuple[QueryType, QueryDifficulty], Tuple[int, int]]:
        """Return the routing table for inspection."""
        return self.ROUTING_TABLE.copy()


def create_adaptive_router(classifier: DifficultyClassifier = None) -> AdaptiveRouter:
    """Factory function to create adaptive router."""
    return AdaptiveRouter(classifier=classifier)
