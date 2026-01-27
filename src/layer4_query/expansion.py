"""
Query Expansion Module

Expands queries with synonyms and related terms.
"""

import re
from typing import List, Dict
import logging

from src.models.query import QueryExpansion

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    Expands queries with synonyms and related concepts.

    Uses a synonym dictionary and optional LLM for expansion.
    """

    # Built-in synonym dictionary for AI/ML domain
    SYNONYMS = {
        "ai": ["artificial intelligence", "machine learning", "ml"],
        "artificial intelligence": ["ai", "machine learning"],
        "ml": ["machine learning", "ai", "artificial intelligence"],
        "machine learning": ["ml", "ai", "deep learning"],
        "deep learning": ["neural networks", "machine learning", "dl"],
        "neural network": ["deep learning", "nn", "neural net"],
        "llm": ["large language model", "language model", "gpt"],
        "large language model": ["llm", "language model", "foundation model"],
        "gpt": ["generative pre-trained transformer", "llm"],
        "transformer": ["attention mechanism", "self-attention"],
        "alignment": ["value alignment", "ai alignment", "aligned ai"],
        "safety": ["ai safety", "safe ai", "risk mitigation"],
        "risk": ["danger", "hazard", "threat"],
        "capability": ["capabilities", "ability", "performance"],
        "benchmark": ["evaluation", "test", "assessment"],
        "training": ["fine-tuning", "learning", "optimization"],
        "inference": ["prediction", "generation", "forward pass"],
        "prompt": ["input", "query", "instruction"],
        "context": ["window", "memory", "context length"],
        "hallucination": ["confabulation", "fabrication", "false output"],
        "rlhf": ["reinforcement learning from human feedback", "human feedback"],
        "emergence": ["emergent behavior", "emergent capability"],
        "scaling": ["scale", "scaling laws", "model size"],
    }

    def __init__(
        self,
        enabled: bool = True,
        max_terms: int = 3,
        synonyms: Dict[str, List[str]] = None,
        llm_provider=None,
    ):
        """
        Initialize query expander.

        Args:
            enabled: Whether expansion is enabled
            max_terms: Maximum expansion terms to add
            synonyms: Custom synonym dictionary
            llm_provider: Optional LLM for dynamic expansion
        """
        self.enabled = enabled
        self.max_terms = max_terms
        self.synonyms = synonyms or self.SYNONYMS
        self.llm_provider = llm_provider

        # Build reverse synonym lookup
        self._build_reverse_lookup()

    def _build_reverse_lookup(self):
        """Build case-insensitive pattern matching."""
        self._patterns = {}
        for term, syns in self.synonyms.items():
            # Create pattern for the term
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            self._patterns[term] = (pattern, syns)

    def expand(self, query: str) -> QueryExpansion:
        """
        Expand a query with synonyms and related terms.

        Args:
            query: Original query

        Returns:
            QueryExpansion object
        """
        if not self.enabled:
            return QueryExpansion(original_query=query)

        expansion = QueryExpansion(original_query=query)

        # Find matching terms and their synonyms
        query_lower = query.lower()
        found_synonyms = {}

        for term, (pattern, syns) in self._patterns.items():
            if pattern.search(query):
                found_synonyms[term] = syns[:self.max_terms]

        expansion.synonyms = found_synonyms

        # Flatten synonyms to expanded terms
        all_expansions = []
        for syns in found_synonyms.values():
            all_expansions.extend(syns)

        # Deduplicate and limit
        seen = set()
        unique_expansions = []
        for term in all_expansions:
            term_lower = term.lower()
            if term_lower not in seen and term_lower not in query_lower:
                seen.add(term_lower)
                unique_expansions.append(term)

        expansion.expanded_terms = unique_expansions[:self.max_terms]

        # Add related concepts if LLM available
        if self.llm_provider:
            expansion.related_concepts = self._get_related_concepts(query)

        logger.debug(
            f"Expanded query with {len(expansion.expanded_terms)} terms: "
            f"{expansion.expanded_terms}"
        )

        return expansion

    def _get_related_concepts(self, query: str) -> List[str]:
        """Get related concepts using LLM."""
        prompt = f"""Given the query: "{query}"

List 3 closely related concepts or terms that could help find relevant information.
Return only the terms, one per line, no explanations."""

        try:
            response = self.llm_provider.generate(
                prompt,
                temperature=0.3,
                max_tokens=50,
            )

            concepts = [
                line.strip().strip("-").strip()
                for line in response.strip().split("\n")
                if line.strip()
            ]
            return concepts[:3]
        except Exception as e:
            logger.warning(f"LLM expansion failed: {e}")
            return []


def expand_query(query: str, max_terms: int = 3) -> QueryExpansion:
    """
    Convenience function to expand a query.

    Args:
        query: Query string
        max_terms: Maximum expansion terms

    Returns:
        QueryExpansion object
    """
    expander = QueryExpander(max_terms=max_terms)
    return expander.expand(query)
