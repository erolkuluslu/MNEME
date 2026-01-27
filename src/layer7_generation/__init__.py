"""
Layer 7: Answer Generation

LLM providers, prompts, confidence, and citations.
"""

from .generator import AnswerGenerator, create_answer_generator
from .confidence import ConfidenceAssessor, determine_confidence
from .citations import CitationGenerator, create_citations
from .llm import BaseLLMProvider, GeminiProvider, create_gemini_provider
from .prompts import PromptBuilder, YearStrictPromptBuilder, create_year_strict_prompt

__all__ = [
    "AnswerGenerator",
    "create_answer_generator",
    "ConfidenceAssessor",
    "determine_confidence",
    "CitationGenerator",
    "create_citations",
    "BaseLLMProvider",
    "GeminiProvider",
    "create_gemini_provider",
    "PromptBuilder",
    "YearStrictPromptBuilder",
    "create_year_strict_prompt",
]
