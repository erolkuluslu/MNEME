"""
Query Difficulty Classifier

Classifies query difficulty based on complexity score for adaptive routing.
"""

from enum import Enum
from typing import Dict
import logging

from src.models.query import QueryPlan, QueryType

logger = logging.getLogger(__name__)


class QueryDifficulty(str, Enum):
    """Classification of query difficulty for routing decisions."""

    EASY = "easy"      # complexity_score < 0.3
    MEDIUM = "medium"  # complexity_score 0.3-0.6
    HARD = "hard"      # complexity_score > 0.6


class DifficultyClassifier:
    """
    Classifies query difficulty based on complexity score.

    Difficulty Thresholds:
    - EASY: complexity_score < 0.3
    - MEDIUM: 0.3 <= complexity_score <= 0.6
    - HARD: complexity_score > 0.6
    """

    # Difficulty thresholds
    EASY_THRESHOLD = 0.3
    HARD_THRESHOLD = 0.6

    # Query type complexity factors
    QUERY_TYPE_FACTORS = {
        QueryType.SPECIFIC: 0.0,
        QueryType.EXPLORATORY: 0.1,
        QueryType.TEMPORAL: 0.15,
        QueryType.COMPARISON: 0.2,
        QueryType.SYNTHESIS: 0.25,
    }

    def classify(self, plan: QueryPlan) -> QueryDifficulty:
        """
        Classify query difficulty based on complexity score.

        Args:
            plan: Query plan with complexity_score computed

        Returns:
            QueryDifficulty enum (EASY, MEDIUM, or HARD)
        """
        complexity = plan.complexity_score

        if complexity < self.EASY_THRESHOLD:
            difficulty = QueryDifficulty.EASY
        elif complexity <= self.HARD_THRESHOLD:
            difficulty = QueryDifficulty.MEDIUM
        else:
            difficulty = QueryDifficulty.HARD

        logger.debug(
            f"Classified query difficulty: {difficulty.value} "
            f"(complexity={complexity:.2f})"
        )

        return difficulty

    def get_difficulty_factors(self, plan: QueryPlan) -> Dict[str, float]:
        """
        Get the contributing factors to difficulty classification.

        Useful for debugging and transparency.

        Args:
            plan: Query plan to analyze

        Returns:
            Dictionary of factor names to their values
        """
        factors = {
            "complexity_score": plan.complexity_score,
            "query_type_factor": self.QUERY_TYPE_FACTORS.get(plan.query_type, 0.0),
            "constraint_count": self._count_constraints(plan),
            "has_year_filter": 1.0 if plan.year_filter else 0.0,
            "has_category_filter": 1.0 if plan.category_filter else 0.0,
        }

        # Add query length factor
        query_words = len(plan.original_query.split())
        if query_words > 20:
            factors["query_length_factor"] = 0.2
        elif query_words > 10:
            factors["query_length_factor"] = 0.1
        else:
            factors["query_length_factor"] = 0.0

        return factors

    def _count_constraints(self, plan: QueryPlan) -> int:
        """Count the number of constraints in the query plan."""
        count = 0

        if plan.filters.year_filter:
            count += 1
        if plan.filters.year_range:
            count += 1
        if plan.filters.category_filter:
            count += 1
        if plan.filters.categories:
            count += len(plan.filters.categories)
        if plan.filters.entities:
            count += len(plan.filters.entities)

        return count


def create_difficulty_classifier() -> DifficultyClassifier:
    """Factory function to create difficulty classifier."""
    return DifficultyClassifier()
