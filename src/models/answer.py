"""
Answer Data Models

Models for generated answers, citations, and evaluation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .chunk import Chunk
    from .retrieval import RetrievalConfidence


class AnswerQuality(str, Enum):
    """Quality assessment of generated answer."""

    EXCELLENT = "excellent"  # All criteria met
    GOOD = "good"  # Most criteria met
    FAIR = "fair"  # Some issues
    POOR = "poor"  # Significant issues
    FAILED = "failed"  # Generation failed


@dataclass
class Citation:
    """
    A citation linking answer content to source chunks.

    Supports numbered reference format [1], [2], etc.
    """

    # Citation identifier (1-indexed)
    index: int

    # Source chunk information
    chunk_id: str
    doc_id: str
    year: int
    category: str

    # Display information
    title: Optional[str] = None
    source_path: Optional[str] = None

    # Relevance to query
    relevance_score: float = 0.0
    year_matched: bool = False

    # Text excerpt
    excerpt: str = ""

    @property
    def reference_tag(self) -> str:
        """Get reference tag like [1], [2]."""
        return f"[{self.index}]"

    @property
    def display_text(self) -> str:
        """Get formatted citation display text."""
        title = self.title or self.doc_id
        return f"{self.reference_tag} {title} ({self.year})"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "index": self.index,
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "year": self.year,
            "category": self.category,
            "title": self.title,
            "source_path": self.source_path,
            "relevance_score": self.relevance_score,
            "year_matched": self.year_matched,
            "excerpt": self.excerpt,
        }

    @classmethod
    def from_chunk(
        cls,
        chunk: "Chunk",
        index: int,
        relevance_score: float = 0.0,
        year_matched: bool = False,
    ) -> "Citation":
        """Create citation from a chunk."""
        return cls(
            index=index,
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            year=chunk.year,
            category=chunk.category,
            title=chunk.title,
            source_path=chunk.source_path,
            relevance_score=relevance_score,
            year_matched=year_matched,
            excerpt=chunk.truncate(200),
        )


@dataclass
class LinkedCitation(Citation):
    """
    Citation with bidirectional linking to answer text.

    Extends Citation with position tracking and usage context
    for interactive citation navigation (like NotebookLM).
    """

    # Position(s) in answer text where this citation is referenced
    answer_positions: List[tuple] = field(default_factory=list)  # [(start, end), ...]

    # Sentence context where citation was used
    usage_contexts: List[str] = field(default_factory=list)

    # Unique ID for UI highlighting
    highlight_id: str = ""

    # Full source text (beyond excerpt)
    full_text: str = ""

    @property
    def usage_count(self) -> int:
        """Number of times this citation is used in the answer."""
        return len(self.answer_positions)

    @property
    def first_position(self) -> Optional[tuple]:
        """Get first position in answer."""
        return self.answer_positions[0] if self.answer_positions else None

    @property
    def primary_context(self) -> str:
        """Get primary usage context."""
        return self.usage_contexts[0] if self.usage_contexts else ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary with linking info."""
        base_dict = super().to_dict()
        base_dict.update({
            "answer_positions": self.answer_positions,
            "usage_contexts": self.usage_contexts,
            "highlight_id": self.highlight_id,
            "usage_count": self.usage_count,
        })
        return base_dict

    @classmethod
    def from_citation(
        cls,
        citation: Citation,
        answer_positions: List[tuple] = None,
        usage_contexts: List[str] = None,
        highlight_id: str = "",
        full_text: str = "",
    ) -> "LinkedCitation":
        """Create LinkedCitation from basic Citation."""
        return cls(
            index=citation.index,
            chunk_id=citation.chunk_id,
            doc_id=citation.doc_id,
            year=citation.year,
            category=citation.category,
            title=citation.title,
            source_path=citation.source_path,
            relevance_score=citation.relevance_score,
            year_matched=citation.year_matched,
            excerpt=citation.excerpt,
            answer_positions=answer_positions or [],
            usage_contexts=usage_contexts or [],
            highlight_id=highlight_id,
            full_text=full_text,
        )


@dataclass
class GenerationStats:
    """Statistics from answer generation."""

    # Timing
    generation_time_ms: float = 0.0
    total_latency_ms: float = 0.0

    # Token counts
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Model info
    model_used: str = ""
    temperature: float = 0.0

    # Context info
    num_source_chunks: int = 0
    context_length: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "generation_time_ms": self.generation_time_ms,
            "total_latency_ms": self.total_latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "model_used": self.model_used,
            "temperature": self.temperature,
            "num_source_chunks": self.num_source_chunks,
            "context_length": self.context_length,
        }


