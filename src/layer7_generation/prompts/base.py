"""
Base Prompt Templates

Core prompt templates for answer generation.
"""

from typing import List, Optional
from string import Template


class PromptBuilder:
    """
    Builds prompts for answer generation.
    """

    # Base template for answer generation
    BASE_TEMPLATE = """You are a knowledgeable assistant answering questions based on provided sources.

CONTEXT (from numbered sources):
$context

QUESTION: $question

INSTRUCTIONS:
1. Answer the question using ONLY information from the provided sources
2. Cite sources using [N] notation where N is the source number
3. If sources don't contain sufficient information, acknowledge the limitation
4. Be concise but comprehensive
$additional_instructions

ANSWER:"""

    # Template for synthesis queries
    SYNTHESIS_TEMPLATE = """You are a knowledgeable assistant synthesizing information from multiple sources.

CONTEXT (from numbered sources):
$context

QUESTION: $question

INSTRUCTIONS:
1. Synthesize information across all provided sources
2. Identify common themes, agreements, and disagreements
3. Cite sources using [N] notation where N is the source number
4. Organize your response logically
$additional_instructions

SYNTHESIS:"""

    # Template for comparison queries
    COMPARISON_TEMPLATE = """You are a knowledgeable assistant comparing and contrasting information.

CONTEXT (from numbered sources):
$context

QUESTION: $question

INSTRUCTIONS:
1. Compare and contrast the perspectives from different sources
2. Identify similarities and differences
3. Cite sources using [N] notation where N is the source number
4. Be balanced and objective
$additional_instructions

COMPARISON:"""

    def __init__(self):
        """Initialize prompt builder."""
        self.templates = {
            "base": Template(self.BASE_TEMPLATE),
            "synthesis": Template(self.SYNTHESIS_TEMPLATE),
            "comparison": Template(self.COMPARISON_TEMPLATE),
        }

    def build_prompt(
        self,
        context: str,
        question: str,
        query_type: str = "specific",
        additional_instructions: str = "",
    ) -> str:
        """
        Build a prompt for answer generation.

        Args:
            context: Formatted context from retrieved chunks
            question: User question
            query_type: Type of query (specific, synthesis, comparison)
            additional_instructions: Additional prompt instructions

        Returns:
            Formatted prompt string
        """
        template_key = self._get_template_key(query_type)
        template = self.templates.get(template_key, self.templates["base"])

        return template.substitute(
            context=context,
            question=question,
            additional_instructions=additional_instructions,
        )

    def _get_template_key(self, query_type: str) -> str:
        """Map query type to template key."""
        mapping = {
            "synthesis": "synthesis",
            "comparison": "comparison",
        }
        return mapping.get(query_type, "base")
