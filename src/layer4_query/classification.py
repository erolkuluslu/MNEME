"""
Query Classification Module

Classifies queries by type and intent.
"""

import re
from typing import Tuple
import logging

from src.models.query import QueryType, QueryIntent

logger = logging.getLogger(__name__)


class QueryClassifier:
    """
    Classifies queries into types and intents.

    Uses pattern matching and keyword analysis for classification.
    """

    # Query type patterns
    TYPE_PATTERNS = {
        QueryType.COMPARISON: [
            r"\bcompare\b",
            r"\bdifference\s+between\b",
            r"\bdiffer\s+between\b",
            r"\bvs\.?\b",
            r"\bversus\b",
            r"\bcontrast\b",
            r"\bhow\s+(?:does|did|do)\s+\w+\s+differ\b",
            r"\bsimilarities?\s+and\s+differences?\b",
            r"\bbetween\s+.*\s+and\s+.*\b",  # "between X and Y" pattern
            r"\b(?:what|how)\s+(?:changed|differed|evolved)\s+between\b",  # "what changed between"
        ],
        QueryType.TEMPORAL: [
            # CRITICAL FIX: Add patterns for year-specific queries
            r"\bwhat\s+happened\b.*\b(19|20)\d{2}\b",  # "what happened in 2021"
            r"\b(19|20)\d{2}\b",  # Any mention of a year (1900s-2000s)
            r"\bin\s+(19|20)\d{2}\b",  # "in 2021"
            r"\bfrom\s+(19|20)\d{2}\b",  # "from 2020"
            r"\bduring\s+(19|20)\d{2}\b",  # "during 2021"
            # Original patterns
            r"\bhow\s+has\s+\w+\s+changed\b",
            r"\bevolution\s+of\b",
            r"\bover\s+time\b",
            r"\bhistor(y|ical)\b",
            r"\bprogress(ion)?\s+of\b",
            r"\btrend\b",
            r"\btimeline\b",
        ],
        QueryType.SYNTHESIS: [
            r"\bsummar(y|ize)\b",
            r"\boverview\s+of\b",
            r"\bexplain\s+all\b",
            r"\bcomprehensive\b",
            r"\bsynthesize\b",
            r"\bcombine\s+\w+\s+perspectives\b",
            r"\bwhat\s+are\s+the\s+main\b",
            r"\bwhat\s+patterns\b",
            r"\bwhat\s+connections\b",
            r"\brelate\s+to\b",
            r"\binfluence[ds]?\b",
            r"\bcreate\s+a\s+comprehensive\b",
            r"\bkey\s+themes\b",
        ],
        QueryType.EXPLORATORY: [
            r"\bwhat\s+is\b",
            r"\bwhat\s+are\b",
            r"\btell\s+me\s+about\b",
            r"\bexplain\b",
            r"\bdescribe\b",
            r"\bdefine\b",
        ],
    }

    # Intent patterns
    INTENT_PATTERNS = {
        QueryIntent.FACTUAL: [
            r"\bwhat\s+is\b",
            r"\bwhen\s+did\b",
            r"\bwho\s+is\b",
            r"\bwhere\s+is\b",
            r"\bhow\s+many\b",
            r"\bhow\s+much\b",
        ],
        QueryIntent.EXPLANATORY: [
            r"\bwhy\b",
            r"\bhow\s+does\b",
            r"\bexplain\b",
            r"\bunderstand\b",
            r"\breason\b",
            r"\bcause\b",
        ],
        QueryIntent.EVALUATIVE: [
            r"\bshould\b",
            r"\bbest\b",
            r"\bworse?\b",
            r"\brecommend\b",
            r"\badvise\b",
            r"\bevaluate\b",
            r"\bassess\b",
        ],
        QueryIntent.PROCEDURAL: [
            r"\bhow\s+to\b",
            r"\bhow\s+can\s+I\b",
            r"\bsteps?\s+to\b",
            r"\bprocess\s+for\b",
            r"\bguide\b",
            r"\btutorial\b",
        ],
        QueryIntent.COMPARATIVE: [
            r"\bcompare\b",
            r"\bdifference\b",
            r"\bvs\.?\b",
            r"\bbetter\b",
            r"\bwhich\s+is\b",
        ],
    }

    def __init__(self):
        """Initialize classifier."""
        # Pre-compile patterns
        self._type_patterns = {
            qtype: [re.compile(p, re.IGNORECASE) for p in patterns]
            for qtype, patterns in self.TYPE_PATTERNS.items()
        }
        self._intent_patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in self.INTENT_PATTERNS.items()
        }

    def classify_type(self, query: str) -> Tuple[QueryType, float]:
        """
        Classify query type.

        Args:
            query: Query string

        Returns:
            Tuple of (QueryType, confidence)
        """
        scores = {qtype: 0.0 for qtype in QueryType}

        for qtype, patterns in self._type_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    scores[qtype] += 1.0

        # Find best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        # Default to SPECIFIC if no patterns match
        if best_score == 0:
            return QueryType.SPECIFIC, 0.5

        # Calculate confidence
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.5

        return best_type, confidence

    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify query intent.

        Args:
            query: Query string

        Returns:
            QueryIntent
        """
        scores = {intent: 0.0 for intent in QueryIntent}

        for intent, patterns in self._intent_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    scores[intent] += 1.0

        # Find best match
        best_intent = max(scores, key=scores.get)

        # Default to FACTUAL if no patterns match
        if scores[best_intent] == 0:
            return QueryIntent.FACTUAL

        return best_intent

    def is_year_specific(self, query: str) -> bool:
        """Check if query mentions a specific year."""
        year_pattern = re.compile(r"\b(19|20)\d{2}\b")
        return bool(year_pattern.search(query))

    def is_comparison_query(self, query: str) -> bool:
        """Check if query is a comparison query."""
        qtype, _ = self.classify_type(query)
        return qtype == QueryType.COMPARISON


def classify_query(query: str) -> Tuple[QueryType, QueryIntent]:
    """
    Convenience function to classify a query.

    Args:
        query: Query string

    Returns:
        Tuple of (QueryType, QueryIntent)
    """
    classifier = QueryClassifier()
    qtype, _ = classifier.classify_type(query)
    intent = classifier.classify_intent(query)
    return qtype, intent
