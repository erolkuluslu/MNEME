"""
Year-Strict Prompt Templates

CRITICAL FIX: Prompts that enforce year-specific citations.
"""

from typing import List, Optional
from string import Template


class YearStrictPromptBuilder:
    """
    Builds prompts with strict year-based citation rules.

    CRITICAL FIX: This addresses the issue where answers cite
    documents from wrong years when a specific year is requested.
    """

    # Year-strict template
    YEAR_STRICT_TEMPLATE = """You are a knowledgeable assistant answering questions based on provided sources.

CONTEXT (from numbered sources):
$context

QUESTION: $question

CRITICAL CITATION RULES:
- The user is asking specifically about year $year
- ONLY cite sources from year $year
- Valid citation indices: $valid_indices
- INVALID citation indices: $invalid_indices
- If you cite an invalid index, your answer will be rejected
- If no valid sources contain relevant information, say "I don't have specific information from $year about this topic."

INSTRUCTIONS:
1. Answer using ONLY sources from the specified year ($year)
2. Use [N] notation for citations
3. DO NOT cite sources from other years
4. Be accurate about what the $year sources actually say

ANSWER:"""

    # Template when year info is unavailable
    # CRITICAL FIX: Strict refusal to prevent hallucination
    YEAR_UNAVAILABLE_TEMPLATE = """You are a knowledgeable assistant answering questions based on provided sources.

CONTEXT (from numbered sources):
$context

QUESTION: $question

CRITICAL: The user asked specifically about year $year, but NO documents from $year were found in the knowledge base.

STRICT INSTRUCTIONS:
1. State clearly: "I don't have information specifically from $year in my knowledge base."
2. DO NOT provide information from other years and claim it happened in $year - this is hallucination.
3. You may briefly mention what years ARE available in the knowledge base.
4. If the user's question could still be partially answered without year-specific claims, you may do so but be explicit that the information is from different years.
5. Keep the response brief and honest about this limitation.

FORBIDDEN:
- Do NOT cite sources from other years while claiming events happened in $year
- Do NOT fabricate or infer what might have happened in $year
- Do NOT answer as if you have $year information when you don't

ANSWER:"""

    def __init__(self):
        """Initialize year-strict prompt builder."""
        self.strict_template = Template(self.YEAR_STRICT_TEMPLATE)
        self.unavailable_template = Template(self.YEAR_UNAVAILABLE_TEMPLATE)

    def build_year_strict_prompt(
        self,
        context: str,
        question: str,
        year: int,
        valid_indices: List[int],
        all_indices: List[int],
    ) -> str:
        """
        Build a year-strict prompt.

        Args:
            context: Formatted context
            question: User question
            year: Year filter
            valid_indices: Indices of year-matched chunks
            all_indices: All chunk indices

        Returns:
            Formatted prompt
        """
        invalid_indices = [i for i in all_indices if i not in valid_indices]

        return self.strict_template.substitute(
            context=context,
            question=question,
            year=year,
            valid_indices=str(valid_indices) if valid_indices else "NONE",
            invalid_indices=str(invalid_indices) if invalid_indices else "NONE",
        )

    def build_year_unavailable_prompt(
        self,
        context: str,
        question: str,
        year: int,
    ) -> str:
        """
        Build prompt when year data is unavailable.

        Args:
            context: Formatted context
            question: User question
            year: Requested year

        Returns:
            Formatted prompt
        """
        return self.unavailable_template.substitute(
            context=context,
            question=question,
            year=year,
        )

    def should_use_strict_mode(
        self,
        year_filter: Optional[int],
        year_matched_count: int,
        total_count: int,
    ) -> bool:
        """
        Determine if strict mode should be used.

        Args:
            year_filter: Requested year
            year_matched_count: Number of year-matched chunks
            total_count: Total chunks retrieved

        Returns:
            True if strict mode should be enabled
        """
        if year_filter is None:
            return False

        # Use strict mode if we have year-matched chunks
        return year_matched_count > 0


def create_year_strict_prompt(
    context: str,
    question: str,
    year: int,
    valid_indices: List[int],
    all_indices: List[int],
) -> str:
    """
    Convenience function to create year-strict prompt.

    Args:
        context: Formatted context
        question: User question
        year: Year filter
        valid_indices: Valid citation indices
        all_indices: All indices

    Returns:
        Formatted prompt
    """
    builder = YearStrictPromptBuilder()
    return builder.build_year_strict_prompt(
        context, question, year, valid_indices, all_indices
    )
