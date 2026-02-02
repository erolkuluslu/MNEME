"""
Retrieval Engine

Main retrieval orchestrator that coordinates retrieval strategies.
"""

import time
from typing import List, Optional, Set
import logging
import numpy as np

try:
    import networkx as nx
except ImportError:
    nx = None

from src.config import MNEMEConfig
from src.models.chunk import Chunk
from src.models.query import QueryPlan, QueryType
from src.models.retrieval import RetrievalResult
from src.layer2_graph.embeddings.base import BaseEmbeddingEngine
from src.layer2_graph.similarity.base import BaseSimilarityEngine
from .strategies.base import BaseRetrievalStrategy
from .strategies.hybrid_rrf import HybridRRFStrategy
from .prefilter import YearPrefilter

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """
    Main retrieval engine that coordinates retrieval strategies.

    Supports multiple retrieval strategies and handles
    filtering, boosting, and result aggregation.
    """

    def __init__(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
        config: MNEMEConfig,
        embedding_engine: BaseEmbeddingEngine,
        similarity_engine: BaseSimilarityEngine,
        strategy: Optional[BaseRetrievalStrategy] = None,
        graph: Optional["nx.DiGraph"] = None,
    ):
        """
        Initialize retrieval engine.

        Args:
            chunks: All chunks in corpus
            embeddings: Embedding matrix
            config: MNEME configuration
            embedding_engine: Engine for query encoding
            similarity_engine: Vector similarity engine
            strategy: Optional custom strategy
            graph: Knowledge graph for expansion
        """
        self.chunks = chunks
        self.embeddings = embeddings
        self.config = config
        self.embedding_engine = embedding_engine
        self.similarity_engine = similarity_engine
        self.graph = graph

        # Build index
        if not similarity_engine.is_built:
            similarity_engine.build_index(embeddings)

        # Initialize strategy
        self.strategy = strategy or self._create_default_strategy()

        # Build lookups
        self._chunk_by_id = {c.chunk_id: c for c in chunks}
        self._chunks_by_year = self._build_year_index()
        self._chunks_by_category = self._build_category_index()

        # Initialize year prefilter for temporal queries
        self.prefilter = YearPrefilter(chunks)

        logger.info(
            f"Initialized retrieval engine with {len(chunks)} chunks, "
            f"strategy={config.retrieval_strategy}"
        )

    def _create_default_strategy(self) -> BaseRetrievalStrategy:
        """Create default retrieval strategy based on config."""
        # Compute adaptive RRF k from corpus size
        if self.config.adaptive_rrf_k:
            rrf_k = max(10, int(len(self.chunks) * self.config.rrf_k_ratio))
            logger.info(
                f"Adaptive RRF k: {rrf_k} "
                f"(corpus={len(self.chunks)}, ratio={self.config.rrf_k_ratio})"
            )
        else:
            rrf_k = self.config.rrf_k_constant

        return HybridRRFStrategy(
            chunks=self.chunks,
            embeddings=self.embeddings,
            embedding_engine=self.embedding_engine,
            similarity_engine=self.similarity_engine,
            rrf_k=rrf_k,
            dense_weight=self.config.dense_weight,
            sparse_weight=self.config.sparse_weight,
            year_boost=self.config.year_match_boost,
            category_boost=self.config.category_match_boost,
            semantic_threshold=self.config.semantic_relevance_threshold,
            scoring_mode=self.config.scoring_mode,
            dense_alpha=self.config.dense_alpha,
            sparse_beta=self.config.sparse_beta,
            # Temporal decay (paper S2)
            temporal_decay_rate=self.config.temporal_decay_rate,
            enable_temporal_decay=self.config.enable_temporal_decay,
            # Trust scoring (paper S3, S7)
            trust_threshold=self.config.trust_threshold,
            enable_trust_filtering=self.config.enable_trust_filtering,
            user_confirmation_weight=self.config.user_confirmation_weight,
            source_reliability_weight=self.config.source_reliability_weight,
        )

    def _build_year_index(self) -> dict:
        """Build index of chunks by year."""
        index = {}
        for chunk in self.chunks:
            if chunk.year not in index:
                index[chunk.year] = []
            index[chunk.year].append(chunk)
        return index

    def _build_category_index(self) -> dict:
        """Build index of chunks by category."""
        index = {}
        for chunk in self.chunks:
            if chunk.category not in index:
                index[chunk.category] = []
            index[chunk.category].append(chunk)
        return index

    def retrieve(
        self,
        query: str,
        plan: QueryPlan,
    ) -> RetrievalResult:
        """
        Retrieve relevant chunks for a query.

        Uses year prefilter when:
        - config.use_year_prefilter is True
        - Query has a year_filter or year_range
        - Prefilter yields enough candidates (>= min_docs)

        Args:
            query: Query string
            plan: Query plan with filters and settings

        Returns:
            RetrievalResult with scored candidates
        """
        top_k = plan.max_docs

        # Try prefiltered retrieval for year-constrained queries
        result = None
        if self._should_use_prefilter(plan):
            result = self._retrieve_with_prefilter(query, plan, top_k)

        # Fallback to full search if prefilter didn't produce enough results
        if result is None or len(result.candidates) < plan.min_docs:
            result = self.strategy.retrieve(query, plan, top_k)

        # Graph Expansion (New)
        if self.config.enable_graph_expansion and self.graph:
            result = self._expand_with_graph(query, result, plan)

        # Ensure minimum results if possible
        if len(result.candidates) < plan.min_docs:
            expanded_result = self._expand_search(query, plan, top_k)
            if len(expanded_result.candidates) > len(result.candidates):
                result = expanded_result

        # Chronological ordering for temporal evolution queries
        if self._should_apply_chronological_ordering(query, plan):
            result = self._apply_chronological_ordering(result)

        return result

    def _should_use_prefilter(self, plan: QueryPlan) -> bool:
        """Determine if year prefilter should be used."""
        if not self.config.use_year_prefilter:
            return False
        if not isinstance(self.strategy, HybridRRFStrategy):
            return False
        return plan.year_filter is not None or plan.filters.year_range is not None

    def _retrieve_with_prefilter(
        self,
        query: str,
        plan: QueryPlan,
        top_k: int,
    ) -> Optional[RetrievalResult]:
        """
        Retrieve using year prefilter to narrow dense search candidates.

        For year_range queries, collects indices for all years in range.
        Falls back to None if too few candidates found.
        """
        # Collect candidate indices
        candidate_indices = []

        if plan.filters.year_range is not None:
            start_year, end_year = plan.filters.year_range

            # For COMPARISON queries, retrieve only boundary years (e.g., "2020 vs 2024" → [2020, 2024])
            # For TEMPORAL queries, retrieve all years in range (e.g., "2020 to 2024" → [2020, 2021, 2022, 2023, 2024])
            if plan.query_type == QueryType.COMPARISON:
                years_to_retrieve = [start_year, end_year]
                logger.debug(
                    f"COMPARISON query: retrieving boundary years only {years_to_retrieve}"
                )
            else:
                years_to_retrieve = list(range(start_year, end_year + 1))

            for year in years_to_retrieve:
                candidate_indices.extend(
                    self.prefilter.get_candidate_indices(year, range_size=0)
                )
        elif plan.year_filter is not None:
            candidate_indices = self.prefilter.get_candidate_indices(
                plan.year_filter, range_size=self.config.year_expansion_range
            )

        # Need enough candidates for meaningful retrieval
        if len(candidate_indices) < plan.min_docs:
            logger.debug(
                f"Prefilter yielded only {len(candidate_indices)} candidates "
                f"(need {plan.min_docs}), falling back to full search"
            )
            return None

        logger.debug(
            f"Using year prefilter: {len(candidate_indices)} candidates "
            f"for year_filter={plan.year_filter}, range={plan.filters.year_range}"
        )

        return self.strategy.retrieve_with_prefilter(
            query, plan, top_k, candidate_indices
        )

    def _expand_with_graph(
        self,
        query: str,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> RetrievalResult:
        """
        Expand retrieval results using graph neighbors.
        
        Traverses edges of types specified in config (CAUSES, CONTRADICTS, SUPPORTS)
        to find semantically relevant neighbors that might have been missed.
        """
        if not result.candidates:
            return result
            
        logger.debug("Expanding search with graph neighbors...")
        
        # Get IDs of current candidates
        current_ids = {c.chunk.chunk_id for c in result.candidates}
        candidates_to_add = []
        
        # Identify valid edge types
        valid_types = set(self.config.graph_expansion_edge_types)
        
        # Check neighbors for top candidates (limit to top 5 to avoid explosion)
        for scored_chunk in result.candidates[:5]:
            chunk_id = scored_chunk.chunk.chunk_id
            
            if not self.graph.has_node(chunk_id):
                continue
                
            # Get neighbors via outgoing edges
            for neighbor_id in self.graph.successors(chunk_id):
                if neighbor_id in current_ids:
                    continue
                    
                # Check edge type
                edge_data = self.graph.get_edge_data(chunk_id, neighbor_id)
                edge_type = edge_data.get("type")
                
                # If explicit semantic edge, consider it
                if str(edge_type) in valid_types or edge_type in valid_types:
                    neighbor_chunk = self._chunk_by_id.get(neighbor_id)
                    if neighbor_chunk:
                        candidates_to_add.append(neighbor_chunk)
                        current_ids.add(neighbor_id)
            
            # Get neighbors via incoming edges (if undirected semantics matter)
            for neighbor_id in self.graph.predecessors(chunk_id):
                if neighbor_id in current_ids:
                    continue
                    
                edge_data = self.graph.get_edge_data(neighbor_id, chunk_id)
                edge_type = edge_data.get("type")
                
                if str(edge_type) in valid_types or edge_type in valid_types:
                    neighbor_chunk = self._chunk_by_id.get(neighbor_id)
                    if neighbor_chunk:
                        candidates_to_add.append(neighbor_chunk)
                        current_ids.add(neighbor_id)
                        
        if not candidates_to_add:
            return result
            
        logger.debug(f"Found {len(candidates_to_add)} graph neighbors to evaluate")
        
        # Score new candidates against the query
        # We use dense similarity for this check
        new_indices = [c.embedding_index for c in candidates_to_add]
        
        # Temporarily use filtered dense retrieval to score these
        # This is efficient because we only check specific indices
        scored_neighbors = self.strategy._dense_retrieve_filtered(
            query, len(candidates_to_add), new_indices
        )
        
        # Convert to ScoredChunk objects
        from src.models.retrieval import ScoredChunk
        
        added_chunks = []
        for idx, score, _ in scored_neighbors:
            # Only add if score is reasonable (e.g. > 0.25)
            # This prevents adding completely irrelevant neighbors
            if score < 0.25:
                continue
                
            chunk = self.chunks[idx]
            
            # Create ScoredChunk (missing BM25/RRF scores, so approximate)
            scored = ScoredChunk(
                chunk=chunk,
                vector_score=score,
                bm25_score=0.0,
                combined_score=score * 0.9, # Discount slightly vs direct hits
                final_score=score * 0.9,
                year_matched=chunk.year == plan.year_filter if plan.year_filter else False
            )
            added_chunks.append(scored)
            
        if added_chunks:
            logger.info(f"Graph expansion added {len(added_chunks)} relevant neighbors")
            result.candidates.extend(added_chunks)
            # Re-sort by score
            result.candidates.sort(key=lambda x: x.final_score, reverse=True)
            
        return result

    def _expand_search(
        self,
        query: str,
        plan: QueryPlan,
        top_k: int,
    ) -> RetrievalResult:
        """Expand search by relaxing filters."""
        # Create a relaxed plan
        from src.models.query import QueryFilters, QueryExpansion

        relaxed_plan = QueryPlan(
            original_query=plan.original_query,
            query_type=plan.query_type,
            intent=plan.intent,
            filters=QueryFilters(),  # No filters
            expansion=plan.expansion,
            min_docs=plan.min_docs,
            max_docs=top_k * 2,
        )

        return self.strategy.retrieve(query, relaxed_plan, top_k * 2)

    def get_chunks_by_year(self, year: int) -> List[Chunk]:
        """Get all chunks for a specific year."""
        return self._chunks_by_year.get(year, [])

    def get_chunks_by_category(self, category: str) -> List[Chunk]:
        """Get all chunks for a specific category."""
        return self._chunks_by_category.get(category, [])

    def get_available_years(self) -> List[int]:
        """Get list of years with chunks."""
        return sorted(self._chunks_by_year.keys())

    def get_available_categories(self) -> List[str]:
        """Get list of categories with chunks."""
        return sorted(self._chunks_by_category.keys())

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get chunk by ID."""
        return self._chunk_by_id.get(chunk_id)

    def _should_apply_chronological_ordering(
        self, query: str, plan: QueryPlan
    ) -> bool:
        """
        Determine if results should be sorted chronologically.

        Applies to TEMPORAL queries asking about evolution/progression over time.
        """
        if plan.query_type != QueryType.TEMPORAL:
            return False

        # Keywords indicating temporal evolution/progression
        evolution_keywords = [
            "evolve", "evolution", "progress", "progression",
            "change", "changed", "develop", "development",
            "grow", "growth", "trajectory", "over time",
            "timeline", "journey", "transformation"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in evolution_keywords)

    def _apply_chronological_ordering(self, result: RetrievalResult) -> RetrievalResult:
        """
        Re-sort retrieval results chronologically (oldest first).

        For temporal evolution queries, chronological order is more important
        than relevance score for understanding progression over time.
        """
        # Sort candidates by year (ascending - oldest first)
        sorted_candidates = sorted(
            result.candidates,
            key=lambda sc: (sc.chunk.year if sc.chunk.year else 9999)
        )

        logger.info(
            f"Applied chronological ordering: "
            f"years {[c.chunk.year for c in sorted_candidates[:10]]}"
        )

        # Create new result preserving all original fields
        from dataclasses import replace
        return replace(result, candidates=sorted_candidates)


def create_retrieval_engine(
    chunks: List[Chunk],
    embeddings: np.ndarray,
    config: MNEMEConfig,
    embedding_engine: BaseEmbeddingEngine,
    similarity_engine: BaseSimilarityEngine,
    graph: Optional["nx.DiGraph"] = None,
) -> RetrievalEngine:
    """Factory function to create retrieval engine."""
    return RetrievalEngine(
        chunks=chunks,
        embeddings=embeddings,
        config=config,
        embedding_engine=embedding_engine,
        similarity_engine=similarity_engine,
        graph=graph,
    )
