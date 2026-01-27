"""
NumPy Similarity Engine

Pure NumPy implementation for similarity search.
Best for small datasets (<5K items) or when FAISS is not available.
"""

from typing import List, Tuple, Optional
import logging
import numpy as np

from .base import BaseSimilarityEngine

logger = logging.getLogger(__name__)


class NumpySimilarityEngine(BaseSimilarityEngine):
    """
    Pure NumPy similarity search engine.

    Uses brute-force cosine similarity search.
    Suitable for small to medium datasets.

    Pros:
    - No external dependencies
    - Simple and reliable
    - Good for datasets < 5K items

    Cons:
    - O(n) search complexity
    - Slower for large datasets
    """

    def __init__(self, dimension: int):
        """
        Initialize NumPy similarity engine.

        Args:
            dimension: Embedding dimension
        """
        super().__init__(dimension)
        self._embeddings: Optional[np.ndarray] = None

    def build_index(self, embeddings: np.ndarray) -> None:
        """
        Store embeddings for search.

        Args:
            embeddings: numpy array of shape (n_items, embedding_dim)
        """
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be 2D array")

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {embeddings.shape[1]}"
            )

        # L2 normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self._embeddings = embeddings / np.maximum(norms, 1e-10)

        self._num_items = embeddings.shape[0]
        self._index_built = True

        logger.info(f"Built NumPy index with {self._num_items} items")

    def find_similar(
        self,
        query_embedding: np.ndarray,
        k: int,
    ) -> List[Tuple[int, float]]:
        """
        Find k most similar items using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            k: Number of results

        Returns:
            List of (index, similarity_score) tuples, sorted by score descending
        """
        if not self._index_built:
            raise RuntimeError("Index not built. Call build_index first.")

        # L2 normalize query
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm

        # Compute cosine similarities (dot product with normalized vectors)
        similarities = np.dot(self._embeddings, query_embedding)

        # Get top-k indices
        k = min(k, self._num_items)
        top_indices = np.argpartition(similarities, -k)[-k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        # Return as list of tuples
        results = [
            (int(idx), float(similarities[idx]))
            for idx in top_indices
        ]

        return results

    def find_similar_batch(
        self,
        query_embeddings: np.ndarray,
        k: int,
    ) -> List[List[Tuple[int, float]]]:
        """
        Find k most similar items for multiple queries (vectorized).

        Args:
            query_embeddings: Query embedding matrix (n_queries, dim)
            k: Number of results per query

        Returns:
            List of lists of (index, similarity_score) tuples
        """
        if not self._index_built:
            raise RuntimeError("Index not built. Call build_index first.")

        # L2 normalize queries
        norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
        query_embeddings = query_embeddings / np.maximum(norms, 1e-10)

        # Compute all similarities at once
        similarities = np.dot(query_embeddings, self._embeddings.T)

        results = []
        k = min(k, self._num_items)

        for i in range(similarities.shape[0]):
            row = similarities[i]
            top_indices = np.argpartition(row, -k)[-k:]
            top_indices = top_indices[np.argsort(row[top_indices])[::-1]]

            query_results = [
                (int(idx), float(row[idx]))
                for idx in top_indices
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

        Args:
            threshold: Minimum similarity threshold
            max_pairs: Maximum number of pairs to return

        Returns:
            List of (idx1, idx2, similarity) tuples, sorted by similarity descending
        """
        if not self._index_built:
            raise RuntimeError("Index not built. Call build_index first.")

        logger.info(f"Finding all pairs with similarity >= {threshold}...")

        # Compute full similarity matrix
        similarity_matrix = np.dot(self._embeddings, self._embeddings.T)

        # Get upper triangle indices (avoid duplicates and self-similarity)
        rows, cols = np.triu_indices(self._num_items, k=1)

        # Filter by threshold
        similarities = similarity_matrix[rows, cols]
        mask = similarities >= threshold
        filtered_rows = rows[mask]
        filtered_cols = cols[mask]
        filtered_sims = similarities[mask]

        # Sort by similarity descending
        sort_idx = np.argsort(filtered_sims)[::-1]

        # Apply max_pairs limit
        if max_pairs is not None:
            sort_idx = sort_idx[:max_pairs]

        pairs = [
            (int(filtered_rows[i]), int(filtered_cols[i]), float(filtered_sims[i]))
            for i in sort_idx
        ]

        logger.info(f"Found {len(pairs)} pairs above threshold")
        return pairs

    def get_embedding(self, index: int) -> np.ndarray:
        """Get embedding by index."""
        if not self._index_built:
            raise RuntimeError("Index not built.")
        return self._embeddings[index]

    def get_similarity(self, idx1: int, idx2: int) -> float:
        """Get similarity between two items."""
        if not self._index_built:
            raise RuntimeError("Index not built.")
        return float(np.dot(self._embeddings[idx1], self._embeddings[idx2]))


def create_numpy_engine(dimension: int) -> NumpySimilarityEngine:
    """Factory function to create NumPy similarity engine."""
    return NumpySimilarityEngine(dimension=dimension)
