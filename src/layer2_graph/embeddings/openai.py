"""
OpenAI Embedding Engine

Uses OpenAI's embedding API for generating embeddings.
Requires OPENAI_API_KEY environment variable.
"""

from typing import List, Optional
import logging
import os
import numpy as np

from .base import BaseEmbeddingEngine
from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


class OpenAIEmbeddingEngine(BaseEmbeddingEngine):
    """
    Embedding engine using OpenAI's embedding API.

    Models:
    - text-embedding-3-small: 1536 dims, cheaper
    - text-embedding-3-large: 3072 dims, higher quality
    - text-embedding-ada-002: 1536 dims (legacy)
    """

    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        batch_size: int = 100,
    ):
        """
        Initialize OpenAI embedding engine.

        Args:
            model_name: OpenAI embedding model name
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            batch_size: Batch size for API calls
        """
        dimension = self.MODEL_DIMENSIONS.get(model_name, 1536)
        super().__init__(model_name, dimension)

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.batch_size = batch_size
        self._client = None

    @property
    def client(self):
        """Lazy load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                if not self.api_key:
                    raise ValueError(
                        "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
                    )

                self._client = OpenAI(api_key=self.api_key)
                logger.info(f"Initialized OpenAI client for model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "openai package is required. Install with: pip install openai"
                )

        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            import openai
            return self.api_key is not None
        except ImportError:
            return False

    def generate_embeddings(
        self,
        chunks: List[Chunk],
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Generate embeddings for all chunks.

        Args:
            chunks: List of Chunk objects
            show_progress: Show progress (logged)

        Returns:
            numpy array of shape (n_chunks, embedding_dim)
        """
        if not chunks:
            return np.array([])

        texts = [chunk.text for chunk in chunks]
        return self._encode_batch(texts, show_progress)

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a query string to embedding.

        Args:
            query: Query string

        Returns:
            1D numpy array of embedding
        """
        response = self.client.embeddings.create(
            model=self.model_name,
            input=query,
        )
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)

    def encode_texts(
        self,
        texts: List[str],
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode a list of text strings.

        Args:
            texts: List of text strings
            show_progress: Show progress

        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])

        return self._encode_batch(texts, show_progress)

    def _encode_batch(
        self,
        texts: List[str],
        show_progress: bool = True,
    ) -> np.ndarray:
        """Encode texts in batches."""
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1

            if show_progress:
                logger.info(f"Encoding batch {batch_num}/{total_batches}...")

            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch,
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        embeddings = np.array(all_embeddings, dtype=np.float32)

        # L2 normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / np.maximum(norms, 1e-10)

        logger.info(f"Generated embeddings with shape {embeddings.shape}")
        return embeddings


def create_openai_embedding_engine(
    model_name: str = "text-embedding-3-small",
    api_key: Optional[str] = None,
) -> OpenAIEmbeddingEngine:
    """Factory function to create OpenAI embedding engine."""
    return OpenAIEmbeddingEngine(model_name=model_name, api_key=api_key)
