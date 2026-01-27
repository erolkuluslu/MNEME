"""
Context Builder Module

Assembles context for answer generation from retrieval results.
Enhanced version includes community summaries for narrative queries.
"""

from typing import List, Optional, Dict, Any
import logging

from src.models.chunk import Chunk
from src.models.query import QueryPlan, QueryType, QueryIntent
from src.models.retrieval import RetrievalResult, ScoredChunk

logger = logging.getLogger(__name__)

# Keywords that indicate narrative/exploratory queries
NARRATIVE_KEYWORDS = [
    'overview', 'summarize', 'describe', 'explain', 'who am i',
    'what do i know', 'tell me about', 'bird', 'big picture',
    'across', 'themes', 'patterns', 'synthesis', 'comprehensive',
]


class ContextBuilder:
    """
    Builds context for LLM answer generation.

    Assembles retrieved chunks into a coherent context,
    handling ordering, deduplication, and formatting.

    Enhanced: Includes community summaries for narrative/exploratory queries,
    providing bird's-eye view alongside detailed sources.
    """

    def __init__(
        self,
        max_context_length: int = 8000,
        chunk_separator: str = "\n\n---\n\n",
        include_metadata: bool = True,
        include_community_summaries: bool = True,
    ):
        """
        Initialize context builder.

        Args:
            max_context_length: Maximum context characters
            chunk_separator: Separator between chunks
            include_metadata: Include chunk metadata in context
            include_community_summaries: Include summaries for narrative queries
        """
        self.max_context_length = max_context_length
        self.chunk_separator = chunk_separator
        self.include_metadata = include_metadata
        self.include_community_summaries = include_community_summaries

    def _is_narrative_query(self, plan: QueryPlan) -> bool:
        """Check if query is narrative/exploratory."""
        NARRATIVE_TYPES = {QueryType.SYNTHESIS, QueryType.EXPLORATORY}
        if plan.query_type in NARRATIVE_TYPES:
            return True
        if plan.intent == QueryIntent.EXPLANATORY:
            return True
        query_lower = plan.original_query.lower()
        return any(kw in query_lower for kw in NARRATIVE_KEYWORDS)

    def _format_community_summaries(self, summaries: Dict[int, str]) -> str:
        """Format community summaries as context header."""
        if not summaries:
            return ""

        lines = [
            "=" * 60,
            "HIGH-LEVEL OVERVIEW (Topic Clusters)",
            "=" * 60,
            "",
        ]

        for community_id, summary in sorted(summaries.items()):
            lines.append(f"[Cluster {community_id}]")
            lines.append(summary.strip())
            lines.append("")

        lines.extend([
            "=" * 60,
            "DETAILED SOURCES",
            "=" * 60,
            "",
        ])

        return "\n".join(lines)

    def build_context(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> str:
        """
        Build context string from retrieval result.

        CRITICAL: Year-matched chunks are NEVER truncated.
        Truncation only applies to other-year chunks.

        Enhanced: For narrative queries, prepends community summaries
        to provide a bird's-eye view before detailed sources.

        Args:
            result: Retrieval result with scored chunks
            plan: Query plan

        Returns:
            Formatted context string
        """
        if not result.candidates:
            return ""

        context_parts = []

        # For narrative queries, prepend community summaries if available
        if self.include_community_summaries and self._is_narrative_query(plan):
            # Check if result has community summaries (CommunityAwareRetrievalResult)
            summaries = getattr(result, 'community_summaries', None)
            if summaries:
                summary_context = self._format_community_summaries(summaries)
                if summary_context:
                    context_parts.append(summary_context)
                    logger.debug(f"Added {len(summaries)} community summaries to context")

        # Order chunks (year-matched first)
        ordered_chunks = self._order_chunks(result.candidates, plan)

        # Track which chunks are included for proper indexing
        self._included_chunks = []

        # Format chunks with year-matched protection
        formatted_chunks = []
        total_length = 0

        # CRITICAL FIX: Ensure year-matched chunks are included first and NOT truncated
        # Separate year-matched and other chunks
        year_matched_chunks = [c for c in ordered_chunks if c.year_matched and plan.year_filter is not None]
        other_chunks = [c for c in ordered_chunks if c not in year_matched_chunks]
        
        # 1. Add ALL year-matched chunks first (bypass length limit for these if needed, or strictly prioritize)
        for i, scored_chunk in enumerate(year_matched_chunks):
             formatted = self._format_chunk(scored_chunk, i + 1)
             formatted_chunks.append(formatted)
             total_length += len(formatted)
             self._included_chunks.append(scored_chunk)
             
        # 2. Add other chunks only if space remains
        start_index = len(year_matched_chunks) + 1
        for i, scored_chunk in enumerate(other_chunks):
            formatted = self._format_chunk(scored_chunk, start_index + i)
            if total_length + len(formatted) <= self.max_context_length:
                formatted_chunks.append(formatted)
                total_length += len(formatted)
                self._included_chunks.append(scored_chunk)
            else:
                logger.debug(f"Context truncated at chunk {start_index+i}")
                break

        chunk_context = self.chunk_separator.join(formatted_chunks)
        context_parts.append(chunk_context)

        # Combine all context parts
        context = "\n".join(context_parts)

        logger.debug(
            f"Built context with {len(formatted_chunks)} chunks, "
            f"{len(context)} chars"
        )

        return context

    def _order_chunks(
        self,
        candidates: List[ScoredChunk],
        plan: QueryPlan,
    ) -> List[ScoredChunk]:
        """Order chunks for context assembly."""
        # Prioritize year-matched chunks first
        if plan.year_filter:
            year_matched = [c for c in candidates if c.year_matched]
            other = [c for c in candidates if not c.year_matched]

            # Keep score order within each group
            return year_matched + other

        return candidates

    def _format_chunk(
        self,
        scored_chunk: ScoredChunk,
        index: int,
    ) -> str:
        """Format a single chunk for context."""
        chunk = scored_chunk.chunk

        if self.include_metadata:
            header = f"[{index}] Source: {chunk.doc_id} | Year: {chunk.year} | Category: {chunk.category}"
            return f"{header}\n{chunk.text}"
        else:
            return f"[{index}] {chunk.text}"

    def build_indexed_context(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> tuple:
        """
        Build context with index mapping.

        CRITICAL: Index map only contains chunks that are actually in the context.

        Returns:
            Tuple of (context_string, index_to_chunk_mapping)
        """
        context = self.build_context(result, plan)

        # Build index mapping for chunks actually included in context
        index_map = {}

        # _included_chunks is set by build_context
        if hasattr(self, "_included_chunks"):
            for i, scored_chunk in enumerate(self._included_chunks):
                index_map[i + 1] = scored_chunk.chunk
        else:
            # Fallback for when build_context wasn't called first
            for i, scored_chunk in enumerate(result.candidates):
                index_map[i + 1] = scored_chunk.chunk

        return context, index_map

    def get_valid_citation_indices(
        self,
        result: RetrievalResult,
        plan: QueryPlan,
    ) -> List[int]:
        """
        Get list of valid citation indices.

        For year-strict mode, only year-matched chunks are valid.
        CRITICAL: Only returns indices for chunks that would be in the context.
        """
        # Get the chunks that are actually included in the context
        if not hasattr(self, "_included_chunks"):
             # If context wasn't built yet, we can't know valid indices reliably
             # So we simulate the build to get included chunks
             self.build_context(result, plan)
             
        included_chunks = self._included_chunks

        if plan.filters.require_year_match and plan.year_filter:
            # Only year-matched chunks are valid citations
            return [
                i + 1 for i, chunk in enumerate(included_chunks)
                if chunk.year_matched
            ]
        else:
            return list(range(1, len(included_chunks) + 1))


def create_context_builder(
    max_context_length: int = 8000,
) -> ContextBuilder:
    """Factory function to create context builder."""
    return ContextBuilder(max_context_length=max_context_length)
