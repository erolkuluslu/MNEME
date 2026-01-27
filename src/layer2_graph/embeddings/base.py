"""
Base Embedding Engine

Abstract base class for all embedding implementations.
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np

from src.models.chunk import Chunk


class BaseEmbeddingEngine(ABC):
    """
    Abstract base class for embedding engines.

    All embedding implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(self, model_name: str, dimension: int):
        """
        Initialize embedding engine.

        Args:
            model_name: Name/path of the embedding model
            dimension: Embedding dimension
        """
        self.model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension

    @abstractmethod
    def generate_embeddings(
        self,
        chunks: List[Chunk],
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Generate embeddings for all chunks.

        Args:
            chunks: List of Chunk objects
            show_progress: Show progress bar

        Returns:
            numpy array of shape (n_chunks, embedding_dim)
        """
        pass

    @abstractmethod
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a query string to embedding.

        Args:
            query: Query string

        Returns:
            1D numpy array of embedding
        """
        pass

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of text strings.

        Args:
            texts: List of text strings

        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        embeddings = []
        for text in texts:
            emb = self.encode_query(text)
            embeddings.append(emb)
        return np.array(embeddings)

    def is_available(self) -> bool:
        """Check if the embedding model is available."""
        return True
