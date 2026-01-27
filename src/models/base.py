"""
Base Protocols and Interfaces for MNEME Architecture.

Defines abstract protocols that enable alternative implementations
for each layer of the MNEME system.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Tuple, Optional, Any, runtime_checkable
import numpy as np

# Forward references for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .chunk import Chunk
    from .query import QueryPlan
    from .retrieval import RetrievalResult


@runtime_checkable
class ChunkingStrategy(Protocol):
    """Protocol for document chunking strategies.

    Implementations:
    - word_count.py: Basic word-count based chunking (300 words)
    - semantic.py: LLM-based semantic boundary detection
    - hierarchical.py: Nested hierarchical chunking
    """

    def chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
    ) -> List["Chunk"]:
        """Split text into chunks with metadata.

        Args:
            text: Full document text
            doc_id: Unique document identifier
            category: Document category (e.g., 'ai_safety', 'capabilities')
            year: Publication year

        Returns:
            List of Chunk objects
        """
        ...


@runtime_checkable
class EmbeddingEngine(Protocol):
    """Protocol for embedding generation engines.

    Implementations:
    - sentence_transformer.py: all-MiniLM-L6-v2 (default)
    - openai.py: OpenAI text-embedding-ada-002
    """

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        ...

    def generate_embeddings(self, chunks: List["Chunk"]) -> np.ndarray:
        """Generate embeddings for all chunks.

        Args:
            chunks: List of Chunk objects

        Returns:
            numpy array of shape (n_chunks, embedding_dim)
        """
        ...

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a query string to embedding.

        Args:
            query: Query string

        Returns:
            1D numpy array of embedding
        """
        ...


@runtime_checkable
class SimilarityEngine(Protocol):
    """Protocol for similarity search engines.

    Implementations:
    - numpy_engine.py: Pure NumPy (baseline, small datasets)
    - faiss_engine.py: FAISS (fast, scalable, production)
    """

    def build_index(self, embeddings: np.ndarray) -> None:
        """Build search index from embeddings.

        Args:
            embeddings: numpy array of shape (n_items, embedding_dim)
        """
        ...

    def find_similar(
        self,
        query_embedding: np.ndarray,
        k: int,
    ) -> List[Tuple[int, float]]:
        """Find k most similar items.

        Args:
            query_embedding: Query embedding vector
            k: Number of results

        Returns:
            List of (index, similarity_score) tuples
        """
        ...


@runtime_checkable
class RetrievalStrategy(Protocol):
    """Protocol for retrieval strategies.

    Implementations:
    - vector_only.py: Pure vector similarity
    - bm25_only.py: Pure BM25 keyword search
    - hybrid_rrf.py: Hybrid RRF (vector + BM25)
    """

    def retrieve(
        self,
        query: str,
        plan: "QueryPlan",
        top_k: int,
    ) -> "RetrievalResult":
        """Retrieve relevant documents for a query.

        Args:
            query: Query string
            plan: Parsed query plan with filters
            top_k: Maximum number of results

        Returns:
            RetrievalResult with scored candidates
        """
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers.

    Implementations:
    - gemini.py: Google Gemini integration
    - openai.py: OpenAI GPT integration
    """

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text completion.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum response tokens

        Returns:
            Generated text
        """
        ...

    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        ...


class BaseChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""

    @abstractmethod
    def chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
    ) -> List["Chunk"]:
        """Split text into chunks."""
        pass


class BaseEmbeddingEngine(ABC):
    """Abstract base class for embedding engines."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass

    @abstractmethod
    def generate_embeddings(self, chunks: List["Chunk"]) -> np.ndarray:
        """Generate embeddings for chunks."""
        pass

    @abstractmethod
    def encode_query(self, query: str) -> np.ndarray:
        """Encode query to embedding."""
        pass


class BaseSimilarityEngine(ABC):
    """Abstract base class for similarity engines."""

    @abstractmethod
    def build_index(self, embeddings: np.ndarray) -> None:
        """Build search index."""
        pass

    @abstractmethod
    def find_similar(
        self,
        query_embedding: np.ndarray,
        k: int,
    ) -> List[Tuple[int, float]]:
        """Find similar items."""
        pass


class BaseRetrievalStrategy(ABC):
    """Abstract base class for retrieval strategies."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        plan: "QueryPlan",
        top_k: int,
    ) -> "RetrievalResult":
        """Retrieve relevant documents."""
        pass


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text completion."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check provider availability."""
        pass
