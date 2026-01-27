"""
Base Similarity Engine

Abstract base class for similarity search implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np


class BaseSimilarityEngine(ABC):
    """
    Abstract base class for similarity engines.

    All similarity search implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(self, dimension: int):
        """
        Initialize similarity engine.

        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
        self._index_built = False
        self._num_items = 0

    @property
    def is_built(self) -> bool:
        """Check if index has been built."""
        return self._index_built

    @property
    def num_items(self) -> int:
        """Number of items in index."""
        return self._num_items

    @abstractmethod
    def build_index(self, embeddings: np.ndarray) -> None:
        """
        Build search index from embeddings.

        Args:
            embeddings: numpy array of shape (n_items, embedding_dim)
        """
        pass

    @abstractmethod
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
        pass

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
        results = []
        for query in query_embeddings:
            results.append(self.find_similar(query, k))
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
            List of (idx1, idx2, similarity) tuples
        """
        raise NotImplementedError("find_all_pairs not implemented for this engine")
