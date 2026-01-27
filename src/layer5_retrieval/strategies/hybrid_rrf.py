"""
Hybrid RRF Retrieval Strategy

Combines dense (vector) and sparse (BM25) retrieval with either:
- Blended scoring (weighted dense + sparse with query-type awareness)
- Reciprocal Rank Fusion (legacy mode)
"""

import time
from typing import List, Dict, Optional, Tuple
import logging
import numpy as np

from .base import BaseRetrievalStrategy
from src.models.chunk import Chunk
from src.models.query import QueryPlan, QueryType
from src.models.retrieval import RetrievalResult, ScoredChunk, RetrievalConfidence
from src.layer2_graph.similarity.base import BaseSimilarityEngine

logger = logging.getLogger(__name__)


class HybridRRFStrategy(BaseRetrievalStrategy):
    """
    Hybrid retrieval combining dense and sparse search.

    Supports two scoring modes:
    - "blended": Weighted combination of normalized dense + sparse scores.
      Preserves score magnitudes for meaningful differentiation.
    - "rrf": Reciprocal Rank Fusion (legacy). Flattens scores by rank.

    Boosting:
    - "blended" mode: multiplicative (score * (1 + boost))
    - "rrf" mode: additive (score + boost)
    """

    DEFAULT_SEMANTIC_THRESHOLD = 0.3

    def __init__(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
        embedding_engine,
        similarity_engine: BaseSimilarityEngine,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        sparse_weight: float = 0.5,
        year_boost: float = 0.5,
        category_boost: float = 0.2,
        semantic_threshold: float = None,
        scoring_mode: str = "blended",
        dense_alpha: float = 0.6,
        sparse_beta: float = 0.4,
    ):
        """
        Initialize hybrid RRF strategy.

        Args:
            chunks: All chunks
            embeddings: Embedding matrix
            embedding_engine: Engine for query encoding
            similarity_engine: Vector similarity engine
            rrf_k: RRF constant (used in rrf mode)
            dense_weight: Weight for dense retrieval in RRF mode
            sparse_weight: Weight for sparse retrieval in RRF mode
            year_boost: Boost factor for year match
            category_boost: Boost factor for category match
            semantic_threshold: Min dense_score to apply boosts
            scoring_mode: "blended" or "rrf"
            dense_alpha: Weight for dense score in blended mode
            sparse_beta: Weight for sparse score in blended mode
        """
        super().__init__(chunks, embeddings)

        self.embedding_engine = embedding_engine
        self.similarity_engine = similarity_engine
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.year_boost = year_boost
        self.category_boost = category_boost
        self.semantic_threshold = (
            semantic_threshold if semantic_threshold is not None
            else self.DEFAULT_SEMANTIC_THRESHOLD
        )
        self.scoring_mode = scoring_mode
        self.dense_alpha = dense_alpha
        self.sparse_beta = sparse_beta

        # Build BM25 index
        self._build_bm25_index()

    def _build_bm25_index(self):
        """Build BM25 index for sparse retrieval."""
        try:
            from rank_bm25 import BM25Okapi
            tokenized = [c.text.lower().split() for c in self.chunks]
            self._bm25 = BM25Okapi(tokenized)
            self._bm25_available = True
            logger.info("BM25 index built successfully")
        except ImportError:
            logger.warning("rank_bm25 not installed, using dense-only retrieval")
            self._bm25 = None
            self._bm25_available = False

    def retrieve(
        self,
        query: str,
        plan: QueryPlan,
        top_k: int,
    ) -> RetrievalResult:
        """
        Retrieve using hybrid scoring.

        Args:
            query: Query string
            plan: Query plan with type/filters
            top_k: Maximum results

        Returns:
            RetrievalResult
        """
        start_time = time.time()

        # Get dense results
        dense_results = self._dense_retrieve(query, top_k * 2)

        # Get sparse results with normalized scores
        sparse_results = (
            self._sparse_retrieve(query, top_k * 2)
            if self._bm25_available else []
        )

        # Combine scores based on mode
        if self.scoring_mode == "blended":
            combined = self._combine_scores_blended(
                dense_results, sparse_results, plan.query_type
            )
        else:
            combined = self._rrf_combine(dense_results, sparse_results)

        # Apply boosting
        boosted = self._apply_boosting(combined, plan)

        # Filter and limit
        candidates = self._filter_and_limit(boosted, plan, top_k)

        # Determine confidence
        confidence = self._determine_confidence(candidates, plan)

        retrieval_time = (time.time() - start_time) * 1000

        return RetrievalResult(
            candidates=candidates,
            query=query,
            retrieval_strategy=f"hybrid_{self.scoring_mode}",
            total_candidates_considered=len(combined),
            retrieval_time_ms=retrieval_time,
            year_filter=plan.year_filter,
            category_filter=plan.category_filter,
            confidence=confidence,
        )

    def retrieve_with_prefilter(
        self,
        query: str,
        plan: QueryPlan,
        top_k: int,
        candidate_indices: List[int],
    ) -> RetrievalResult:
        """
        Retrieve within a prefiltered set of candidate indices.

        Performs dense search only within the specified indices,
        while BM25 searches the full corpus for keyword coverage.

        Args:
            query: Query string
            plan: Query plan
            top_k: Maximum results
            candidate_indices: Indices to search within for dense retrieval

        Returns:
            RetrievalResult
        """
        start_time = time.time()

        # Dense search within prefiltered candidates
        dense_results = self._dense_retrieve_filtered(
            query, top_k * 2, candidate_indices
        )

        # BM25 searches full corpus (keyword matches may be outside year filter)
        sparse_results = (
            self._sparse_retrieve(query, top_k * 2)
            if self._bm25_available else []
        )

        # Combine using blended scoring
        if self.scoring_mode == "blended":
            combined = self._combine_scores_blended(
                dense_results, sparse_results, plan.query_type
            )
        else:
            combined = self._rrf_combine(dense_results, sparse_results)

        # Apply boosting
        boosted = self._apply_boosting(combined, plan)

        # Filter and limit
        candidates = self._filter_and_limit(boosted, plan, top_k)

        # Determine confidence
        confidence = self._determine_confidence(candidates, plan)

        retrieval_time = (time.time() - start_time) * 1000

        return RetrievalResult(
            candidates=candidates,
            query=query,
            retrieval_strategy=f"hybrid_{self.scoring_mode}_prefiltered",
            total_candidates_considered=len(combined),
            retrieval_time_ms=retrieval_time,
            year_filter=plan.year_filter,
            category_filter=plan.category_filter,
            confidence=confidence,
        )

    def _dense_retrieve(self, query: str, k: int) -> List[Tuple[int, float, str]]:
        """Dense retrieval using vector similarity."""
        query_embedding = self.embedding_engine.encode_query(query)
        results = self.similarity_engine.find_similar(query_embedding, k)
        return [(idx, score, "dense") for idx, score in results]

    def _dense_retrieve_filtered(
        self,
        query: str,
        k: int,
        candidate_indices: List[int],
    ) -> List[Tuple[int, float, str]]:
        """Dense retrieval within a subset of candidate indices."""
        if not candidate_indices:
            return []

        query_embedding = self.embedding_engine.encode_query(query)

        # Get embeddings for candidates only
        candidate_embeddings = self.embeddings[candidate_indices]

        # Compute similarities
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Normalize for cosine similarity
        query_norm = query_embedding / (
            np.linalg.norm(query_embedding, axis=1, keepdims=True) + 1e-10
        )
        cand_norms = candidate_embeddings / (
            np.linalg.norm(candidate_embeddings, axis=1, keepdims=True) + 1e-10
        )

        similarities = np.dot(cand_norms, query_norm.T).flatten()

        # Get top-k indices within candidates
        top_k_local = min(k, len(similarities))
        top_local_indices = np.argsort(similarities)[::-1][:top_k_local]

        # Map back to original indices
        results = [
            (candidate_indices[local_idx], float(similarities[local_idx]), "dense")
            for local_idx in top_local_indices
            if similarities[local_idx] > 0
        ]

        return results

    def _sparse_retrieve(self, query: str, k: int) -> List[Tuple[int, float, str]]:
        """Sparse retrieval using BM25 with normalized scores."""
        if not self._bm25_available:
            return []

        tokenized_query = query.lower().split()
        raw_scores = self._bm25.get_scores(tokenized_query)

        # Normalize BM25 scores to [0, 1]
        normalized = self._normalize_scores(raw_scores)

        # Get top-k indices (filter zero scores)
        top_indices = np.argsort(normalized)[::-1][:k]

        return [
            (int(idx), float(normalized[idx]), "sparse")
            for idx in top_indices
            if normalized[idx] > 0
        ]

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Min-max normalize scores to [0, 1]."""
        min_score = scores.min()
        max_score = scores.max()
        if max_score - min_score < 1e-10:
            return np.zeros_like(scores)
        return (scores - min_score) / (max_score - min_score)

    def _get_blended_weights(self, query_type: QueryType) -> Tuple[float, float]:
        """
        Get query-type-aware blending weights.

        SPECIFIC queries weight BM25 more (keyword matching important).
        SYNTHESIS/EXPLORATORY queries weight dense more (semantic important).
        """
        if query_type == QueryType.SPECIFIC:
            return 0.5, 0.5
        elif query_type in (QueryType.SYNTHESIS, QueryType.EXPLORATORY):
            return 0.7, 0.3
        elif query_type == QueryType.TEMPORAL:
            return 0.55, 0.45
        elif query_type == QueryType.COMPARISON:
            return 0.6, 0.4
        else:
            return self.dense_alpha, self.sparse_beta

    def _combine_scores_blended(
        self,
        dense_results: List[Tuple[int, float, str]],
        sparse_results: List[Tuple[int, float, str]],
        query_type: QueryType,
    ) -> Dict[int, Dict]:
        """
        Combine dense and sparse scores using weighted blending.

        Preserves actual score magnitudes instead of just ranks,
        producing meaningful score differentiation.
        """
        alpha, beta = self._get_blended_weights(query_type)
        combined = {}

        # Process dense results
        for idx, score, _ in dense_results:
            if idx not in combined:
                combined[idx] = {
                    "dense_score": 0.0,
                    "sparse_score": 0.0,
                    "dense_rank": 0,
                    "sparse_rank": 0,
                }
            combined[idx]["dense_score"] = score

        # Process sparse results
        for rank, (idx, score, _) in enumerate(sparse_results, 1):
            if idx not in combined:
                combined[idx] = {
                    "dense_score": 0.0,
                    "sparse_score": 0.0,
                    "dense_rank": 0,
                    "sparse_rank": 0,
                }
            combined[idx]["sparse_score"] = score
            combined[idx]["sparse_rank"] = rank

        # Assign dense ranks for logging
        dense_sorted = sorted(
            [(idx, d["dense_score"]) for idx, d in combined.items()],
            key=lambda x: x[1], reverse=True
        )
        for rank, (idx, _) in enumerate(dense_sorted, 1):
            combined[idx]["dense_rank"] = rank

        # Compute blended scores
        for idx, data in combined.items():
            blended = alpha * data["dense_score"] + beta * data["sparse_score"]
            data["blended_score"] = blended
            # Also store RRF for fallback/comparison
            data["rrf_score"] = blended  # Use blended as combined_score

        logger.debug(
            f"Blended scoring: alpha={alpha:.2f}, beta={beta:.2f}, "
            f"query_type={query_type.value}, candidates={len(combined)}"
        )

        return combined

    def _rrf_combine(
        self,
        dense_results: List[Tuple[int, float, str]],
        sparse_results: List[Tuple[int, float, str]],
    ) -> Dict[int, Dict]:
        """Legacy RRF combination (preserved for backwards compatibility)."""
        combined = {}

        for rank, (idx, score, _) in enumerate(dense_results, 1):
            if idx not in combined:
                combined[idx] = {
                    "dense_score": 0.0,
                    "sparse_score": 0.0,
                    "dense_rank": 0,
                    "sparse_rank": 0,
                }
            combined[idx]["dense_score"] = score
            combined[idx]["dense_rank"] = rank

        for rank, (idx, score, _) in enumerate(sparse_results, 1):
            if idx not in combined:
                combined[idx] = {
                    "dense_score": 0.0,
                    "sparse_score": 0.0,
                    "dense_rank": 0,
                    "sparse_rank": 0,
                }
            combined[idx]["sparse_score"] = score
            combined[idx]["sparse_rank"] = rank

        for idx, data in combined.items():
            rrf_score = 0.0
            if data["dense_rank"] > 0:
                rrf_score += self.dense_weight / (self.rrf_k + data["dense_rank"])
            if data["sparse_rank"] > 0:
                rrf_score += self.sparse_weight / (self.rrf_k + data["sparse_rank"])
            data["rrf_score"] = rrf_score
            data["blended_score"] = rrf_score

        return combined

    def _apply_boosting(
        self,
        combined: Dict[int, Dict],
        plan: QueryPlan,
    ) -> List[ScoredChunk]:
        """
        Apply year and category boosting.

        In blended mode: multiplicative boosting preserves score ordering.
          final = blended * (1 + year_boost) * (1 + category_boost)
          Example: 0.8 * 1.5 = 1.2 vs 0.3 * 1.0 = 0.3

        In rrf mode: additive boosting (legacy behavior).
          final = rrf + year_boost + category_boost

        Safety: Only boost if dense_score >= semantic_threshold.
        """
        scored_chunks = []

        # Determine valid years for boosting
        valid_years = set()
        if plan.year_filter is not None:
            valid_years.add(plan.year_filter)
        if plan.filters.year_range is not None:
            start_year, end_year = plan.filters.year_range
            valid_years.update(range(start_year, end_year + 1))

        for idx, data in combined.items():
            chunk = self.get_chunk_by_index(idx)
            if not chunk:
                continue

            dense_score = data["dense_score"]
            blended_score = data.get("blended_score", data.get("rrf_score", 0.0))

            # Determine matches
            year_matched = bool(valid_years) and chunk.year in valid_years
            category_matched = (
                plan.category_filter is not None
                and chunk.category == plan.category_filter
            )

            # Only apply boost if semantic relevance above threshold
            meets_threshold = dense_score >= self.semantic_threshold

            if meets_threshold and self.scoring_mode == "blended":
                # Multiplicative boosting: preserves semantic ordering
                year_mult = (1.0 + self.year_boost) if year_matched else 1.0
                cat_mult = (1.0 + self.category_boost) if category_matched else 1.0
                final_score = blended_score * year_mult * cat_mult
                applied_year_boost = self.year_boost if year_matched else 0.0
                applied_category_boost = self.category_boost if category_matched else 0.0
            elif meets_threshold:
                # Additive boosting (legacy RRF mode)
                applied_year_boost = self.year_boost if year_matched else 0.0
                applied_category_boost = self.category_boost if category_matched else 0.0
                final_score = blended_score + applied_year_boost + applied_category_boost
            else:
                # Below threshold: no boost
                final_score = blended_score
                applied_year_boost = 0.0
                applied_category_boost = 0.0

            scored_chunk = ScoredChunk(
                chunk=chunk,
                vector_score=dense_score,
                bm25_score=data["sparse_score"],
                combined_score=data.get("rrf_score", blended_score),
                blended_score=blended_score,
                final_score=final_score,
                year_boost=applied_year_boost,
                category_boost=applied_category_boost,
                year_matched=year_matched,
                category_matched=category_matched,
            )
            scored_chunks.append(scored_chunk)

        scored_chunks.sort(key=lambda x: x.final_score, reverse=True)

        # Log score distribution for debugging
        if scored_chunks:
            scores = [sc.final_score for sc in scored_chunks[:10]]
            logger.debug(
                f"Top-10 score distribution: "
                f"max={scores[0]:.4f}, min={scores[-1]:.4f}, "
                f"range={scores[0] - scores[-1]:.4f}"
            )

        return scored_chunks

    def _filter_and_limit(
        self,
        candidates: List[ScoredChunk],
        plan: QueryPlan,
        top_k: int,
    ) -> List[ScoredChunk]:
        """Filter candidates and limit to top_k."""
        if plan.year_filter:
            year_matched = [c for c in candidates if c.year_matched]
            other = [c for c in candidates if not c.year_matched]
            result = year_matched[:top_k]
            remaining = top_k - len(result)
            if remaining > 0:
                result.extend(other[:remaining])
        else:
            result = candidates[:top_k]

        for i, chunk in enumerate(result):
            chunk.rank = i + 1

        return result

    def _determine_confidence(
        self,
        candidates: List[ScoredChunk],
        plan: QueryPlan,
    ) -> RetrievalConfidence:
        """Determine retrieval confidence based on results."""
        if not candidates:
            return RetrievalConfidence.NO_RESULTS

        year_matched_count = sum(1 for c in candidates if c.year_matched)

        has_year_constraint = (
            plan.year_filter is not None or
            plan.filters.year_range is not None
        )

        if has_year_constraint:
            if year_matched_count >= 1:
                return RetrievalConfidence.YEAR_MATCHED
            else:
                return RetrievalConfidence.PARTIAL_MATCH

        if len(candidates) >= 3:
            return RetrievalConfidence.GOOD_MATCH
        elif len(candidates) > 0:
            return RetrievalConfidence.LOW_MATCH
        else:
            return RetrievalConfidence.NO_RESULTS


def create_hybrid_rrf_strategy(
    chunks: List[Chunk],
    embeddings: np.ndarray,
    embedding_engine,
    similarity_engine: BaseSimilarityEngine,
) -> HybridRRFStrategy:
    """Factory function for hybrid RRF strategy."""
    return HybridRRFStrategy(
        chunks=chunks,
        embeddings=embeddings,
        embedding_engine=embedding_engine,
        similarity_engine=similarity_engine,
    )
