"""
Semantic Chunking Strategy

LLM-based semantic boundary detection for intelligent chunking.
Alternative to word-count chunking for better semantic coherence.
"""

from typing import List, Optional
import logging
import re

from .base import BaseChunkingStrategy
from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


class SemanticChunking(BaseChunkingStrategy):
    """
    Semantic chunking using topic/concept boundaries.

    Uses sentence embeddings to detect topic shifts and create
    semantically coherent chunks.

    Requires sentence-transformers for embedding generation.
    """

    def __init__(
        self,
        target_size: int = 300,
        min_size: int = 50,
        max_size: int = 600,
        overlap: int = 50,
        similarity_threshold: float = 0.5,
        embedding_model: Optional[str] = None,
    ):
        """
        Initialize semantic chunking.

        Args:
            target_size: Target words per chunk
            min_size: Minimum words for valid chunk
            max_size: Maximum words per chunk
            overlap: Word overlap between chunks
            similarity_threshold: Threshold for detecting topic shifts
            embedding_model: Optional custom embedding model
        """
        super().__init__(target_size, min_size, max_size, overlap)
        self.similarity_threshold = similarity_threshold
        self.embedding_model_name = embedding_model or "all-MiniLM-L6-v2"
        self._model = None

    @property
    def model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.embedding_model_name)
                logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            except ImportError:
                logger.warning("sentence-transformers not installed, using fallback")
                self._model = None
        return self._model

    def chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
    ) -> List[Chunk]:
        """
        Split text into semantically coherent chunks.

        Args:
            text: Full document text
            doc_id: Unique document identifier
            category: Document category
            year: Publication year

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        # If model not available, fall back to sentence-based chunking
        if self.model is None:
            return self._fallback_chunk(text, doc_id, category, year)

        # Split into sentences
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        # Get sentence embeddings
        embeddings = self.model.encode(sentences, show_progress_bar=False)

        # Find semantic breakpoints
        breakpoints = self._find_semantic_breakpoints(sentences, embeddings)

        # Build chunks from breakpoints
        chunks_text = self._build_chunks_from_breakpoints(sentences, breakpoints)

        # Create Chunk objects
        chunks = []
        total_chunks = len(chunks_text)

        for i, chunk_text in enumerate(chunks_text):
            chunk = self.create_chunk(
                text=chunk_text,
                doc_id=doc_id,
                category=category,
                year=year,
                chunk_index=i,
                total_chunks=total_chunks,
                metadata={"chunking_strategy": "semantic"},
            )
            chunks.append(chunk)

        logger.debug(f"Created {len(chunks)} semantic chunks for {doc_id}")
        return chunks

    def _find_semantic_breakpoints(
        self,
        sentences: List[str],
        embeddings,
    ) -> List[int]:
        """
        Find indices where semantic shifts occur.

        Uses cosine similarity between adjacent sentences to
        detect topic boundaries.
        """
        import numpy as np

        if len(sentences) <= 1:
            return []

        breakpoints = []
        current_words = 0

        for i in range(1, len(sentences)):
            # Calculate similarity between current and previous sentence
            similarity = self._cosine_similarity(embeddings[i-1], embeddings[i])

            sentence_words = len(sentences[i].split())
            current_words += len(sentences[i-1].split())

            # Consider breakpoint if:
            # 1. Similarity is low (topic shift)
            # 2. AND we have enough words for a valid chunk
            if similarity < self.similarity_threshold and current_words >= self.min_size:
                breakpoints.append(i)
                current_words = 0

            # Force breakpoint if exceeding max size
            elif current_words + sentence_words > self.max_size:
                breakpoints.append(i)
                current_words = 0

        return breakpoints

    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        dot = np.dot(vec1, vec2)
        norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return float(dot / norm) if norm > 0 else 0.0

    def _build_chunks_from_breakpoints(
        self,
        sentences: List[str],
        breakpoints: List[int],
    ) -> List[str]:
        """Build chunk texts from sentences and breakpoints."""
        chunks = []
        start = 0

        for bp in breakpoints:
            chunk_sentences = sentences[start:bp]
            if chunk_sentences:
                chunk_text = ' '.join(chunk_sentences)
                if self._count_words(chunk_text) >= self.min_size:
                    chunks.append(chunk_text)
            start = bp

        # Handle remaining sentences
        if start < len(sentences):
            chunk_sentences = sentences[start:]
            chunk_text = ' '.join(chunk_sentences)
            if self._count_words(chunk_text) >= self.min_size:
                chunks.append(chunk_text)
            elif chunks:
                # Merge with previous if too small
                chunks[-1] = chunks[-1] + ' ' + chunk_text

        return chunks

    def _fallback_chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
    ) -> List[Chunk]:
        """Fallback to simple sentence-based chunking."""
        from .word_count import WordCountChunking

        logger.warning("Using word-count fallback for semantic chunking")
        fallback = WordCountChunking(
            target_size=self.target_size,
            min_size=self.min_size,
            max_size=self.max_size,
            overlap=self.overlap,
        )
        return fallback.chunk(text, doc_id, category, year)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Clean text first
        text = re.sub(r'\s+', ' ', text).strip()

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


def create_semantic_chunker(
    target_size: int = 300,
    similarity_threshold: float = 0.5,
    embedding_model: Optional[str] = None,
) -> SemanticChunking:
    """Factory function to create semantic chunker."""
    return SemanticChunking(
        target_size=target_size,
        similarity_threshold=similarity_threshold,
        embedding_model=embedding_model,
    )
