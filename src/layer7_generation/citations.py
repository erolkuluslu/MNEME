"""
Citation Generator and Linker Module

Creates citations from retrieval results and links them
to their usage in the answer text for interactive navigation.
"""

from typing import List, Dict, Optional, Tuple
import re
import logging

from src.models.chunk import Chunk
from src.models.retrieval import ScoredChunk
from src.models.answer import Citation, LinkedCitation

logger = logging.getLogger(__name__)


class CitationGenerator:
    """
    Generates citations for answer responses.

    Creates numbered citations linking to source chunks.
    """

    def __init__(
        self,
        chunks: List[Chunk],
        max_excerpt_length: int = 200,
    ):
        """
        Initialize citation generator.

        Args:
            chunks: All chunks in corpus
            max_excerpt_length: Maximum excerpt length
        """
        self._chunk_by_id = {c.chunk_id: c for c in chunks}
        self.max_excerpt_length = max_excerpt_length

    def create_citations(
        self,
        scored_chunks: List[ScoredChunk],
        year_filter: Optional[int] = None,
    ) -> List[Citation]:
        """
        Create citations from scored chunks.

        Args:
            scored_chunks: Retrieved and scored chunks
            year_filter: Optional year filter

        Returns:
            List of Citation objects
        """
        citations = []

        for i, scored_chunk in enumerate(scored_chunks):
            chunk = scored_chunk.chunk

            citation = Citation(
                index=i + 1,
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                year=chunk.year,
                category=chunk.category,
                title=chunk.title,
                source_path=chunk.source_path,
                relevance_score=scored_chunk.final_score,
                year_matched=scored_chunk.year_matched,
                excerpt=self._create_excerpt(chunk.text),
            )
            citations.append(citation)

        return citations

    def _create_excerpt(self, text: str) -> str:
        """Create truncated excerpt from text."""
        if len(text) <= self.max_excerpt_length:
            return text

        # Try to break at sentence boundary
        truncated = text[:self.max_excerpt_length]
        last_period = truncated.rfind('.')
        if last_period > self.max_excerpt_length // 2:
            return truncated[:last_period + 1]

        return truncated + "..."

    def get_year_matched_citations(
        self,
        citations: List[Citation],
    ) -> List[Citation]:
        """Get only year-matched citations."""
        return [c for c in citations if c.year_matched]

    def format_citation_list(
        self,
        citations: List[Citation],
    ) -> str:
        """Format citations as text list."""
        lines = []
        for citation in citations:
            year_marker = " ✓" if citation.year_matched else ""
            lines.append(f"  {citation.display_text}{year_marker}")
        return "\n".join(lines)


class CitationValidator:
    """
    Validates citations in generated answers.

    Ensures that:
    1. Citations reference sources that exist in the context
    2. Year-matched citations are used when required
    3. No citations reference truncated or missing sources
    """

    # Pattern to match citation references like [1], [2], etc.
    CITATION_PATTERN = re.compile(r'\[(\d+)\]')

    def validate_citations(
        self,
        answer_text: str,
        included_indices: List[int],
        valid_year_indices: Optional[List[int]] = None,
    ) -> Tuple[str, List[str], bool]:
        """
        Validate that citations in answer reference sources in context.

        Args:
            answer_text: Generated answer text
            included_indices: Indices of chunks actually in context (1-based)
            valid_year_indices: If year-strict, indices that match the year filter

        Returns:
            Tuple of (cleaned_answer, warnings, is_valid)
        """
        warnings = []
        is_valid = True

        # Find all citations in the answer
        cited_indices = [int(m.group(1)) for m in self.CITATION_PATTERN.finditer(answer_text)]

        if not cited_indices:
            # No citations found - might be a "don't know" answer
            return answer_text, warnings, True

        # Check each citation
        invalid_citations = []
        wrong_year_citations = []

        for idx in set(cited_indices):
            if idx not in included_indices:
                # Citation references source not in context (likely truncated)
                invalid_citations.append(idx)
                is_valid = False
            elif valid_year_indices is not None and idx not in valid_year_indices:
                # Citation references wrong-year source in year-strict mode
                wrong_year_citations.append(idx)
                # This is a warning but may still be intentional (comparing years)

        if invalid_citations:
            warnings.append(
                f"Citations {sorted(invalid_citations)} reference sources not in context "
                "(sources may have been truncated)"
            )

        if wrong_year_citations:
            warnings.append(
                f"Citations {sorted(wrong_year_citations)} reference sources from "
                "years other than requested"
            )

        return answer_text, warnings, is_valid

    def get_citation_coverage(
        self,
        answer_text: str,
        included_indices: List[int],
    ) -> Dict[str, any]:
        """
        Analyze citation coverage in the answer.

        Args:
            answer_text: Generated answer text
            included_indices: Indices of chunks in context

        Returns:
            Coverage statistics
        """
        cited_indices = set(int(m.group(1)) for m in self.CITATION_PATTERN.finditer(answer_text))
        included_set = set(included_indices)

        valid_citations = cited_indices & included_set
        invalid_citations = cited_indices - included_set
        unused_sources = included_set - cited_indices

        return {
            "total_sources_in_context": len(included_indices),
            "sources_cited": len(valid_citations),
            "invalid_citations": list(sorted(invalid_citations)),
            "unused_sources": list(sorted(unused_sources)),
            "citation_rate": len(valid_citations) / len(included_indices) if included_indices else 0,
            "all_citations_valid": len(invalid_citations) == 0,
        }


