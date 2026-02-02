"""
Community-Aware Retrieval Strategy

Enhanced retrieval for narrative/exploratory queries that leverages
community structure and summaries for better context.
"""

import time
from typing import List, Dict, Optional, Set
import logging
import numpy as np

from .base import BaseRetrievalStrategy
from .hybrid_rrf import HybridRRFStrategy
from src.models.chunk import Chunk
from src.models.query import QueryPlan, QueryType, QueryIntent
from src.models.retrieval import RetrievalResult, ScoredChunk, RetrievalConfidence
from src.models.graph import KnowledgeStructures, Community
from src.layer2_graph.similarity.base import BaseSimilarityEngine

logger = logging.getLogger(__name__)

# Keywords that indicate narrative/exploratory queries
NARRATIVE_KEYWORDS = [
    'overview', 'summarize', 'describe', 'explain', 'who am i',
    'what do i know', 'tell me about', 'bird', 'big picture',
    'across', 'themes', 'patterns', 'synthesis', 'comprehensive',
]


class CommunityAwareRetrievalResult(RetrievalResult):
    """Extended retrieval result with community summaries."""

    def __init__(
        self,
        *args,
        community_summaries: Optional[Dict[int, str]] = None,
        expanded_from_communities: Optional[List[int]] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.community_summaries = community_summaries or {}
        self.expanded_from_communities = expanded_from_communities or []

    @classmethod
    def from_retrieval_result(
        cls,
        result: RetrievalResult,
        community_summaries: Optional[Dict[int, str]] = None,
        expanded_from_communities: Optional[List[int]] = None,
    ) -> "CommunityAwareRetrievalResult":
        """Create from a standard RetrievalResult."""
        return cls(
            candidates=result.candidates,
            query=result.query,
            retrieval_strategy=result.retrieval_strategy,
            total_candidates_considered=result.total_candidates_considered,
            retrieval_time_ms=result.retrieval_time_ms,
            year_filter=result.year_filter,
            category_filter=result.category_filter,
            confidence=result.confidence,
            coverage_gaps=result.coverage_gaps,
            missing_years=result.missing_years,
            community_summaries=community_summaries,
            expanded_from_communities=expanded_from_communities,
        )


class CommunityAwareStrategy(BaseRetrievalStrategy):
    """
    Enhanced retrieval for narrative/exploratory queries.

    Only activates for SYNTHESIS/EXPLORATORY query types or when query
    contains narrative keywords. For factual/specific queries, falls
    back to standard HybridRRF.

    Key features:
    - Expands retrieval with community context
    - Includes community summaries for bird's-eye view
    - Boosts bridge nodes for cross-topic connections
    """

    def __init__(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
        embedding_engine,
        similarity_engine: BaseSimilarityEngine,
        knowledge_structures: Optional[KnowledgeStructures] = None,
        hybrid_strategy: Optional[HybridRRFStrategy] = None,
        community_boost: float = 0.3,
        bridge_boost: float = 0.4,
        **hybrid_kwargs,
    ):
        """
        Initialize community-aware retrieval strategy.

        Args:
            chunks: All chunks
            embeddings: Embedding matrix
            embedding_engine: Engine for query encoding
            similarity_engine: Vector similarity engine
            knowledge_structures: Pre-computed community structures
            hybrid_strategy: Existing HybridRRF strategy to wrap
            community_boost: Score boost for same-community chunks
            bridge_boost: Score boost for bridge nodes
            **hybrid_kwargs: Arguments passed to HybridRRFStrategy
        """
        super().__init__(chunks, embeddings)

        self.embedding_engine = embedding_engine
        self.similarity_engine = similarity_engine
        self.knowledge_structures = knowledge_structures
        self.community_boost = community_boost
        self.bridge_boost = bridge_boost

        # Use provided strategy or create new one
        self.hybrid_strategy = hybrid_strategy or HybridRRFStrategy(
            chunks=chunks,
            embeddings=embeddings,
            embedding_engine=embedding_engine,
            similarity_engine=similarity_engine,
            **hybrid_kwargs,
        )

        # Build quick lookup structures
        self._build_lookups()

    def _build_lookups(self):
        """Build lookup structures for fast community access."""
        self._chunk_to_community: Dict[str, int] = {}
        self._bridge_ids: Set[str] = set()
        self._hub_ids: Set[str] = set()

        if self.knowledge_structures:
            self._chunk_to_community = self.knowledge_structures.chunk_to_community
            self._bridge_ids = set(self.knowledge_structures.get_bridge_ids())
            self._hub_ids = set(self.knowledge_structures.get_hub_ids())

    def retrieve(
        self,
        query: str,
        plan: QueryPlan,
        top_k: int,
    ) -> RetrievalResult:
        """
        Retrieve using community-aware strategy.

        For factual queries: standard HybridRRF
        For narrative queries: expanded retrieval with community context

        Args:
            query: Query string
            plan: Query plan
            top_k: Maximum results

        Returns:
            RetrievalResult (or CommunityAwareRetrievalResult for narrative)
        """
        start_time = time.time()

        # Check if this is a narrative query
        if not self._is_narrative_query(plan, query):
            logger.debug("Non-narrative query, using standard hybrid strategy")
            return self.hybrid_strategy.retrieve(query, plan, top_k)

        logger.debug("Narrative query detected, using community-aware retrieval")

        # Get base results with expanded pool
        base_result = self.hybrid_strategy.retrieve(query, plan, top_k * 2)

        # Expand with community context
        expanded_candidates, expanded_communities = self._expand_with_communities(
            base_result.candidates, top_k
        )

        # Apply community and bridge boosting
        boosted_candidates = self._apply_structure_boosting(expanded_candidates)

        # Get relevant community summaries
        summaries = self._get_relevant_summaries(expanded_communities)

        # Limit to top_k
        final_candidates = boosted_candidates[:top_k]

        # Assign ranks
        for i, chunk in enumerate(final_candidates):
            chunk.rank = i + 1

        retrieval_time = (time.time() - start_time) * 1000

        # Create enhanced result
        return CommunityAwareRetrievalResult.from_retrieval_result(
            RetrievalResult(
                candidates=final_candidates,
                query=query,
                retrieval_strategy="community_aware",
                total_candidates_considered=base_result.total_candidates_considered,
                retrieval_time_ms=retrieval_time,
                year_filter=plan.year_filter,
                category_filter=plan.category_filter,
                confidence=self._determine_confidence(final_candidates, plan, summaries),
            ),
            community_summaries=summaries,
            expanded_from_communities=list(expanded_communities),
        )

    def _is_narrative_query(self, plan: QueryPlan, query: str) -> bool:
        """
        Determine if query is narrative/exploratory.

        Narrative queries benefit from community context and summaries.
        Factual queries should use standard retrieval for precision.

        Args:
            plan: Query plan with type/intent
            query: Original query string

        Returns:
            True if narrative query
        """
        # Check query type
        # COMPARISON queries benefit from community summaries for year-range comparisons
        NARRATIVE_TYPES = {QueryType.SYNTHESIS, QueryType.EXPLORATORY, QueryType.COMPARISON}
        if plan.query_type in NARRATIVE_TYPES:
            return True

        # Check intent
        if plan.intent == QueryIntent.EXPLANATORY:
            return True

        # Check for narrative keywords
        query_lower = query.lower()
        return any(kw in query_lower for kw in NARRATIVE_KEYWORDS)

    def _expand_with_communities(
        self,
        candidates: List[ScoredChunk],
        target_count: int,
    ) -> tuple:
        """
        Expand candidates with chunks from same communities.

        Args:
            candidates: Initial candidates
            target_count: Target number of candidates

        Returns:
            Tuple of (expanded_candidates, community_ids)
        """
        if not self.knowledge_structures or not candidates:
            return candidates, set()

        # Find communities represented in top results
        top_communities: Set[int] = set()
        for scored_chunk in candidates[:5]:  # Top 5 results
            chunk_id = scored_chunk.chunk_id
            if chunk_id in self._chunk_to_community:
                top_communities.add(self._chunk_to_community[chunk_id])

        if not top_communities:
            return candidates, set()

        # Get existing chunk IDs
        existing_ids = {c.chunk_id for c in candidates}

        # Find additional chunks from these communities
        additional_chunks = []
        for community in self.knowledge_structures.communities:
            if community.community_id not in top_communities:
                continue

            for chunk_id in community.member_ids:
                if chunk_id in existing_ids:
                    continue

                chunk = self.get_chunk(chunk_id)
                if chunk:
                    # Create scored chunk with community membership boost
                    scored = ScoredChunk(
                        chunk=chunk,
                        vector_score=0.0,
                        bm25_score=0.0,
                        combined_score=0.0,
                        final_score=self.community_boost,  # Base community boost
                        year_matched=False,
                        category_matched=False,
                    )
                    additional_chunks.append(scored)
                    existing_ids.add(chunk_id)

        # Combine and limit
        all_candidates = list(candidates) + additional_chunks
        all_candidates.sort(key=lambda x: x.final_score, reverse=True)

        return all_candidates[:target_count * 2], top_communities

    def _apply_structure_boosting(
        self,
        candidates: List[ScoredChunk],
    ) -> List[ScoredChunk]:
        """
        Apply boosting based on graph structure.

        Boosts:
        - Bridge nodes: cross-community connectors
        - Hub nodes: central knowledge points

        Args:
            candidates: Candidates to boost

        Returns:
            Boosted candidates sorted by score
        """
        for scored_chunk in candidates:
            chunk_id = scored_chunk.chunk_id

            # Boost bridges
            if chunk_id in self._bridge_ids:
                scored_chunk.final_score *= (1 + self.bridge_boost)
                logger.debug(f"Bridge boost applied to {chunk_id}")

            # Slight boost for hubs (less than bridges)
            elif chunk_id in self._hub_ids:
                scored_chunk.final_score *= (1 + self.community_boost * 0.5)

        # Re-sort by boosted scores
        candidates.sort(key=lambda x: x.final_score, reverse=True)
        return candidates

    def _get_relevant_summaries(
        self,
        community_ids: Set[int],
    ) -> Dict[int, str]:
        """
        Get summaries for relevant communities.

        Args:
            community_ids: IDs of communities to include

        Returns:
            Dict mapping community_id -> summary
        """
        if not self.knowledge_structures:
            return {}

        summaries = {}
        for community in self.knowledge_structures.communities:
            if community.community_id in community_ids and community.summary:
                summaries[community.community_id] = community.summary

        return summaries

    def _determine_confidence(
        self,
        candidates: List[ScoredChunk],
        plan: QueryPlan,
        summaries: Dict[int, str],
    ) -> RetrievalConfidence:
        """Determine retrieval confidence for narrative query."""
        if not candidates:
            return RetrievalConfidence.NO_RESULTS

        # For narrative queries, having summaries is a good sign
        if summaries:
            return RetrievalConfidence.GOOD_MATCH

        # Fall back to standard confidence
        if len(candidates) >= 3:
            return RetrievalConfidence.GOOD_MATCH
        elif len(candidates) > 0:
            return RetrievalConfidence.PARTIAL_MATCH
        else:
            return RetrievalConfidence.NO_RESULTS


def create_community_aware_strategy(
    chunks: List[Chunk],
    embeddings: np.ndarray,
    embedding_engine,
    similarity_engine: BaseSimilarityEngine,
    knowledge_structures: Optional[KnowledgeStructures] = None,
    **kwargs,
) -> CommunityAwareStrategy:
    """Factory function for community-aware strategy."""
    return CommunityAwareStrategy(
        chunks=chunks,
        embeddings=embeddings,
        embedding_engine=embedding_engine,
        similarity_engine=similarity_engine,
        knowledge_structures=knowledge_structures,
        **kwargs,
    )
