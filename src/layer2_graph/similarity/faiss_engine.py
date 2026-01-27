"""
FAISS Similarity Engine

FAISS-based implementation for fast similarity search.
Best for large datasets (>5K items) and production use.
"""

from typing import List, Tuple, Optional
import logging
import numpy as np

from .base import BaseSimilarityEngine

logger = logging.getLogger(__name__)


class FaissSimilarityEngine(BaseSimilarityEngine):
    """
    FAISS-based similarity search engine.

    Uses Facebook AI Similarity Search for efficient nearest neighbor search.
    Supports both CPU and GPU.

    Pros:
    - Very fast for large datasets
    - Supports approximate search for even faster results
    - GPU acceleration available

    Cons:
    - Requires faiss-cpu or faiss-gpu package
    - More complex configuration
    """

    def __init__(
        self,
        dimension: int,
        use_gpu: bool = False,
        index_type: str = "flat",
        nlist: int = 100,
        nprobe: int = 10,
    ):
        """
        Initialize FAISS similarity engine.

        Args:
            dimension: Embedding dimension
            use_gpu: Whether to use GPU (requires faiss-gpu)
            index_type: Index type ('flat', 'ivf', 'hnsw')
            nlist: Number of clusters for IVF index
            nprobe: Number of clusters to search for IVF
        """
        super().__init__(dimension)

        self.use_gpu = use_gpu
        self.index_type = index_type
        self.nlist = nlist
        self.nprobe = nprobe
        self._index = None
        self._faiss = None
        self._embeddings = None  # Keep copy for find_all_pairs

    def _get_faiss(self):
        """Lazy import faiss."""
        if self._faiss is None:
            try:
                import faiss
                self._faiss = faiss
            except ImportError:
                raise ImportError(
                    "faiss is required. Install with: pip install faiss-cpu "
                    "or pip install faiss-gpu"
                )
        return self._faiss

    def build_index(self, embeddings: np.ndarray) -> None:
        """
        Build FAISS index from embeddings.

        Args:
            embeddings: numpy array of shape (n_items, embedding_dim)
        """
        faiss = self._get_faiss()

        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be 2D array")

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {embeddings.shape[1]}"
            )

        # Ensure float32 and contiguous
        embeddings = np.ascontiguousarray(embeddings.astype(np.float32))

        # L2 normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        # Keep a copy for find_all_pairs
        self._embeddings = embeddings.copy()

        # Create index based on type
        if self.index_type == "flat":
            # Exact search - Inner Product (cosine after normalization)
            self._index = faiss.IndexFlatIP(self.dimension)

        elif self.index_type == "ivf":
            # Approximate search with IVF
            quantizer = faiss.IndexFlatIP(self.dimension)
            self._index = faiss.IndexIVFFlat(
                quantizer, self.dimension, self.nlist, faiss.METRIC_INNER_PRODUCT
            )
            self._index.train(embeddings)
            self._index.nprobe = self.nprobe

        elif self.index_type == "hnsw":
            # Hierarchical Navigable Small World
            self._index = faiss.IndexHNSWFlat(self.dimension, 32, faiss.METRIC_INNER_PRODUCT)

        else:
            raise ValueError(f"Unknown index type: {self.index_type}")

        # Move to GPU if requested
        if self.use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self._index = faiss.index_cpu_to_gpu(res, 0, self._index)
                logger.info("Using GPU for FAISS")
            except Exception as e:
                logger.warning(f"Failed to use GPU, falling back to CPU: {e}")

        # Add embeddings to index
        self._index.add(embeddings)

        self._num_items = embeddings.shape[0]
        self._index_built = True

        logger.info(
            f"Built FAISS {self.index_type} index with {self._num_items} items"
        )

    def find_similar(
        self,
        query_embedding: np.ndarray,
        k: int,
    ) -> List[Tuple[int, float]]:
        """
        Find k most similar items.

        Args:
            query_embedding: Query embedding vector
            k: Number of results

        Returns:
            List of (index, similarity_score) tuples
        """
        if not self._index_built:
            raise RuntimeError("Index not built. Call build_index first.")

        faiss = self._get_faiss()

        # Prepare query
        query = np.ascontiguousarray(
            query_embedding.reshape(1, -1).astype(np.float32)
        )
        faiss.normalize_L2(query)

        # Search
        k = min(k, self._num_items)
        similarities, indices = self._index.search(query, k)

        # Return as list of tuples
        results = [
            (int(idx), float(sim))
            for idx, sim in zip(indices[0], similarities[0])
            if idx >= 0  # FAISS returns -1 for empty slots
        ]

        return results

    def find_similar_batch(
        self,
        query_embeddings: np.ndarray,
        k: int,
    ) -> List[List[Tuple[int, float]]]:
        """
        Find k most similar items for multiple queries.

        Args:
            query_embeddings: Query embedding matrix (n_queries, dim)
            k: Number of results per query

        Returns:
            List of lists of (index, similarity_score) tuples
        """
        if not self._index_built:
            raise RuntimeError("Index not built. Call build_index first.")

        faiss = self._get_faiss()

        # Prepare queries
        queries = np.ascontiguousarray(query_embeddings.astype(np.float32))
        faiss.normalize_L2(queries)

        # Search
        k = min(k, self._num_items)
        similarities, indices = self._index.search(queries, k)

        # Return as nested list of tuples
        results = []
        for i in range(len(queries)):
            query_results = [
                (int(idx), float(sim))
                for idx, sim in zip(indices[i], similarities[i])
                if idx >= 0
            ]
            results.append(query_results)

        return results

    def find_all_pairs(
        self,
        threshold: float,
        max_pairs: Optional[int] = None,
    ) -> List[Tuple[int, int, float]]:
        """
        Find all pairs with similarity above threshold.

        For FAISS, this falls back to using stored embeddings
        since FAISS doesn't have native all-pairs search.

        Args:
            threshold: Minimum similarity threshold
            max_pairs: Maximum number of pairs to return

        Returns:
            List of (idx1, idx2, similarity) tuples
        """
        if not self._index_built or self._embeddings is None:
            raise RuntimeError("Index not built or embeddings not stored.")

        logger.info(f"Finding all pairs with similarity >= {threshold}...")

        # Use stored embeddings for all-pairs computation
        similarity_matrix = np.dot(self._embeddings, self._embeddings.T)

        # Get upper triangle indices
        rows, cols = np.triu_indices(self._num_items, k=1)

        # Filter by threshold
        similarities = similarity_matrix[rows, cols]
        mask = similarities >= threshold
        filtered_rows = rows[mask]
        filtered_cols = cols[mask]
        filtered_sims = similarities[mask]

        # Sort by similarity descending
        sort_idx = np.argsort(filtered_sims)[::-1]

        if max_pairs is not None:
            sort_idx = sort_idx[:max_pairs]

        pairs = [
            (int(filtered_rows[i]), int(filtered_cols[i]), float(filtered_sims[i]))
            for i in sort_idx
        ]

        logger.info(f"Found {len(pairs)} pairs above threshold")
        return pairs


def create_faiss_engine(
    dimension: int,
    use_gpu: bool = False,
    index_type: str = "flat",
) -> FaissSimilarityEngine:
    """Factory function to create FAISS similarity engine."""
    return FaissSimilarityEngine(
        dimension=dimension,
        use_gpu=use_gpu,
        index_type=index_type,
    )
