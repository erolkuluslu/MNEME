"""
Base Chunking Strategy

Abstract base class for all chunking implementations.
"""

from abc import ABC, abstractmethod
from typing import List

from src.models.chunk import Chunk


class BaseChunkingStrategy(ABC):
    """
    Abstract base class for chunking strategies.

    All chunking implementations must inherit from this class
    and implement the chunk() method.
    """

    def __init__(
        self,
        target_size: int = 300,
        min_size: int = 50,
        max_size: int = 600,
        overlap: int = 50,
    ):
        """
        Initialize chunking strategy.

        Args:
            target_size: Target words per chunk
            min_size: Minimum words for valid chunk
            max_size: Maximum words per chunk
            overlap: Word overlap between chunks
        """
        self.target_size = target_size
        self.min_size = min_size
        self.max_size = max_size
        self.overlap = overlap

    @abstractmethod
    def chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
    ) -> List[Chunk]:
        """
        Split text into chunks.

        Args:
            text: Full document text
            doc_id: Unique document identifier
            category: Document category
            year: Publication year

        Returns:
            List of Chunk objects
        """
        pass

    def generate_chunk_id(self, doc_id: str, index: int) -> str:
        """Generate unique chunk ID."""
        return f"{doc_id}_chunk_{index}"

    def create_chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
        chunk_index: int,
        total_chunks: int,
        **kwargs,
    ) -> Chunk:
        """Create a Chunk object with standard fields."""
        chunk_id = self.generate_chunk_id(doc_id, chunk_index)
        return Chunk(
            text=text,
            chunk_id=chunk_id,
            doc_id=doc_id,
            category=category,
            year=year,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            **kwargs,
        )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    def _validate_chunk(self, text: str) -> bool:
        """Check if chunk meets size requirements."""
        word_count = self._count_words(text)
        return self.min_size <= word_count <= self.max_size
