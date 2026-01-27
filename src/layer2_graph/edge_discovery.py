"""
Edge Discovery Module

Discovers connections between chunks based on similarity thresholds.
"""

from typing import List, Tuple, Dict, Optional
import logging
import numpy as np

from src.models.chunk import Chunk
from src.models.graph import GraphEdge, EdgeType
from .similarity.base import BaseSimilarityEngine

logger = logging.getLogger(__name__)


class EdgeDiscovery:
    """
    Discovers edges between chunks based on semantic similarity.

    Implements the paper's memory-efficient connection discovery algorithm:
    - Processes embeddings in batches (chunk_size=50) to avoid O(N^2) memory
    - Uses configurable thresholds: 0.38 for same-domain, 0.30 for cross-domain
    - Top-15 neighbors per node
    - Semantic edge typing via keyword heuristics
    """

    # Keyword sets for semantic edge classification (from paper Table III)
    # Note: Only multi-word phrases or distinctive single words are used to avoid
    # false positives from common words like "but" or "because"
    CONTRADICTION_KEYWORDS = {"however", "although", "contrary", "disagree",
                              "nevertheless", "on the other hand", "in contrast"}
    CAUSAL_KEYWORDS = {"therefore", "led to", "caused", "resulted in",
                       "consequently", "as a result", "this led"}
    SUPPORT_KEYWORDS = {"confirms", "agrees", "evidence", "proves", "validates",
                        "consistent with", "aligns with", "reinforces"}
    TEMPORAL_KEYWORDS = {"subsequently", "afterwards", "over time",
                         "eventually", "years later", "looking back"}

    def __init__(
        self,
        semantic_threshold: float = 0.38,
        cross_domain_threshold: float = 0.30,
        max_total_edges: int = 3000,
        top_k_neighbors: int = 15,
    ):
        """
        Initialize edge discovery.

        Args:
            semantic_threshold: Similarity threshold for same-domain edges (paper: 0.38)
            cross_domain_threshold: Threshold for cross-domain edges (paper: 0.30)
            max_total_edges: Maximum total edges in graph (paper: 3000)
            top_k_neighbors: Max neighbors per node (paper: 15)
        """
        self.semantic_threshold = semantic_threshold
        self.cross_domain_threshold = cross_domain_threshold
        self.max_total_edges = max_total_edges
        self.top_k_neighbors = top_k_neighbors

    def discover_edges(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
        similarity_engine: BaseSimilarityEngine,
    ) -> List[GraphEdge]:
        """
        Discover all edges between chunks.

        Uses a hybrid approach:
        1. k-NN to find candidate edges for each node
        2. Threshold filtering based on domain

        Args:
            chunks: List of Chunk objects
            embeddings: Embedding matrix
            similarity_engine: Similarity search engine

        Returns:
            List of GraphEdge objects
        """
        if not chunks or embeddings.size == 0:
            return []

        logger.info(f"Discovering edges for {len(chunks)} chunks...")

        # Build index if not already built
        if not similarity_engine.is_built:
            similarity_engine.build_index(embeddings)

        # Build chunk lookup
        chunk_by_idx = {i: chunk for i, chunk in enumerate(chunks)}

        # Find candidate edges using k-NN
        edges = self._find_knn_edges(chunks, embeddings, similarity_engine, chunk_by_idx)

        # Add sequential edges (same document, adjacent chunks)
        sequential_edges = self._find_sequential_edges(chunks)
        edges.extend(sequential_edges)

        # Deduplicate edges
        edges = self._deduplicate_edges(edges)

        # Limit total edges if needed
        if len(edges) > self.max_total_edges:
            edges = self._limit_edges(edges, self.max_total_edges)

        logger.info(f"Discovered {len(edges)} edges")
        return edges

    def _find_knn_edges(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
        similarity_engine: BaseSimilarityEngine,
        chunk_by_idx: Dict[int, Chunk],
    ) -> List[GraphEdge]:
        """Find edges using k-nearest neighbors."""
        edges = []

        # Batch query for all chunks
        results = similarity_engine.find_similar_batch(embeddings, self.top_k_neighbors + 1)

        for i, neighbors in enumerate(results):
            source_chunk = chunk_by_idx[i]

            for neighbor_idx, similarity in neighbors:
                # Skip self
                if neighbor_idx == i:
                    continue

                target_chunk = chunk_by_idx[neighbor_idx]

                # Determine threshold based on domain
                same_category = source_chunk.category == target_chunk.category
                threshold = self.semantic_threshold if same_category else self.cross_domain_threshold

                if similarity >= threshold:
                    edge_type = self._determine_edge_type(
                        source_chunk, target_chunk, similarity, same_category
                    )

                    edge = GraphEdge(
                        source_id=source_chunk.chunk_id,
                        target_id=target_chunk.chunk_id,
                        edge_type=edge_type,
                        weight=similarity,
                        similarity=similarity,
                        created_by="knn",
                    )
                    edges.append(edge)

        return edges

    def _find_sequential_edges(self, chunks: List[Chunk]) -> List[GraphEdge]:
        """Find sequential edges (adjacent chunks in same document)."""
        edges = []

        # Group chunks by document
        doc_chunks: Dict[str, List[Chunk]] = {}
        for chunk in chunks:
            if chunk.doc_id not in doc_chunks:
                doc_chunks[chunk.doc_id] = []
            doc_chunks[chunk.doc_id].append(chunk)

        # Sort each document's chunks by index
        for doc_id, doc_chunk_list in doc_chunks.items():
            doc_chunk_list.sort(key=lambda c: c.chunk_index)

            # Create edges between adjacent chunks
            for i in range(len(doc_chunk_list) - 1):
                source = doc_chunk_list[i]
                target = doc_chunk_list[i + 1]

                edge = GraphEdge(
                    source_id=source.chunk_id,
                    target_id=target.chunk_id,
                    edge_type=EdgeType.SEQUENTIAL,
                    weight=0.9,  # High weight for sequential
                    similarity=0.9,
                    created_by="sequential",
                )
                edges.append(edge)

        return edges

    def _determine_edge_type(
        self,
        source: Chunk,
        target: Chunk,
        similarity: float,
        same_category: bool,
    ) -> EdgeType:
        """
        Classify edge type using heuristic-based detection (paper Algorithm).

        Decision flowchart:
        1. Same doc & target chunk_index > source → ELABORATES
        2. Contradiction keywords in either chunk → CONTRADICTS
        3. Causal keywords in either chunk → CAUSES
        4. Support keywords in either chunk → SUPPORTS
        5. Earlier year + temporal markers → TEMPORAL_SEQUENCE
        6. Different category → CROSS_DOMAIN
        7. Default (same category) → SAME_TOPIC
        """
        # 1. Same document, later chunk → elaborates
        if source.doc_id == target.doc_id and target.chunk_index > source.chunk_index:
            return EdgeType.ELABORATES

        # Get combined text for keyword checking (lowercase)
        combined_text = (source.text + " " + target.text).lower()

        # 2. Contradiction keywords
        if any(kw in combined_text for kw in self.CONTRADICTION_KEYWORDS):
            return EdgeType.CONTRADICTS

        # 3. Causal keywords
        if any(kw in combined_text for kw in self.CAUSAL_KEYWORDS):
            return EdgeType.CAUSES

        # 4. Support keywords
        if any(kw in combined_text for kw in self.SUPPORT_KEYWORDS):
            return EdgeType.SUPPORTS

        # 5. Temporal sequence: earlier year + temporal markers
        if (source.year != target.year and
                any(kw in combined_text for kw in self.TEMPORAL_KEYWORDS)):
            return EdgeType.TEMPORAL_SEQUENCE

        # 6. Different category → cross_domain
        if not same_category:
            return EdgeType.CROSS_DOMAIN

        # 7. Default: same category, high similarity → same_topic
        return EdgeType.SAME_TOPIC

    def _deduplicate_edges(self, edges: List[GraphEdge]) -> List[GraphEdge]:
        """Remove duplicate edges (keep highest similarity)."""
        edge_dict: Dict[Tuple[str, str], GraphEdge] = {}

        for edge in edges:
            # Create canonical key (sorted pair)
            key = tuple(sorted([edge.source_id, edge.target_id]))

            if key not in edge_dict or edge.similarity > edge_dict[key].similarity:
                edge_dict[key] = edge

        return list(edge_dict.values())

    def _limit_edges(self, edges: List[GraphEdge], max_edges: int) -> List[GraphEdge]:
        """Limit total edges by keeping highest similarity ones."""
        # Sort by similarity descending
        edges.sort(key=lambda e: e.similarity, reverse=True)
        return edges[:max_edges]


