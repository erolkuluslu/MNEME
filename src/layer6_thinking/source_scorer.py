"""
Source Importance Scoring Module

Implements thinking mechanism from notebook v16 that scores and filters
sources before LLM generation based on multiple factors.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import logging
import hashlib

from src.config import MNEMEConfig
from src.models.query import QueryPlan
from src.models.retrieval import ScoredChunk

logger = logging.getLogger(__name__)


@dataclass
class ScoredSource:
    """
    A source chunk with multi-factor importance scoring.

    Extends ScoredChunk with additional scoring dimensions for
    source filtering and context optimization.
    """

    chunk: ScoredChunk

    # Component scores (0-1)
    relevance_score: float = 0.0  # From retrieval final_score
    year_match_score: float = 0.0  # 1.0 if matches, configurable otherwise
    category_match_score: float = 0.0  # 1.0 if matches, configurable otherwise
    diversity_score: float = 0.0  # Penalizes redundant sources

    # Final weighted importance
    final_importance: float = 0.0

    # Selection flag
    include_in_context: bool = True

    # Deduplication
    content_hash: str = ""

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "chunk_id": self.chunk.chunk_id,
            "doc_id": self.chunk.doc_id,
            "year": self.chunk.year,
            "category": self.chunk.category,
            "relevance_score": self.relevance_score,
            "year_match_score": self.year_match_score,
            "category_match_score": self.category_match_score,
            "diversity_score": self.diversity_score,
            "final_importance": self.final_importance,
            "include_in_context": self.include_in_context,
        }


@dataclass
class SourceScoringResult:
    """Result of source importance scoring."""

    # Scored sources (all)
    all_sources: List[ScoredSource] = field(default_factory=list)

    # Filtered sources (included in context)
    selected_sources: List[ScoredSource] = field(default_factory=list)

    # Statistics
    total_sources: int = 0
    sources_included: int = 0
    sources_filtered: int = 0
    avg_importance: float = 0.0

    # Filtering metadata
    threshold_used: float = 0.0
    max_sources: int = 0

    def get_selected_chunks(self) -> List[ScoredChunk]:
        """Get the selected chunks for context building."""
        return [s.chunk for s in self.selected_sources]

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "total_sources": self.total_sources,
            "sources_included": self.sources_included,
            "sources_filtered": self.sources_filtered,
            "avg_importance": self.avg_importance,
            "threshold_used": self.threshold_used,
            "max_sources": self.max_sources,
            "selected": [s.to_dict() for s in self.selected_sources],
        }


class SourceImportanceScorer:
    """
    Scores and filters retrieved sources based on multiple factors.

    Implements the thinking mechanism from notebook v16 that evaluates
    source relevance, year/category match, and diversity before
    including sources in the LLM context.

    Scoring factors:
    1. Relevance (from retrieval): How semantically relevant is the source?
    2. Year match: Does the source match the requested year?
    3. Category match: Does the source match the requested category?
    4. Diversity: Is the source adding new information vs. redundant?
    """

    def __init__(self, config: MNEMEConfig):
        """
        Initialize source scorer.

        Args:
            config: MNEME configuration with scoring parameters
        """
        self.config = config
        self.min_importance_threshold = config.source_importance_threshold
        self.max_sources = config.max_context_sources

        # Scoring weights
        self.relevance_weight = config.relevance_weight
        self.year_match_weight = config.year_match_weight
        self.category_match_weight = config.category_match_weight
        self.diversity_weight = config.diversity_weight

        logger.info(
            f"SourceImportanceScorer initialized: "
            f"threshold={self.min_importance_threshold}, "
            f"max_sources={self.max_sources}"
        )

    def score_and_filter(
        self,
        candidates: List[ScoredChunk],
        query_plan: QueryPlan,
    ) -> SourceScoringResult:
        """
        Score sources by multiple factors and filter by importance.

        Args:
            candidates: Retrieved chunks with scores
            query_plan: Query plan with filters

        Returns:
            SourceScoringResult with scored and filtered sources
        """
        if not candidates:
            return SourceScoringResult()

        logger.debug(f"Scoring {len(candidates)} sources...")

        # Track seen content for diversity scoring
        seen_content_hashes: Set[str] = set()
        seen_doc_ids: Set[str] = set()

        scored_sources: List[ScoredSource] = []

        for candidate in candidates:
            # Calculate component scores
            relevance = self._calculate_relevance_score(candidate)
            year_match = self._calculate_year_match_score(candidate, query_plan)
            category_match = self._calculate_category_match_score(candidate, query_plan)
            content_hash = self._compute_content_hash(candidate)
            diversity = self._calculate_diversity_score(
                candidate, content_hash, seen_content_hashes, seen_doc_ids
            )

            # Weighted combination
            final_importance = (
                relevance * self.relevance_weight +
                year_match * self.year_match_weight +
                category_match * self.category_match_weight +
                diversity * self.diversity_weight
            )

            scored_source = ScoredSource(
                chunk=candidate,
                relevance_score=relevance,
                year_match_score=year_match,
                category_match_score=category_match,
                diversity_score=diversity,
                final_importance=final_importance,
                include_in_context=final_importance >= self.min_importance_threshold,
                content_hash=content_hash,
            )

            scored_sources.append(scored_source)

            # Update seen sets for diversity tracking
            seen_content_hashes.add(content_hash)
            seen_doc_ids.add(candidate.doc_id)

        # Sort by importance
        scored_sources.sort(key=lambda s: s.final_importance, reverse=True)

        # Select top sources that pass threshold
        selected = [
            s for s in scored_sources
            if s.include_in_context
        ][:self.max_sources]

        # Mark selected sources
        selected_ids = {s.chunk.chunk_id for s in selected}
        for source in scored_sources:
            source.include_in_context = source.chunk.chunk_id in selected_ids

        # Compute statistics
        avg_importance = (
            sum(s.final_importance for s in selected) / len(selected)
            if selected else 0.0
        )

        result = SourceScoringResult(
            all_sources=scored_sources,
            selected_sources=selected,
            total_sources=len(candidates),
            sources_included=len(selected),
            sources_filtered=len(candidates) - len(selected),
            avg_importance=avg_importance,
            threshold_used=self.min_importance_threshold,
            max_sources=self.max_sources,
        )

        logger.info(
            f"Source scoring complete: {result.sources_included}/{result.total_sources} "
            f"sources selected (avg importance: {avg_importance:.3f})"
        )

        return result

    def _calculate_relevance_score(self, candidate: ScoredChunk) -> float:
        """
        Calculate relevance score from retrieval score.

        Normalizes the final_score to 0-1 range.
        """
        # final_score is typically already normalized, but clamp to be safe
        return min(max(candidate.final_score, 0.0), 1.0)

    def _calculate_year_match_score(
        self,
        candidate: ScoredChunk,
        query_plan: QueryPlan,
    ) -> float:
        """
        Calculate year match score.

        Returns:
            1.0 if year matches filter
            0.7 if within expansion range
            0.5 otherwise
        """
        if not query_plan.year_filter:
            # No year filter - all years equally valid
            return 1.0

        if candidate.year_matched:
            return 1.0

        # Check expansion range
        expansion_years = query_plan.get_year_expansion_range()
        if candidate.year in expansion_years:
            return 0.7

        # No match
        return 0.5

    def _calculate_category_match_score(
        self,
        candidate: ScoredChunk,
        query_plan: QueryPlan,
    ) -> float:
        """
        Calculate category match score.

        Returns:
            1.0 if category matches filter
            0.8 if in related categories
            0.7 otherwise
        """
        if not query_plan.category_filter:
            # No category filter - all categories equally valid
            return 1.0

        if candidate.category_matched:
            return 1.0

        # Check if in filter categories list
        if candidate.category in query_plan.filters.categories:
            return 0.8

        # No match
        return 0.7

    def _calculate_diversity_score(
        self,
        candidate: ScoredChunk,
        content_hash: str,
        seen_hashes: Set[str],
        seen_doc_ids: Set[str],
    ) -> float:
        """
        Calculate diversity score.

        Penalizes redundant sources:
        - Same content (hash match): 0.0
        - Same document, different chunk: 0.5
        - Different document: 1.0
        """
        # Exact content duplicate
        if content_hash in seen_hashes:
            return 0.0

        # Same document (but different chunk)
        if candidate.doc_id in seen_doc_ids:
            return 0.5

        # Unique source
        return 1.0

    def _compute_content_hash(self, candidate: ScoredChunk) -> str:
        """
        Compute hash of chunk content for deduplication.

        Uses first 200 chars normalized to detect near-duplicates.
        """
        text = candidate.text[:200].lower().strip()
        # Remove extra whitespace
        text = " ".join(text.split())
        return hashlib.md5(text.encode()).hexdigest()[:8]


def create_source_scorer(config: MNEMEConfig) -> SourceImportanceScorer:
    """Factory function to create source importance scorer."""
    return SourceImportanceScorer(config)
