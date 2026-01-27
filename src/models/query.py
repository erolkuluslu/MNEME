"""
Query Data Models

Models for query analysis, classification, and planning.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set


class QueryType(str, Enum):
    """Classification of query types for retrieval strategy selection."""

    # Specific queries: focus on particular entities/concepts
    SPECIFIC = "specific"

    # Synthesis queries: combine information across sources
    SYNTHESIS = "synthesis"

    # Comparison queries: compare/contrast entities
    COMPARISON = "comparison"

    # Temporal queries: time-based analysis
    TEMPORAL = "temporal"

    # Exploratory queries: broad topic exploration
    EXPLORATORY = "exploratory"


class QueryIntent(str, Enum):
    """Intent classification for answer generation."""

    FACTUAL = "factual"  # Looking for specific facts
    EXPLANATORY = "explanatory"  # Want explanation/understanding
    EVALUATIVE = "evaluative"  # Seeking evaluation/opinion
    PROCEDURAL = "procedural"  # How-to questions
    COMPARATIVE = "comparative"  # Comparing entities


@dataclass
class QueryFilters:
    """Extracted filters from query analysis."""

    # Temporal filters
    year_filter: Optional[int] = None
    year_range: Optional[tuple] = None  # (start_year, end_year)
    year_expansion: List[int] = field(default_factory=list)  # Related years

    # Category filters
    category_filter: Optional[str] = None
    categories: List[str] = field(default_factory=list)

    # Entity filters
    entities: List[str] = field(default_factory=list)

    # Boolean flags
    require_year_match: bool = False
    require_category_match: bool = False

    def has_temporal_constraint(self) -> bool:
        """Check if query has temporal constraints."""
        return self.year_filter is not None or self.year_range is not None

    def has_category_constraint(self) -> bool:
        """Check if query has category constraints."""
        return self.category_filter is not None or len(self.categories) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize filters to dictionary."""
        return {
            "year_filter": self.year_filter,
            "year_range": self.year_range,
            "year_expansion": self.year_expansion,
            "category_filter": self.category_filter,
            "categories": self.categories,
            "entities": self.entities,
            "require_year_match": self.require_year_match,
            "require_category_match": self.require_category_match,
        }


@dataclass
class QueryExpansion:
    """Expanded query terms for improved retrieval."""

    original_query: str
    expanded_terms: List[str] = field(default_factory=list)
    synonyms: Dict[str, List[str]] = field(default_factory=dict)
    related_concepts: List[str] = field(default_factory=list)

    def get_all_terms(self) -> List[str]:
        """Get all search terms (original + expansions)."""
        terms = [self.original_query] + self.expanded_terms + self.related_concepts
        for synonym_list in self.synonyms.values():
            terms.extend(synonym_list)
        return list(set(terms))

    def get_expanded_query(self) -> str:
        """Get expanded query string."""
        all_terms = self.get_all_terms()
        return " ".join(all_terms)


@dataclass
class QueryPlan:
    """
    Complete query plan for retrieval and generation.

    Combines query analysis, filters, expansion, and strategy selection.
    """

    # Original query
    original_query: str

    # Classification
    query_type: QueryType
    intent: QueryIntent

    # Filters and expansion
    filters: QueryFilters
    expansion: QueryExpansion

    # Retrieval parameters
    min_docs: int = 5
    max_docs: int = 10
    retrieval_strategy: str = "hybrid_rrf"

    # Confidence and scores
    classification_confidence: float = 0.0
    complexity_score: float = 0.0

    # Processing metadata
    analysis_time_ms: float = 0.0

    @property
    def year_filter(self) -> Optional[int]:
        """Convenience accessor for year filter."""
        return self.filters.year_filter

    @property
    def category_filter(self) -> Optional[str]:
        """Convenience accessor for category filter."""
        return self.filters.category_filter

    @property
    def has_temporal_focus(self) -> bool:
        """Check if query has temporal focus."""
        return self.filters.has_temporal_constraint()

    @property
    def has_category_focus(self) -> bool:
        """Check if query has category focus."""
        return self.filters.has_category_constraint()

    def get_search_terms(self) -> List[str]:
        """Get all search terms for retrieval."""
        return self.expansion.get_all_terms()

    def get_year_expansion_range(self) -> List[int]:
        """Get years to consider for retrieval."""
        years = []
        if self.filters.year_filter:
            years.append(self.filters.year_filter)
        years.extend(self.filters.year_expansion)
        return sorted(set(years))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize query plan to dictionary."""
        return {
            "original_query": self.original_query,
            "query_type": self.query_type.value,
            "intent": self.intent.value,
            "filters": self.filters.to_dict(),
            "expansion": {
                "original_query": self.expansion.original_query,
                "expanded_terms": self.expansion.expanded_terms,
                "synonyms": self.expansion.synonyms,
                "related_concepts": self.expansion.related_concepts,
            },
            "min_docs": self.min_docs,
            "max_docs": self.max_docs,
            "retrieval_strategy": self.retrieval_strategy,
            "classification_confidence": self.classification_confidence,
            "complexity_score": self.complexity_score,
            "analysis_time_ms": self.analysis_time_ms,
        }

    @classmethod
    def simple(cls, query: str, query_type: QueryType = QueryType.SPECIFIC) -> "QueryPlan":
        """Create a simple query plan without analysis."""
        return cls(
            original_query=query,
            query_type=query_type,
            intent=QueryIntent.FACTUAL,
            filters=QueryFilters(),
            expansion=QueryExpansion(original_query=query),
        )

    def __repr__(self) -> str:
        return (
            f"QueryPlan(type={self.query_type.value}, "
            f"year={self.year_filter}, "
            f"category={self.category_filter})"
        )