class EdgeTyper:
    """
    Classifies edges with semantic type labels using keyword heuristics.

    Implements the paper's heuristic-based edge classification (1000x faster
    than LLM-based classification at comparable quality).
    """

    def __init__(self, llm_provider=None):
        """
        Initialize edge typer.

        Args:
            llm_provider: Optional LLM for semantic typing (not used in paper)
        """
        self.llm_provider = llm_provider

    def classify_edge(
        self,
        source_chunk: Chunk,
        target_chunk: Chunk,
        similarity: float,
    ) -> EdgeType:
        """
        Classify edge type based on chunk content using keyword heuristics.

        Uses the same classification logic as EdgeDiscovery._determine_edge_type.
        """
        same_category = source_chunk.category == target_chunk.category

        # Same document, later chunk → elaborates
        if source_chunk.doc_id == target_chunk.doc_id and target_chunk.chunk_index > source_chunk.chunk_index:
            return EdgeType.ELABORATES

        combined_text = (source_chunk.text + " " + target_chunk.text).lower()

        if any(kw in combined_text for kw in EdgeDiscovery.CONTRADICTION_KEYWORDS):
            return EdgeType.CONTRADICTS
        if any(kw in combined_text for kw in EdgeDiscovery.CAUSAL_KEYWORDS):
            return EdgeType.CAUSES
        if any(kw in combined_text for kw in EdgeDiscovery.SUPPORT_KEYWORDS):
            return EdgeType.SUPPORTS
        if (source_chunk.year != target_chunk.year and
                any(kw in combined_text for kw in EdgeDiscovery.TEMPORAL_KEYWORDS)):
            return EdgeType.TEMPORAL_SEQUENCE
        if not same_category:
            return EdgeType.CROSS_DOMAIN

        return EdgeType.SAME_TOPIC


def create_edge_discovery(
    semantic_threshold: float = 0.38,
    cross_domain_threshold: float = 0.30,
    max_total_edges: int = 3000,
    top_k_neighbors: int = 15,
) -> EdgeDiscovery:
    """Factory function to create edge discovery."""
    return EdgeDiscovery(
        semantic_threshold=semantic_threshold,
        cross_domain_threshold=cross_domain_threshold,
        max_total_edges=max_total_edges,
        top_k_neighbors=top_k_neighbors,
    )
