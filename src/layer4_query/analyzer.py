"""
Query Analyzer Module

Main query analysis orchestrator for the MNEME system.
"""

import time
import logging
from typing import Optional

from src.config import MNEMEConfig
from src.models.query import QueryPlan, QueryType, QueryIntent, QueryFilters, QueryExpansion
from .classification import QueryClassifier
from .expansion import QueryExpander
from .filters import FilterExtractor

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyzes user queries to create execution plans.

    Combines query classification, filter extraction, and expansion
    into a complete QueryPlan for retrieval.
    """

    def __init__(
        self,
        config: Optional[MNEMEConfig] = None,
        classifier: Optional["QueryClassifier"] = None,
        expander: Optional["QueryExpander"] = None,
        filter_extractor: Optional["FilterExtractor"] = None,
    ):
        """
        Initialize query analyzer.

        Args:
            config: MNEME configuration
            classifier: Query type classifier
            expander: Query expander
            filter_extractor: Filter extractor
        """
        self.config = config or MNEMEConfig()
        self.classifier = classifier or QueryClassifier()
        self.expander = expander or QueryExpander(
            enabled=self.config.enable_query_expansion,
            max_terms=self.config.max_expansion_terms,
        )
        self.filter_extractor = filter_extractor or FilterExtractor(
            year_patterns=self.config.year_detection_patterns,
        )

    def analyze(self, query: str) -> QueryPlan:
        """
        Analyze a query and create an execution plan.

        Args:
            query: User query string

        Returns:
            QueryPlan with classification, filters, and expansion
        """
        start_time = time.time()

        logger.debug(f"Analyzing query: {query}")

        # Classify query type and intent
        query_type, type_confidence = self.classifier.classify_type(query)
        intent = self.classifier.classify_intent(query)

        # Extract filters
        filters = self.filter_extractor.extract(query)

        # For synthesis/exploratory/comparison queries, don't apply category filter
        # These queries inherently span multiple categories
        if query_type in (QueryType.SYNTHESIS, QueryType.EXPLORATORY, QueryType.COMPARISON):
            filters.category_filter = None

        # Add year expansion
        if filters.year_filter:
            filters.year_expansion = self._get_year_expansion(
                filters.year_filter,
                self.config.year_expansion_range,
            )

        # Expand query
        if self.config.enable_query_expansion:
            expansion = self.expander.expand(query)
        else:
            expansion = QueryExpansion(original_query=query)

        # Determine document limits based on query type
        min_docs, max_docs = self._get_doc_limits(query_type)

        # Calculate complexity score
        complexity = self._calculate_complexity(query, filters, query_type)

        # Build query plan
        plan = QueryPlan(
            original_query=query,
            query_type=query_type,
            intent=intent,
            filters=filters,
            expansion=expansion,
            min_docs=min_docs,
            max_docs=max_docs,
            retrieval_strategy=self.config.retrieval_strategy,
            classification_confidence=type_confidence,
            complexity_score=complexity,
            analysis_time_ms=(time.time() - start_time) * 1000,
        )

        logger.debug(
            f"Query plan: type={query_type.value}, "
            f"year={filters.year_filter}, "
            f"complexity={complexity:.2f}"
        )

        return plan

    def _get_year_expansion(self, year: int, range_size: int) -> list:
        """Get expanded year range."""
        return [y for y in range(year - range_size, year + range_size + 1) if y != year]

    def _get_doc_limits(self, query_type: QueryType) -> tuple:
        """Get min/max document limits based on query type."""
        if query_type == QueryType.SPECIFIC:
            return self.config.specific_min_docs, self.config.specific_max_docs
        elif query_type == QueryType.SYNTHESIS:
            return self.config.synthesis_min_docs, self.config.synthesis_max_docs
        elif query_type == QueryType.COMPARISON:
            return self.config.comparison_min_docs, self.config.comparison_max_docs
        elif query_type == QueryType.TEMPORAL:
            # Temporal queries need more docs to cover year ranges
            return self.config.comparison_min_docs, self.config.comparison_max_docs
        elif query_type == QueryType.EXPLORATORY:
            return self.config.synthesis_min_docs, self.config.synthesis_max_docs
        else:
            return self.config.specific_min_docs, self.config.specific_max_docs

    def _calculate_complexity(
        self,
        query: str,
        filters: QueryFilters,
        query_type: QueryType,
    ) -> float:
        """
        Calculate query complexity score (0-1).

        Factors:
        - Query length
        - Number of constraints
        - Query type complexity
        """
        score = 0.0

        # Query length factor
        words = len(query.split())
        if words > 20:
            score += 0.2
        elif words > 10:
            score += 0.1

        # Constraint factors
        if filters.year_filter:
            score += 0.15
        if filters.category_filter:
            score += 0.15
        if filters.entities:
            score += 0.1

        # Query type factor
        type_scores = {
            QueryType.SPECIFIC: 0.1,
            QueryType.EXPLORATORY: 0.2,
            QueryType.TEMPORAL: 0.25,
            QueryType.COMPARISON: 0.3,
            QueryType.SYNTHESIS: 0.35,
        }
        score += type_scores.get(query_type, 0.1)

        return min(score, 1.0)


def create_query_analyzer(config: Optional[MNEMEConfig] = None) -> QueryAnalyzer:
    """Factory function to create query analyzer."""
    return QueryAnalyzer(config=config)
