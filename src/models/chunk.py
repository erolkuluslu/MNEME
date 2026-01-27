"""
Chunk Data Model

Represents a text chunk with metadata for the MNEME RAG system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import hashlib


@dataclass
class Chunk:
    """
    A text chunk with associated metadata.

    Represents a segment of a document with rich metadata for
    retrieval, filtering, and citation generation.
    """

    # Core content
    text: str
    chunk_id: str

    # Document metadata
    doc_id: str
    category: str
    year: int

    # Position in document
    chunk_index: int = 0
    total_chunks: int = 1

    # Optional metadata
    title: Optional[str] = None
    source_path: Optional[str] = None
    word_count: int = 0
    char_count: int = 0

    # Hierarchical structure (for hierarchical chunking)
    parent_chunk_id: Optional[str] = None
    level: int = 0  # 0 = base level, 1+ = summary levels

    # Processing metadata
    embedding_index: Optional[int] = None  # Index in embeddings array
    hash: Optional[str] = None  # Content hash for deduplication

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate derived fields after initialization."""
        if self.word_count == 0:
            self.word_count = len(self.text.split())

        if self.char_count == 0:
            self.char_count = len(self.text)

        if self.hash is None:
            self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute content hash for deduplication."""
        content = f"{self.doc_id}:{self.chunk_index}:{self.text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    @property
    def citation_id(self) -> str:
        """Generate a citation-friendly identifier."""
        return f"{self.doc_id}:{self.chunk_index}"

    @property
    def display_title(self) -> str:
        """Return display title for citations."""
        if self.title:
            return self.title
        return f"{self.doc_id} ({self.year})"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize chunk to dictionary."""
        return {
            "text": self.text,
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "category": self.category,
            "year": self.year,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "title": self.title,
            "source_path": self.source_path,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "parent_chunk_id": self.parent_chunk_id,
            "level": self.level,
            "embedding_index": self.embedding_index,
            "hash": self.hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """Deserialize chunk from dictionary."""
        return cls(
            text=data["text"],
            chunk_id=data["chunk_id"],
            doc_id=data["doc_id"],
            category=data["category"],
            year=data["year"],
            chunk_index=data.get("chunk_index", 0),
            total_chunks=data.get("total_chunks", 1),
            title=data.get("title"),
            source_path=data.get("source_path"),
            word_count=data.get("word_count", 0),
            char_count=data.get("char_count", 0),
            parent_chunk_id=data.get("parent_chunk_id"),
            level=data.get("level", 0),
            embedding_index=data.get("embedding_index"),
            hash=data.get("hash"),
            metadata=data.get("metadata", {}),
        )

    def truncate(self, max_chars: int = 500) -> str:
        """Return truncated text for display."""
        if len(self.text) <= max_chars:
            return self.text
        return self.text[:max_chars] + "..."

    def __repr__(self) -> str:
        return (
            f"Chunk(id={self.chunk_id}, doc={self.doc_id}, "
            f"year={self.year}, words={self.word_count})"
        )


@dataclass
class ChunkBatch:
    """Collection of chunks with aggregate statistics."""

    chunks: List[Chunk] = field(default_factory=list)

    @property
    def total_chunks(self) -> int:
        """Total number of chunks."""
        return len(self.chunks)

    @property
    def total_words(self) -> int:
        """Total word count across all chunks."""
        return sum(c.word_count for c in self.chunks)

    @property
    def unique_documents(self) -> int:
        """Number of unique source documents."""
        return len(set(c.doc_id for c in self.chunks))

    @property
    def unique_years(self) -> List[int]:
        """List of unique years in batch."""
        return sorted(set(c.year for c in self.chunks))

    @property
    def unique_categories(self) -> List[str]:
        """List of unique categories in batch."""
        return sorted(set(c.category for c in self.chunks))

    def filter_by_year(self, year: int) -> "ChunkBatch":
        """Filter chunks by year."""
        return ChunkBatch(chunks=[c for c in self.chunks if c.year == year])

    def filter_by_category(self, category: str) -> "ChunkBatch":
        """Filter chunks by category."""
        return ChunkBatch(chunks=[c for c in self.chunks if c.category == category])

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        return {
            "total_chunks": self.total_chunks,
            "total_words": self.total_words,
            "unique_documents": self.unique_documents,
            "years": self.unique_years,
            "categories": self.unique_categories,
            "avg_words_per_chunk": self.total_words / self.total_chunks if self.chunks else 0,
        }