class CitationLinker:
    """
    Links citations to their usage in the answer text.

    Enables interactive navigation like NotebookLM where clicking
    a citation reference highlights the source and vice versa.
    """

    # Pattern to match citation references like [1], [2], etc.
    CITATION_PATTERN = re.compile(r'\[(\d+)\]')

    def link_citations(
        self,
        answer: str,
        citations: List[Citation],
        scored_chunks: Optional[List[ScoredChunk]] = None,
    ) -> Tuple[str, List[LinkedCitation]]:
        """
        Link citations to their positions in the answer text.

        Args:
            answer: Generated answer text
            citations: Basic citations
            scored_chunks: Optional scored chunks for full text

        Returns:
            Tuple of (answer, linked_citations)
        """
        # Build lookup maps
        chunk_map = {}
        if scored_chunks:
            chunk_map = {
                sc.chunk.chunk_id: sc.chunk.text
                for sc in scored_chunks
            }

        # Track citation usage
        citation_usage: Dict[int, List[Tuple[int, int]]] = {
            c.index: [] for c in citations
        }
        citation_contexts: Dict[int, List[str]] = {
            c.index: [] for c in citations
        }

        # Find all citation references in answer
        for match in self.CITATION_PATTERN.finditer(answer):
            idx = int(match.group(1))
            if idx in citation_usage:
                position = (match.start(), match.end())
                citation_usage[idx].append(position)

                # Extract surrounding sentence for context
                context = self._extract_sentence(answer, match.start())
                if context and context not in citation_contexts[idx]:
                    citation_contexts[idx].append(context)

        # Create LinkedCitations
        linked_citations = []
        for citation in citations:
            highlight_id = f"cite-{citation.index}"
            full_text = chunk_map.get(citation.chunk_id, "")

            linked = LinkedCitation.from_citation(
                citation=citation,
                answer_positions=citation_usage.get(citation.index, []),
                usage_contexts=citation_contexts.get(citation.index, []),
                highlight_id=highlight_id,
                full_text=full_text,
            )
            linked_citations.append(linked)

        return answer, linked_citations

    def _extract_sentence(self, text: str, position: int) -> str:
        """
        Extract the sentence containing the citation.

        Args:
            text: Full text
            position: Position of citation

        Returns:
            Sentence containing the citation
        """
        # Find sentence boundaries
        # Look for period, question mark, or exclamation before position
        start = 0
        for i in range(position - 1, -1, -1):
            if text[i] in '.?!':
                start = i + 1
                break

        # Look for period, question mark, or exclamation after position
        end = len(text)
        for i in range(position, len(text)):
            if text[i] in '.?!':
                end = i + 1
                break

        sentence = text[start:end].strip()

        # Clean up any leading whitespace or newlines
        sentence = ' '.join(sentence.split())

        return sentence

    def get_citation_statistics(
        self,
        linked_citations: List[LinkedCitation],
    ) -> Dict[str, any]:
        """
        Get statistics about citation usage.

        Args:
            linked_citations: Linked citations

        Returns:
            Statistics dictionary
        """
        total_usage = sum(c.usage_count for c in linked_citations)
        used_citations = sum(1 for c in linked_citations if c.usage_count > 0)
        unused_citations = sum(1 for c in linked_citations if c.usage_count == 0)

        return {
            "total_citations": len(linked_citations),
            "used_citations": used_citations,
            "unused_citations": unused_citations,
            "total_references": total_usage,
            "usage_rate": used_citations / len(linked_citations) if linked_citations else 0,
            "avg_usage_per_citation": total_usage / len(linked_citations) if linked_citations else 0,
        }


def create_citations(
    scored_chunks: List[ScoredChunk],
    year_filter: Optional[int] = None,
) -> List[Citation]:
    """
    Convenience function to create citations.

    Args:
        scored_chunks: Scored chunks
        year_filter: Year filter

    Returns:
        List of citations
    """
    chunks = [sc.chunk for sc in scored_chunks]
    generator = CitationGenerator(chunks)
    return generator.create_citations(scored_chunks, year_filter)


def create_linked_citations(
    answer: str,
    citations: List[Citation],
    scored_chunks: Optional[List[ScoredChunk]] = None,
) -> Tuple[str, List[LinkedCitation]]:
    """
    Convenience function to create linked citations.

    Args:
        answer: Generated answer text
        citations: Basic citations
        scored_chunks: Optional scored chunks

    Returns:
        Tuple of (answer, linked_citations)
    """
    linker = CitationLinker()
    return linker.link_citations(answer, citations, scored_chunks)


def validate_answer_citations(
    answer_text: str,
    included_indices: List[int],
    valid_year_indices: Optional[List[int]] = None,
) -> Tuple[str, List[str], bool]:
    """
    Convenience function to validate citations in an answer.

    Args:
        answer_text: Generated answer text
        included_indices: Indices of chunks in context (1-based)
        valid_year_indices: If year-strict, indices that match year filter

    Returns:
        Tuple of (answer_text, warnings, is_valid)
    """
    validator = CitationValidator()
    return validator.validate_citations(answer_text, included_indices, valid_year_indices)
