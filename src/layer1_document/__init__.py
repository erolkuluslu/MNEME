"""
Layer 1: Document Processing

Handles document discovery, chunking, and metadata extraction.
"""

from .discovery import DocumentDiscovery, DiscoveredDocument
from .metadata import MetadataExtractor, ExtractedMetadata, extract_year_from_text, extract_category_from_text
from .chunking import (
    BaseChunkingStrategy,
    WordCountChunking,
    SemanticChunking,
    HierarchicalChunking,
    create_word_count_chunker,
    create_semantic_chunker,
    create_hierarchical_chunker,
)

__all__ = [
    # Discovery
    "DocumentDiscovery",
    "DiscoveredDocument",
    # Metadata
    "MetadataExtractor",
    "ExtractedMetadata",
    "extract_year_from_text",
    "extract_category_from_text",
    # Chunking
    "BaseChunkingStrategy",
    "WordCountChunking",
    "SemanticChunking",
    "HierarchicalChunking",
    "create_word_count_chunker",
    "create_semantic_chunker",
    "create_hierarchical_chunker",
]
