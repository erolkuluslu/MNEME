"""
Sentence Transformer Embedding Engine

Uses sentence-transformers library for generating embeddings.
Default model: all-MiniLM-L6-v2 (384 dimensions)
"""

from typing import List, Optional
import logging
import numpy as np

from .base import BaseEmbeddingEngine
from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


class SentenceTransformerEngine(BaseEmbeddingEngine):
    """
    Embedding engine using sentence-transformers.

    Default model: all-MiniLM-L6-v2
    - 384 dimensions
    - Fast inference
    - Good quality for semantic similarity

    Alternative models:
    - all-mpnet-base-v2: Higher quality, 768 dims, slower
    - paraphrase-MiniLM-L6-v2: Optimized for paraphrase
    """

    # Known model dimensions
    MODEL_DIMENSIONS = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "paraphrase-MiniLM-L6-v2": 384,
        "multi-qa-MiniLM-L6-cos-v1": 384,
        "all-distilroberta-v1": 768,
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32,
    ):
        """
        Initialize sentence transformer engine.

        Args:
            model_name: Model name or path
            device: Device to use ('cuda', 'cpu', or None for auto)
            batch_size: Batch size for encoding
        """
        dimension = self.MODEL_DIMENSIONS.get(model_name, 384)
        super().__init__(model_name, dimension)

        self.device = device
        self.batch_size = batch_size
        self._model = None
        self._available = None

    @property
    def model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name, device=self.device)
                self._dimension = self._model.get_sentence_embedding_dimension()
                self._available = True
                logger.info(
                    f"Loaded embedding model: {self.model_name} "
                    f"(dim={self._dimension}, device={self._model.device})"
                )
            except ImportError:
                logger.error("sentence-transformers not installed")
                self._available = False
                raise ImportError(
                    "sentence-transformers is required. "
                    "Install with: pip install sentence-transformers"
                )
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self._available = False
                raise

        return self._model

    def is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        if self._available is not None:
            return self._available

        try:
            import sentence_transformers
            self._available = True
        except ImportError:
            self._available = False

        return self._available

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
        if not chunks:
            return np.array([])

        texts = [chunk.text for chunk in chunks]

        logger.info(f"Generating embeddings for {len(texts)} chunks...")

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2 normalize for cosine similarity
        )

        logger.info(f"Generated embeddings with shape {embeddings.shape}")
        return embeddings

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a query string to embedding.

        Args:
            query: Query string

        Returns:
            1D numpy array of embedding
        """
        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding

    def encode_texts(
        self,
        texts: List[str],
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode a list of text strings.

        Args:
            texts: List of text strings
            show_progress: Show progress bar

        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])

        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )


def create_sentence_transformer_engine(
    model_name: str = "all-MiniLM-L6-v2",
    device: Optional[str] = None,
) -> SentenceTransformerEngine:
    """Factory function to create sentence transformer engine."""
    return SentenceTransformerEngine(model_name=model_name, device=device)
