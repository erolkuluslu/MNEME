"""
Word Count Chunking Strategy

Simple word-count based chunking with sentence boundary respect.
This is the primary chunking strategy for the MNEME system.
"""

from typing import List
import logging

from .base import BaseChunkingStrategy
from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


class WordCountChunking(BaseChunkingStrategy):
    """
    Word-count based chunking strategy.

    Splits documents into chunks of approximately target_size words,
    respecting sentence boundaries when possible.

    Default configuration:
    - Target: 300 words per chunk
    - Min: 50 words
    - Max: 600 words
    - Overlap: 50 words (1-2 sentences)
    """

    def __init__(
        self,
        target_size: int = 300,
        min_size: int = 50,
        max_size: int = 600,
        overlap: int = 50,
        respect_paragraphs: bool = True,
    ):
        """
        Initialize word count chunking.

        Args:
            target_size: Target words per chunk (default: 300)
            min_size: Minimum words for valid chunk (default: 50)
            max_size: Maximum words per chunk (default: 600)
            overlap: Word overlap between chunks (default: 50)
            respect_paragraphs: Try to break at paragraph boundaries
        """
        super().__init__(target_size, min_size, max_size, overlap)
        self.respect_paragraphs = respect_paragraphs

    def chunk(
        self,
        text: str,
        doc_id: str,
        category: str,
        year: int,
    ) -> List[Chunk]:
        """
        Split text into word-count based chunks.

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

        # Clean text
        text = self._clean_text(text)

        # Split into sentences
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        # Build chunks from sentences
        chunks_text = self._build_chunks(sentences)

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
            )
            chunks.append(chunk)

        logger.debug(f"Created {len(chunks)} chunks for {doc_id}")
        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        import re

        # Split into lines to preserve structure and check line length
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Normalize whitespace within the line
            # This preserves newlines between lines but fixes spacing within them
            line = re.sub(r'\s+', ' ', line).strip()
            
            # Remove very long lines that might be tables/code/base64
            # Increased limit to Avoid dropping valid long paragraphs
            if len(line) < 4096:  
                cleaned_lines.append(line)
                
        text = '\n'.join(cleaned_lines)

        return text.strip()

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences, respecting paragraph boundaries."""
        import re

        sentences = []

        if self.respect_paragraphs:
            # Split by paragraphs first
            paragraphs = re.split(r'\n\s*\n', text)
            for para in paragraphs:
                if para.strip():
                    # Split paragraph into sentences
                    para_sentences = re.split(r'(?<=[.!?])\s+', para)
                    sentences.extend([s.strip() for s in para_sentences if s.strip()])
        else:
            # Simple sentence split
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _build_chunks(self, sentences: List[str]) -> List[str]:
        """Build chunks from sentences, respecting size limits."""
        chunks = []
        current_chunk = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())

            # If adding this sentence exceeds max, finalize current chunk
            if current_word_count + sentence_words > self.max_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                current_chunk = self._get_overlap_sentences(current_chunk)
                current_word_count = sum(len(s.split()) for s in current_chunk)

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_word_count += sentence_words

            # If reached target size and this is a good break point
            if current_word_count >= self.target_size:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                current_chunk = self._get_overlap_sentences(current_chunk)
                current_word_count = sum(len(s.split()) for s in current_chunk)

        # Don't forget last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if self._count_words(chunk_text) >= self.min_size:
                chunks.append(chunk_text)
            elif chunks:
                # Merge with previous chunk if too small
                chunks[-1] = chunks[-1] + ' ' + chunk_text

        return chunks

    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap with next chunk."""
        if self.overlap <= 0:
            return []

        overlap_sentences = []
        overlap_words = 0

        # Take sentences from the end until we hit overlap target
        for sentence in reversed(sentences):
            sentence_words = len(sentence.split())
            if overlap_words + sentence_words > self.overlap:
                break
            overlap_sentences.insert(0, sentence)
            overlap_words += sentence_words

        return overlap_sentences


def create_word_count_chunker(
    target_size: int = 300,
    min_size: int = 50,
    max_size: int = 600,
    overlap: int = 50,
) -> WordCountChunking:
    """Factory function to create word count chunker."""
    return WordCountChunking(
        target_size=target_size,
        min_size=min_size,
        max_size=max_size,
        overlap=overlap,
    )
