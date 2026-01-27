"""
Hierarchical Summaries Module

Implements RAPTOR-style hierarchical summarization for communities.
"""

from typing import List, Dict, Optional
import logging

from src.models.chunk import Chunk
from src.models.graph import Community

logger = logging.getLogger(__name__)


class CommunitySummarizer:
    """
    Creates hierarchical summaries for communities.

    Implements RAPTOR-style summarization where each community
    gets a summary that can be used for high-level retrieval.
    """

    def __init__(
        self,
        llm_provider=None,
        max_chunks_per_summary: int = 10,
        max_summary_length: int = 500,
    ):
        """
        Initialize summarizer.

        Args:
            llm_provider: LLM for generating summaries
            max_chunks_per_summary: Max chunks to include in summary prompt
            max_summary_length: Maximum summary token length
        """
        self.llm_provider = llm_provider
        self.max_chunks_per_summary = max_chunks_per_summary
        self.max_summary_length = max_summary_length

    def summarize_communities(
        self,
        communities: List[Community],
        chunks: List[Chunk],
    ) -> Dict[int, str]:
        """
        Generate summaries for all communities.

        Args:
            communities: List of communities
            chunks: All chunks in the corpus

        Returns:
            Dict mapping community_id -> summary
        """
        logger.info(f"Generating summaries for {len(communities)} communities...")

        # Build chunk lookup
        chunk_by_id = {c.chunk_id: c for c in chunks}

        summaries = {}

        for community in communities:
            summary = self._summarize_community(community, chunk_by_id)
            summaries[community.community_id] = summary
            community.summary = summary

        logger.info(f"Generated {len(summaries)} community summaries")
        return summaries

    def _summarize_community(
        self,
        community: Community,
        chunk_by_id: Dict[str, Chunk],
    ) -> str:
        """Generate summary for a single community."""
        # Get chunks in this community
        community_chunks = [
            chunk_by_id[chunk_id]
            for chunk_id in community.member_ids
            if chunk_id in chunk_by_id
        ]

        if not community_chunks:
            return ""

        # Sort by relevance (hubs first if available)
        if community.hub_ids:
            hub_set = set(community.hub_ids)
            community_chunks.sort(
                key=lambda c: (c.chunk_id in hub_set, c.word_count),
                reverse=True,
            )

        # Limit chunks
        selected_chunks = community_chunks[:self.max_chunks_per_summary]

        # Generate summary
        if self.llm_provider:
            return self._generate_llm_summary(selected_chunks, community)
        else:
            return self._generate_extractive_summary(selected_chunks, community)

    def _generate_llm_summary(
        self,
        chunks: List[Chunk],
        community: Community,
    ) -> str:
        """Generate abstractive summary using LLM."""
        # Combine chunk texts
        combined_text = "\n\n".join(
            f"[{c.year}] {c.text[:500]}" for c in chunks
        )

        prompt = f"""Summarize the following collection of related text passages into a coherent summary that captures the main themes, findings, and relationships.

Context: These passages belong to a community focused on "{community.dominant_category or 'general'}" topics, primarily from {community.dominant_year or 'various years'}.

Passages:
{combined_text}

Provide a concise summary (2-3 paragraphs) that:
1. Identifies the main themes and topics
2. Highlights key findings or concepts
3. Notes any temporal evolution if applicable

Summary:"""

        try:
            summary = self.llm_provider.generate(
                prompt,
                temperature=0.3,
                max_tokens=self.max_summary_length,
            )
            return summary.strip()
        except Exception as e:
            logger.warning(f"LLM summary failed: {e}")
            return self._generate_extractive_summary(chunks, community)

    def _generate_extractive_summary(
        self,
        chunks: List[Chunk],
        community: Community,
    ) -> str:
        """Generate extractive summary without LLM."""
        # Take first sentences from top chunks
        sentences = []

        for chunk in chunks[:5]:
            # Get first sentence
            text = chunk.text.strip()
            first_sentence = text.split('.')[0] + '.'
            if len(first_sentence) > 20:  # Skip very short sentences
                sentences.append(first_sentence)

        if not sentences:
            return ""

        # Add metadata header
        header = f"[Community: {community.dominant_category}, Year: {community.dominant_year}]"
        summary = header + " " + " ".join(sentences)

        return summary


class HierarchicalSummarizer:
    """
    Creates multi-level hierarchical summaries.

    Level 0: Individual chunks
    Level 1: Community summaries
    Level 2: Category summaries
    Level 3: Corpus summary
    """

    def __init__(
        self,
        llm_provider=None,
        community_summarizer: Optional[CommunitySummarizer] = None,
    ):
        """
        Initialize hierarchical summarizer.

        Args:
            llm_provider: LLM for generating summaries
            community_summarizer: Summarizer for communities
        """
        self.llm_provider = llm_provider
        self.community_summarizer = community_summarizer or CommunitySummarizer(
            llm_provider=llm_provider
        )

    def build_hierarchy(
        self,
        communities: List[Community],
        chunks: List[Chunk],
    ) -> Dict[int, str]:
        """
        Build hierarchical summary structure.

        Args:
            communities: Detected communities
            chunks: All chunks

        Returns:
            Dict mapping level -> summaries
        """
        hierarchy = {}

        # Level 1: Community summaries
        community_summaries = self.community_summarizer.summarize_communities(
            communities, chunks
        )
        hierarchy[1] = community_summaries

        # Level 2: Category summaries (group by category)
        if self.llm_provider:
            category_summaries = self._summarize_by_category(
                communities, community_summaries
            )
            hierarchy[2] = category_summaries

        return hierarchy

    def _summarize_by_category(
        self,
        communities: List[Community],
        community_summaries: Dict[int, str],
    ) -> Dict[str, str]:
        """Summarize communities by category."""
        # Group communities by category
        by_category: Dict[str, List[str]] = {}

        for community in communities:
            category = community.dominant_category or "general"
            if category not in by_category:
                by_category[category] = []

            summary = community_summaries.get(community.community_id, "")
            if summary:
                by_category[category].append(summary)

        # Generate category summaries
        category_summaries = {}

        for category, summaries in by_category.items():
            if not summaries:
                continue

            combined = "\n\n".join(summaries[:5])

            try:
                prompt = f"""Synthesize the following community summaries into a high-level overview of the "{category}" category:

{combined}

Provide a brief synthesis (1-2 paragraphs):"""

                synthesis = self.llm_provider.generate(
                    prompt,
                    temperature=0.3,
                    max_tokens=300,
                )
                category_summaries[category] = synthesis.strip()
            except Exception as e:
                logger.warning(f"Category summary failed for {category}: {e}")
                category_summaries[category] = summaries[0] if summaries else ""

        return category_summaries


def create_community_summarizer(
    llm_provider=None,
) -> CommunitySummarizer:
    """Factory function for community summarizer."""
    return CommunitySummarizer(llm_provider=llm_provider)
