"""
Metadata Extraction Module

Extracts year, category, and other metadata from documents.
"""

import re
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMetadata:
    """Container for extracted document metadata."""

    year: Optional[int] = None
    category: Optional[str] = None
    title: Optional[str] = None
    authors: List[str] = None
    keywords: List[str] = None
    abstract: Optional[str] = None

    # Confidence scores
    year_confidence: float = 0.0
    category_confidence: float = 0.0

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []


class MetadataExtractor:
    """
    Extracts metadata from document content and filenames.

    Supports multiple extraction strategies:
    - Pattern matching for years
    - Keyword matching for categories
    - Content analysis for titles and abstracts
    """

    # Year patterns
    YEAR_PATTERNS = [
        (r'\b(19|20)\d{2}\b', 0.8),  # Plain year
        (r'Published\s+(?:in\s+)?(\d{4})', 0.95),  # "Published in 2020"
        (r'©\s*(\d{4})', 0.9),  # Copyright year
        (r'\((\d{4})\)', 0.7),  # Year in parentheses
        (r'Date:\s*(\d{4})', 0.9),  # Explicit date field
    ]

    # Category keywords (pattern -> category)
    CATEGORY_KEYWORDS = {
        "ai_safety": [
            "alignment", "safety", "risk", "harm", "misalignment",
            "robustness", "interpretability", "transparency",
        ],
        "capabilities": [
            "performance", "benchmark", "capability", "scaling",
            "emergence", "reasoning", "language model",
        ],
        "governance": [
            "governance", "regulation", "policy", "law", "ethics",
            "accountability", "audit", "oversight",
        ],
        "research": [
            "research", "study", "analysis", "methodology",
            "experiment", "findings", "paper",
        ],
        "technical": [
            "architecture", "implementation", "algorithm",
            "optimization", "training", "inference",
        ],
    }

    def __init__(
        self,
        default_year: int = 2020,
        default_category: str = "general",
        min_year: int = 1990,
        max_year: int = 2030,
    ):
        """
        Initialize metadata extractor.

        Args:
            default_year: Default year if not extractable
            default_category: Default category if not extractable
            min_year: Minimum valid year
            max_year: Maximum valid year
        """
        self.default_year = default_year
        self.default_category = default_category
        self.min_year = min_year
        self.max_year = max_year

    def extract(
        self,
        text: str,
        filename: Optional[str] = None,
    ) -> ExtractedMetadata:
        """
        Extract all available metadata from document.

        Args:
            text: Document text content
            filename: Original filename
            file_path: Full file path

        Returns:
            ExtractedMetadata with extracted fields
        """
        metadata = ExtractedMetadata()

        # Extract year
        year, year_conf = self.extract_year(text, filename)
        metadata.year = year
        metadata.year_confidence = year_conf

        # Extract category
        category, cat_conf = self.extract_category(text, filename)
        metadata.category = category
        metadata.category_confidence = cat_conf

        # Extract title
        metadata.title = self.extract_title(text)

        # Extract abstract
        metadata.abstract = self.extract_abstract(text)

        # Extract keywords
        metadata.keywords = self.extract_keywords(text)

        return metadata

    def extract_year(
        self,
        text: str,
        filename: Optional[str] = None,
    ) -> Tuple[int, float]:
        """
        Extract publication year from text or filename.

        Returns:
            Tuple of (year, confidence)
        """
        best_year = None
        best_confidence = 0.0

        # Try filename first (usually more reliable)
        if filename:
            for pattern, confidence in self.YEAR_PATTERNS:
                match = re.search(pattern, filename)
                if match:
                    year = int(match.group(1) if '(' in pattern else match.group(0))
                    if self.min_year <= year <= self.max_year:
                        if confidence > best_confidence:
                            best_year = year
                            best_confidence = confidence

        # Try text content (first 1000 chars most likely to have year)
        text_sample = text[:1000]
        for pattern, confidence in self.YEAR_PATTERNS:
            matches = re.findall(pattern, text_sample)
            for match in matches:
                year = int(match if isinstance(match, str) else match[0])
                if self.min_year <= year <= self.max_year:
                    if confidence > best_confidence:
                        best_year = year
                        best_confidence = confidence

        if best_year is None:
            return self.default_year, 0.0

        return best_year, best_confidence

    def extract_category(
        self,
        text: str,
        filename: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Extract document category based on content keywords.

        Returns:
            Tuple of (category, confidence)
        """
        text_lower = text.lower()
        filename_lower = (filename or "").lower()

        category_scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0.0

            # Check filename
            for keyword in keywords:
                if keyword in filename_lower:
                    score += 0.3

            # Check text content
            for keyword in keywords:
                count = text_lower.count(keyword)
                score += min(count * 0.1, 0.5)  # Cap contribution

            category_scores[category] = score

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            best_score = category_scores[best_category]

            if best_score > 0.2:
                confidence = min(best_score / 2.0, 1.0)
                return best_category, confidence

        return self.default_category, 0.0

    def extract_title(self, text: str) -> Optional[str]:
        """Extract document title from content."""
        lines = text.strip().split('\n')

        for line in lines[:10]:
            line = line.strip()
            # Skip very short or very long lines
            if 10 < len(line) < 200:
                # Skip lines that look like metadata
                if not any(p in line.lower() for p in ['abstract', 'date:', 'author:', 'published']):
                    # Title is often the first substantial line
                    return line

        return None

    def extract_abstract(self, text: str) -> Optional[str]:
        """Extract abstract from document."""
        # Look for explicit abstract section
        patterns = [
            r'Abstract[:\s]*\n*(.*?)(?:\n\n|\nIntroduction|\n1\.)',
            r'ABSTRACT[:\s]*\n*(.*?)(?:\n\n|\nINTRODUCTION|\n1\.)',
            r'Summary[:\s]*\n*(.*?)(?:\n\n|\nIntroduction|\n1\.)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                if 50 < len(abstract) < 2000:
                    return abstract

        return None

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from document."""
        keywords = []

        # Look for explicit keywords section
        pattern = r'Keywords?[:\s]*([^\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            keyword_line = match.group(1)
            # Split by common delimiters
            for kw in re.split(r'[,;•·]', keyword_line):
                kw = kw.strip()
                if 2 < len(kw) < 50:
                    keywords.append(kw.lower())

        return keywords[:10]  # Limit to 10 keywords


def extract_year_from_text(
    text: str,
    default: int = 2020,
) -> int:
    """
    Simple helper to extract year from text.

    Args:
        text: Text to search
        default: Default year if not found

    Returns:
        Extracted year or default
    """
    extractor = MetadataExtractor(default_year=default)
    year, _ = extractor.extract_year(text)
    return year


def extract_category_from_text(
    text: str,
    default: str = "general",
) -> str:
    """
    Simple helper to extract category from text.

    Args:
        text: Text to search
        default: Default category if not found

    Returns:
        Extracted category or default
    """
    extractor = MetadataExtractor(default_category=default)
    category, _ = extractor.extract_category(text)
    return category
