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

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW EXACTLY:
1. For temporal comparisons (e.g., "between 2023 and 2024"), structure as:

   **2023 (or earlier period):**
   [Content from 2023 sources with [N] citations]

   **2024 (or later period):**
   [Content from 2024 sources with [N] citations]
   - If no major changes documented: State "Limited documented changes in 2024" and mention what IS available [N]
   - If sources are events not thinking: Note "2024 sources focus on [topic] rather than [requested topic]" [N]

   **Comparison:**
   Explicitly state what changed, what stayed same, what's different between the periods

2. ABSOLUTE REQUIREMENT: You MUST include BOTH period sections even if one has minimal content
3. Never write only about one period - always cover both with explicit headers
4. If imbalanced sources: Acknowledge the imbalance directly ("Most documented changes from [period]...")
5. Cite sources using [N] notation
$additional_instructions

COMPARISON:"""

    # Template for temporal evolution queries
    TEMPORAL_TEMPLATE = """You are a knowledgeable assistant tracking evolution and changes over time.

CONTEXT (from numbered sources, ordered chronologically):
$context

QUESTION: $question

INSTRUCTIONS:
1. Present information in CHRONOLOGICAL ORDER, starting from the earliest year
2. Show how understanding, perspectives, or events evolved over time
3. Cite sources using [N] notation where N is the source number
4. Use temporal markers (e.g., "Initially in 2020...", "By 2023...", "Most recently...")
5. Highlight key transitions and milestones
$additional_instructions

CHRONOLOGICAL ANSWER:"""

    def __init__(self):
        """Initialize prompt builder."""
        self.templates = {
            "base": Template(self.BASE_TEMPLATE),
            "synthesis": Template(self.SYNTHESIS_TEMPLATE),
            "comparison": Template(self.COMPARISON_TEMPLATE),
            "temporal": Template(self.TEMPORAL_TEMPLATE),
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
            "temporal": "temporal",
        }
        return mapping.get(query_type, "base")
