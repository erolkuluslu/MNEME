"""
Hierarchical Chunking Strategy

Creates nested hierarchical chunks for multi-level retrieval.
Supports RAPTOR-style tree-based summarization.
"""

from typing import List, Optional, Dict
import logging

from .base import BaseChunkingStrategy
from .word_count import WordCountChunking
from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


class HierarchicalChunking(BaseChunkingStrategy):
    """
    Hierarchical chunking with multiple granularity levels.

    Creates a tree of chunks where:
    - Level 0: Base chunks (word-count based)
    - Level 1: Summary of 2-4 base chunks
    - Level 2: Summary of level 1 summaries
    - etc.

    Useful for RAPTOR-style retrieval where different granularities
    may be relevant for different query types.
    """

    def __init__(
        self,
        target_size: int = 300,
        min_size: int = 50,
        max_size: int = 600,
        overlap: int = 50,
        num_levels: int = 2,
        chunks_per_summary: int = 3,
        summary_provider=None,
    ):
        """
        Initialize hierarchical chunking.

        Args:
            target_size: Target words per base chunk
            min_size: Minimum words for valid chunk
            max_size: Maximum words per chunk
            overlap: Word overlap between chunks
            num_levels: Number of hierarchy levels (1 = base only)
            chunks_per_summary: Chunks to combine per summary
            summary_provider: Optional LLM provider for summaries
        """
        super().__init__(target_size, min_size, max_size, overlap)
        self.num_levels = num_levels
        self.chunks_per_summary = chunks_per_summary
        self.summary_provider = summary_provider

        # Use word-count chunking for base level
        self.base_chunker = WordCountChunking(
            target_size=target_size,
            min_size=min_size,
            max_size=max_size,
            overlap=overlap,
        )

    def chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
    ) -> List[Chunk]:
        """
        Create hierarchical chunks.

        Args:
            text: Full document text
            doc_id: Unique document identifier
            category: Document category
            year: Publication year

        Returns:
            List of Chunk objects at all hierarchy levels
        """
        if not text or not text.strip():
            return []

        # Create base level chunks
        base_chunks = self.base_chunker.chunk(text, doc_id, category, year)
        if not base_chunks:
            return []

        all_chunks = list(base_chunks)

        # Create higher levels
        current_level_chunks = base_chunks
        for level in range(1, self.num_levels):
            higher_chunks = self._create_summary_level(
                current_level_chunks,
                doc_id,
                category,
                year,
                level,
            )
            if higher_chunks:
                all_chunks.extend(higher_chunks)
                current_level_chunks = higher_chunks
            else:
                break

        # Update parent references
        self._link_hierarchy(all_chunks)

        logger.debug(
            f"Created {len(all_chunks)} hierarchical chunks "
            f"({len(base_chunks)} base, {len(all_chunks) - len(base_chunks)} summary) "
            f"for {doc_id}"
        )
        return all_chunks

    def _create_summary_level(
        self,
        lower_chunks: List[Chunk],
        doc_id: str,
        category: str,
        year: int,
        level: int,
    ) -> List[Chunk]:
        """Create summary chunks from lower level chunks."""
        if len(lower_chunks) < 2:
            return []

        summary_chunks = []
        chunk_groups = self._group_chunks(lower_chunks, self.chunks_per_summary)

        for i, group in enumerate(chunk_groups):
            # Create summary text
            if self.summary_provider:
                summary_text = self._generate_summary(group)
            else:
                # Fallback: concatenate first sentences
                summary_text = self._create_fallback_summary(group)

            chunk_id = f"{doc_id}_L{level}_chunk_{i}"
            chunk = Chunk(
                text=summary_text,
                chunk_id=chunk_id,
                doc_id=doc_id,
                category=category,
                year=year,
                chunk_index=i,
                total_chunks=len(chunk_groups),
                level=level,
                metadata={
                    "child_ids": [c.chunk_id for c in group],
                    "is_summary": True,
                },
            )
            summary_chunks.append(chunk)

        return summary_chunks

    def _group_chunks(
        self,
        chunks: List[Chunk],
        group_size: int,
    ) -> List[List[Chunk]]:
        """Group chunks into batches for summarization."""
        groups = []
        for i in range(0, len(chunks), group_size):
            group = chunks[i:i + group_size]
            groups.append(group)
        return groups

    def _generate_summary(self, chunks: List[Chunk]) -> str:
        """Generate summary using LLM provider."""
        combined_text = "\n\n".join(c.text for c in chunks)
        prompt = f"""Summarize the following text in a concise paragraph that captures the main points:

{combined_text}

Summary:"""

        try:
            summary = self.summary_provider.generate(
                prompt,
                temperature=0.3,
                max_tokens=500,
            )
            return summary.strip()
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return self._create_fallback_summary(chunks)

    def _create_fallback_summary(self, chunks: List[Chunk]) -> str:
        """Create simple summary without LLM."""
        # Take first 1-2 sentences from each chunk
        summaries = []
        for chunk in chunks:
            sentences = chunk.text.split('. ')
            summary = '. '.join(sentences[:2])
            if not summary.endswith('.'):
                summary += '.'
            summaries.append(summary)
        return ' '.join(summaries)

    def _link_hierarchy(self, chunks: List[Chunk]) -> None:
        """Link parent-child relationships in hierarchy."""
        # Build lookup by ID
        chunk_by_id = {c.chunk_id: c for c in chunks}

        for chunk in chunks:
            if chunk.metadata.get("child_ids"):
                for child_id in chunk.metadata["child_ids"]:
                    if child_id in chunk_by_id:
                        chunk_by_id[child_id].parent_chunk_id = chunk.chunk_id

    def get_base_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Get only base level (level 0) chunks."""
        return [c for c in chunks if c.level == 0]

    def get_summary_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Get only summary level (level > 0) chunks."""
        return [c for c in chunks if c.level > 0]

    def get_chunks_by_level(
        self,
        chunks: List[Chunk],
        level: int,
    ) -> List[Chunk]:
        """Get chunks at a specific level."""
        return [c for c in chunks if c.level == level]


def create_hierarchical_chunker(
    target_size: int = 300,
    num_levels: int = 2,
    summary_provider=None,
) -> HierarchicalChunking:
    """Factory function to create hierarchical chunker."""
    return HierarchicalChunking(
        target_size=target_size,
        num_levels=num_levels,
        summary_provider=summary_provider,
    )
