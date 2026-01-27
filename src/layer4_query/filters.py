"""
Query Filter Extraction Module

Extracts year, category, and entity filters from queries.
"""

import re
from typing import List, Optional, Tuple
import logging

from src.models.query import QueryFilters

logger = logging.getLogger(__name__)


class FilterExtractor:
    """
    Extracts filters from query text.

    Supports:
    - Year extraction (single year or range)
    - Category extraction
    - Entity extraction
    """

    # Default year patterns
    # CRITICAL FIX: Use non-capturing groups (?:...) so findall() returns full match
    DEFAULT_YEAR_PATTERNS = [
        r'\b(?:19|20)\d{2}\b',  # Plain year: 2020
        r'\bin\s+(?:19|20)\d{2}\b',  # "in 2020"
        r'\bfrom\s+(?:19|20)\d{2}\b',  # "from 2020"
        r'\bsince\s+(?:19|20)\d{2}\b',  # "since 2020"
        r'\bbefore\s+(?:19|20)\d{2}\b',  # "before 2020"
        r'\bafter\s+(?:19|20)\d{2}\b',  # "after 2020"
    ]

    # Category keywords matching personal knowledge base categories
    CATEGORY_KEYWORDS = {
        "ideas": [
            "idea", "concept", "mental model", "framework",
            "philosophy", "principle", "theory", "insight",
            "thought", "notion", "paradigm",
        ],
        "learning": [
            "learn", "study", "technique", "method",
            "skill", "practice", "habit", "education",
            "knowledge", "understanding", "training",
        ],
        "personal": [
            "personal", "reflection", "growth", "self",
            "goal", "experience", "life", "journal",
            "motivation", "mindset", "routine",
        ],
        "saved": [
            "article", "book", "resource", "reference",
            "external", "author", "read", "saved",
            "quote", "source", "recommended",
        ],
    }

    def __init__(
        self,
        year_patterns: Optional[List[str]] = None,
        category_keywords: Optional[dict] = None,
    ):
        """
        Initialize filter extractor.

        Args:
            year_patterns: Custom year extraction patterns
            category_keywords: Custom category keywords
        """
        self.year_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in (year_patterns or self.DEFAULT_YEAR_PATTERNS)
        ]
        self.category_keywords = category_keywords or self.CATEGORY_KEYWORDS

    def extract(self, query: str) -> QueryFilters:
        """
        Extract all filters from query.

        Args:
            query: Query string

        Returns:
            QueryFilters object
        """
        filters = QueryFilters()

        # Extract year
        year, year_range = self._extract_year(query)
        filters.year_filter = year
        filters.year_range = year_range

        # Check if year is required
        filters.require_year_match = self._is_year_required(query)

        # Extract category
        category = self._extract_category(query)
        filters.category_filter = category

        # Extract entities
        filters.entities = self._extract_entities(query)

        logger.debug(
            f"Extracted filters: year={year}, category={category}, "
            f"entities={len(filters.entities)}"
        )

        return filters

    def _extract_year(self, query: str) -> Tuple[Optional[int], Optional[tuple]]:
        """
        Extract year or year range from query.

        CRITICAL FIX: Uses finditer() instead of findall() to get full matches.
        With non-capturing groups (?:19|20), findall returns the full year string.

        Returns:
            Tuple of (single_year, year_range)
        """
        years_found = []

        for pattern in self.year_patterns:
            # Use finditer for reliable full match extraction
            for match in pattern.finditer(query):
                full_match = match.group()  # Gets the full match like "2021" or "in 2021"

                # Extract the 4-digit year from the match
                year_search = re.search(r'(?:19|20)\d{2}', full_match)
                if year_search:
                    year = int(year_search.group())
                    if 1990 <= year <= 2030:
                        years_found.append(year)
                        logger.debug(f"Extracted year {year} from match: '{full_match}'")

        if not years_found:
            logger.debug(f"No years found in query: '{query}'")
            return None, None

        # Deduplicate and sort
        years_found = sorted(set(years_found))

        if len(years_found) == 1:
            logger.debug(f"Single year extracted: {years_found[0]}")
            return years_found[0], None
        else:
            # Multiple years - treat as range
            logger.debug(f"Year range extracted: {years_found}")
            return years_found[0], (min(years_found), max(years_found))

    def _is_year_required(self, query: str) -> bool:
        """Check if year is explicitly required in query."""
        # Use non-capturing groups for consistency
        required_patterns = [
            r'\bonly\s+from\s+(?:19|20)\d{2}\b',
            r'\bspecifically\s+in\s+(?:19|20)\d{2}\b',
            r'\bexactly\s+in\s+(?:19|20)\d{2}\b',
            r'\bfrom\s+(?:19|20)\d{2}\s+only\b',
            r'\bin\s+(?:19|20)\d{2}\s+specifically\b',
        ]

        for pattern in required_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True

        return False

    def _extract_category(self, query: str) -> Optional[str]:
        """Extract category from query based on keywords."""
        query_lower = query.lower()
        category_scores = {}

        for category, keywords in self.category_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            return max(category_scores, key=category_scores.get)

        return None

    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract named entities from query.

        Uses simple heuristics for entity detection.
        """
        entities = []

        # Look for quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)

        # Look for capitalized phrases (potential names/concepts)
        # Skip common words and query starters
        skip_words = {
            "what", "how", "why", "when", "where", "who", "which",
            "is", "are", "was", "were", "the", "a", "an", "in", "on",
            "of", "for", "to", "from", "by", "with", "about",
        }

        words = query.split()
        i = 0
        while i < len(words):
            word = words[i]
            # Check for capitalized word (not at sentence start)
            if i > 0 and word[0].isupper() and word.lower() not in skip_words:
                # Collect consecutive capitalized words
                entity_words = [word]
                j = i + 1
                while j < len(words) and words[j][0].isupper():
                    entity_words.append(words[j])
                    j += 1

                entity = " ".join(entity_words)
                if len(entity) > 2:
                    entities.append(entity)
                i = j
            else:
                i += 1

        return entities[:5]  # Limit entities


def extract_filters(query: str) -> QueryFilters:
    """
    Convenience function to extract filters.

    Args:
        query: Query string

    Returns:
        QueryFilters object
    """
    extractor = FilterExtractor()
    return extractor.extract(query)