@dataclass
class EnhancedAnswer:
    """
    Complete answer with citations, metadata, and quality assessment.

    The main output type of the MNEME query pipeline.
    """

    # Core answer
    answer: str
    query: str

    # Citations (can be Citation or LinkedCitation)
    citations: List[Citation] = field(default_factory=list)

    # Quick lookup map for citations by index
    citation_map: Dict[int, Citation] = field(default_factory=dict)

    # Confidence assessment
    confidence: str = "good_match"  # RetrievalConfidence value

    # Quality assessment
    quality: AnswerQuality = AnswerQuality.GOOD

    # Timing
    latency_ms: float = 0.0

    # Generation stats
    stats: Optional[GenerationStats] = None

    # Query metadata
    query_type: str = "specific"
    year_filter: Optional[int] = None
    category_filter: Optional[str] = None

    # Source metadata
    num_sources_used: int = 0
    years_covered: List[int] = field(default_factory=list)
    categories_covered: List[str] = field(default_factory=list)

    # Gap information
    coverage_gaps: List[str] = field(default_factory=list)

    # Retrieval context (for evaluation and debugging)
    retrieval_result: Optional[Any] = None  # RetrievalResult object

    # Error handling
    error: Optional[str] = None
    fallback_used: bool = False

    def __post_init__(self):
        """Build citation map after initialization."""
        if self.citations and not self.citation_map:
            self.citation_map = {c.index: c for c in self.citations}

    @property
    def has_citations(self) -> bool:
        """Check if answer has citations."""
        return len(self.citations) > 0

    @property
    def num_citations(self) -> int:
        """Number of citations."""
        return len(self.citations)

    @property
    def year_matched_citations(self) -> List[Citation]:
        """Get citations that match the year filter."""
        return [c for c in self.citations if c.year_matched]

    @property
    def is_successful(self) -> bool:
        """Check if answer generation was successful."""
        return self.error is None and self.quality != AnswerQuality.FAILED

    def get_citation_by_index(self, index: int) -> Optional[Citation]:
        """Get citation by index (1-indexed)."""
        for citation in self.citations:
            if citation.index == index:
                return citation
        return None

    def format_with_citations(self) -> str:
        """Format answer with citation list."""
        lines = [self.answer, "", "Sources:"]
        for citation in self.citations:
            year_marker = " ✓" if citation.year_matched else ""
            lines.append(f"  {citation.display_text}{year_marker}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "answer": self.answer,
            "query": self.query,
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
            "quality": self.quality.value,
            "latency_ms": self.latency_ms,
            "stats": self.stats.to_dict() if self.stats else None,
            "query_type": self.query_type,
            "year_filter": self.year_filter,
            "category_filter": self.category_filter,
            "num_sources_used": self.num_sources_used,
            "years_covered": self.years_covered,
            "categories_covered": self.categories_covered,
            "coverage_gaps": self.coverage_gaps,
            "error": self.error,
            "fallback_used": self.fallback_used,
        }

    @classmethod
    def error_response(cls, query: str, error: str) -> "EnhancedAnswer":
        """Create an error response."""
        return cls(
            answer=f"Unable to generate answer: {error}",
            query=query,
            quality=AnswerQuality.FAILED,
            error=error,
        )

    def __repr__(self) -> str:
        return (
            f"EnhancedAnswer(quality={self.quality.value}, "
            f"citations={self.num_citations}, "
            f"latency={self.latency_ms:.0f}ms)"
        )


@dataclass
class AnswerEvaluation:
    """Evaluation metrics for answer quality."""

    # Relevance scores
    answer_relevance: float = 0.0
    context_relevance: float = 0.0

    # Faithfulness (grounded in sources)
    faithfulness: float = 0.0

    # Citation quality
    citation_accuracy: float = 0.0
    citation_coverage: float = 0.0

    # Year-specific metrics
    year_accuracy: float = 0.0

    # Overall score
    overall_score: float = 0.0

    # Human feedback (if available)
    human_rating: Optional[int] = None
    feedback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "answer_relevance": self.answer_relevance,
            "context_relevance": self.context_relevance,
            "faithfulness": self.faithfulness,
            "citation_accuracy": self.citation_accuracy,
            "citation_coverage": self.citation_coverage,
            "year_accuracy": self.year_accuracy,
            "overall_score": self.overall_score,
            "human_rating": self.human_rating,
            "feedback": self.feedback,
        }
