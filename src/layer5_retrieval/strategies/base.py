"""
Base Retrieval Strategy

Abstract base class for retrieval strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from src.models.chunk import Chunk
from src.models.query import QueryPlan
from src.models.retrieval import RetrievalResult, ScoredChunk


class BaseRetrievalStrategy(ABC):
    """
    Abstract base class for retrieval strategies.

    All retrieval implementations must inherit from this class.
    """

    def __init__(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
    ):
        """
        Initialize retrieval strategy.

        Args:
            chunks: List of all chunks
            embeddings: Embedding matrix
        """
        self.chunks = chunks
        self.embeddings = embeddings
        self._chunk_by_id = {c.chunk_id: c for c in chunks}
        self._chunk_by_idx = {i: c for i, c in enumerate(chunks)}

    @abstractmethod
    def retrieve(
        self,
        query: str,
        plan: QueryPlan,
        top_k: int,
    ) -> RetrievalResult:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Query string
            plan: Query plan with filters
            top_k: Maximum results

        Returns:
            RetrievalResult with scored candidates
        """
        pass

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get chunk by ID."""
        return self._chunk_by_id.get(chunk_id)

    def get_chunk_by_index(self, index: int) -> Optional[Chunk]:
        """Get chunk by embedding index."""
        return self._chunk_by_idx.get(index)
