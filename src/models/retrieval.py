"""
Retrieval Data Models

Models for retrieval results, scoring, and confidence.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .chunk import Chunk


class RetrievalConfidence(str, Enum):
    """
    Confidence levels for retrieval results.

    CRITICAL FIX: Content-based confidence, not just score-based.
    """

    # High confidence: year-matched documents found
    YEAR_MATCHED = "year_matched"

    # Good confidence: relevant documents found, but no year match
    GOOD_MATCH = "good_match"

    # Partial match: some relevant documents, mixed years
    PARTIAL_MATCH = "partial_match"

    # Low confidence: few relevant documents
    LOW_MATCH = "low_match"

    # No results: no relevant documents found
    NO_RESULTS = "no_results"


@dataclass
class ScoredChunk:
    """A chunk with retrieval scores."""

    chunk: "Chunk"

    # Individual scores
    vector_score: float = 0.0
    bm25_score: float = 0.0

    # Combined score (after RRF or other fusion)
    combined_score: float = 0.0

    # Blended score (weighted dense + sparse, before boosting)
    blended_score: float = 0.0

    # Boosted score (after year/category boosting)
    final_score: float = 0.0

    # Score components
    year_boost: float = 0.0
    category_boost: float = 0.0

    # Matching flags
    year_matched: bool = False
    category_matched: bool = False

    # Rank in retrieval
    rank: int = 0

    @property
    def chunk_id(self) -> str:
        """Convenience accessor for chunk_id."""
        return self.chunk.chunk_id

    @property
    def doc_id(self) -> str:
        """Convenience accessor for doc_id."""
        return self.chunk.doc_id

    @property
    def year(self) -> int:
        """Convenience accessor for year."""
        return self.chunk.year

    @property
    def category(self) -> str:
        """Convenience accessor for category."""
        return self.chunk.category

    @property
    def text(self) -> str:
        """Convenience accessor for text."""
        return self.chunk.text

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "year": self.year,
            "category": self.category,
            "vector_score": self.vector_score,
            "bm25_score": self.bm25_score,
            "combined_score": self.combined_score,
            "blended_score": self.blended_score,
            "final_score": self.final_score,
            "year_boost": self.year_boost,
            "category_boost": self.category_boost,
            "year_matched": self.year_matched,
            "category_matched": self.category_matched,
            "rank": self.rank,
        }


@dataclass
class RetrievalResult:
    """
    Complete retrieval result with scored candidates.

    Contains both the results and metadata about the retrieval process.
    """

    # Scored chunks (ordered by final_score)
    candidates: List[ScoredChunk] = field(default_factory=list)

    # Retrieval metadata
    query: str = ""
    retrieval_strategy: str = "hybrid_rrf"
    total_candidates_considered: int = 0
    retrieval_time_ms: float = 0.0

    # Query filters applied
    year_filter: Optional[int] = None
    category_filter: Optional[str] = None

    # Confidence assessment
    confidence: RetrievalConfidence = RetrievalConfidence.NO_RESULTS

    # Gap detection
    coverage_gaps: List[str] = field(default_factory=list)
    missing_years: List[int] = field(default_factory=list)

    @property
    def top_candidate(self) -> Optional[ScoredChunk]:
        """Get the top-ranked candidate."""
        return self.candidates[0] if self.candidates else None

    @property
    def num_results(self) -> int:
        """Number of results returned."""
        return len(self.candidates)

    @property
    def num_year_matched(self) -> int:
        """Number of results matching year filter."""
        return sum(1 for c in self.candidates if c.year_matched)

    @property
    def num_category_matched(self) -> int:
        """Number of results matching category filter."""
        return sum(1 for c in self.candidates if c.category_matched)

    @property
    def years_represented(self) -> List[int]:
        """List of years in results."""
        return sorted(set(c.year for c in self.candidates))

    @property
    def categories_represented(self) -> List[str]:
        """List of categories in results."""
        return sorted(set(c.category for c in self.candidates))

    def get_year_matched_chunks(self) -> List[ScoredChunk]:
        """Get only year-matched chunks."""
        return [c for c in self.candidates if c.year_matched]

    def get_top_k(self, k: int) -> List[ScoredChunk]:
        """Get top-k results."""
        return self.candidates[:k]

    def filter_by_threshold(self, min_score: float) -> "RetrievalResult":
        """Filter results by minimum score."""
        filtered = [c for c in self.candidates if c.final_score >= min_score]
        return RetrievalResult(
            candidates=filtered,
            query=self.query,
            retrieval_strategy=self.retrieval_strategy,
            total_candidates_considered=self.total_candidates_considered,
            retrieval_time_ms=self.retrieval_time_ms,
            year_filter=self.year_filter,
            category_filter=self.category_filter,
            confidence=self.confidence,
            coverage_gaps=self.coverage_gaps,
            missing_years=self.missing_years,
        )

    def get_context_text(self, separator: str = "\n\n---\n\n") -> str:
        """Get concatenated text from all candidates for LLM context."""
        return separator.join(c.text for c in self.candidates)

    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        scores = [c.final_score for c in self.candidates]
        return {
            "num_results": self.num_results,
            "num_year_matched": self.num_year_matched,
            "num_category_matched": self.num_category_matched,
            "years_represented": self.years_represented,
            "categories_represented": self.categories_represented,
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "confidence": self.confidence.value,
            "retrieval_time_ms": self.retrieval_time_ms,
            "coverage_gaps": self.coverage_gaps,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "candidates": [c.to_dict() for c in self.candidates],
            "query": self.query,
            "retrieval_strategy": self.retrieval_strategy,
            "total_candidates_considered": self.total_candidates_considered,
            "retrieval_time_ms": self.retrieval_time_ms,
            "year_filter": self.year_filter,
            "category_filter": self.category_filter,
            "confidence": self.confidence.value,
            "coverage_gaps": self.coverage_gaps,
            "missing_years": self.missing_years,
            "stats": self.get_stats(),
        }


@dataclass
class RetrievalMetrics:
    """Metrics for evaluating retrieval quality."""

    # Precision and recall
    precision_at_k: Dict[int, float] = field(default_factory=dict)
    recall_at_k: Dict[int, float] = field(default_factory=dict)

    # Ranking metrics
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg: float = 0.0  # Normalized Discounted Cumulative Gain
    map_score: float = 0.0  # Mean Average Precision

    # Year-specific metrics
    year_accuracy: float = 0.0  # Fraction with correct year
    year_coverage: float = 0.0  # Coverage of requested year

    # Timing
    avg_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "mrr": self.mrr,
            "ndcg": self.ndcg,
            "map_score": self.map_score,
            "year_accuracy": self.year_accuracy,
            "year_coverage": self.year_coverage,
            "avg_latency_ms": self.avg_latency_ms,
        }
