"""
Answer Generator Module

Main answer generation orchestrator with dual-model selection support.
"""

import time
from typing import List, Tuple
import logging

from src.config import MNEMEConfig
from src.models.query import QueryPlan
from src.models.retrieval import RetrievalResult
from src.models.answer import EnhancedAnswer, Citation, GenerationStats, AnswerQuality
from .llm.base import BaseLLMProvider
from .llm.gemini import GeminiModelSelector
from .prompts.base import PromptBuilder
from .prompts.year_strict import YearStrictPromptBuilder
from .confidence import ConfidenceAssessor

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """
    Generates answers from retrieval results using LLM.

    Coordinates prompt building, LLM generation, and citation creation.
    """

    def __init__(
        self,
        config: MNEMEConfig,
        llm_provider: BaseLLMProvider,
    ):
        """
        Initialize answer generator.

        Args:
            config: MNEME configuration
            llm_provider: LLM for generation
        """
        self.config = config
        self.llm_provider = llm_provider

        self.prompt_builder = PromptBuilder()
        self.year_strict_builder = YearStrictPromptBuilder()
        self.confidence_assessor = ConfidenceAssessor(
            min_year_matched_for_high=config.min_year_matched_for_confidence,
        )

        # Initialize model selector if enabled
        self.model_selector = None
        if config.model_selection_enabled:
            self.model_selector = GeminiModelSelector(
                complex_model=config.complex_model,
                simple_model=config.simple_model,
            )
            logger.info(
                f"Model selection enabled: complex={config.complex_model}, "
                f"simple={config.simple_model}"
            )

    def generate(
        self,
        question: str,
        plan: QueryPlan,
        retrieval_result: RetrievalResult,
        context: str,
    ) -> Tuple[str, GenerationStats]:
        """
        Generate an answer from retrieval results.

        Uses dual-model selection when enabled:
        - Complex model for synthesis, multi-hop, low-confidence queries
        - Simple model for factual, direct retrieval queries

        Args:
            question: User question
            plan: Query plan
            retrieval_result: Retrieval results
            context: Formatted context string

        Returns:
            Tuple of (answer_text, generation_stats)
        """
        start_time = time.time()

        # Build prompt
        prompt = self._build_prompt(question, plan, retrieval_result, context)

        # Select model based on query complexity
        selected_model = None
        if self.model_selector:
            selected_model = self.model_selector.select_model(
                query_plan=plan,
                retrieval_confidence=retrieval_result.confidence,
            )
            logger.info(f"Selected model for query: {selected_model}")

        # Generate
        try:
            # Pass model override if using model selection
            if selected_model and hasattr(self.llm_provider, 'generate'):
                # Check if provider supports model_override
                import inspect
                sig = inspect.signature(self.llm_provider.generate)
                if 'model_override' in sig.parameters:
                    answer_text = self.llm_provider.generate(
                        prompt,
                        temperature=self.config.answer_temperature,
                        max_tokens=self.config.max_tokens,
                        model_override=selected_model,
                    )
                else:
                    answer_text = self.llm_provider.generate(
                        prompt,
                        temperature=self.config.answer_temperature,
                        max_tokens=self.config.max_tokens,
                    )
            else:
                answer_text = self.llm_provider.generate(
                    prompt,
                    temperature=self.config.answer_temperature,
                    max_tokens=self.config.max_tokens,
                )
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            answer_text = f"Unable to generate answer: {str(e)}"

        generation_time = (time.time() - start_time) * 1000

        # Use selected model name if available, otherwise default
        model_used = selected_model if selected_model else self.llm_provider.model_name

        stats = GenerationStats(
            generation_time_ms=generation_time,
            model_used=model_used,
            temperature=self.config.answer_temperature,
            num_source_chunks=len(retrieval_result.candidates),
            context_length=len(context),
        )

        return answer_text, stats

    def _build_prompt(
        self,
        question: str,
        plan: QueryPlan,
        retrieval_result: RetrievalResult,
        context: str,
    ) -> str:
        """Build the appropriate prompt."""
        # Check if year-strict mode should be used
        if self.config.year_strict_mode and plan.year_filter:
            year_matched_count = sum(
                1 for c in retrieval_result.candidates if c.year_matched
            )

            if year_matched_count > 0:
                # Use year-strict prompt
                valid_indices = [
                    i + 1 for i, c in enumerate(retrieval_result.candidates)
                    if c.year_matched
                ]
                all_indices = list(range(1, len(retrieval_result.candidates) + 1))

                return self.year_strict_builder.build_year_strict_prompt(
                    context=context,
                    question=question,
                    year=plan.year_filter,
                    valid_indices=valid_indices,
                    all_indices=all_indices,
                )
            else:
                # No year matches - use unavailable prompt
                return self.year_strict_builder.build_year_unavailable_prompt(
                    context=context,
                    question=question,
                    year=plan.year_filter,
                )

        # Use standard prompt
        return self.prompt_builder.build_prompt(
            context=context,
            question=question,
            query_type=plan.query_type.value,
        )

    def create_enhanced_answer(
        self,
        answer_text: str,
        question: str,
        plan: QueryPlan,
        retrieval_result: RetrievalResult,
        stats: GenerationStats,
        citations: List[Citation],
        total_latency_ms: float,
    ) -> EnhancedAnswer:
        """
        Create an EnhancedAnswer from generation results.

        Args:
            answer_text: Generated answer
            question: Original question
            plan: Query plan
            retrieval_result: Retrieval results
            stats: Generation stats
            citations: Generated citations
            total_latency_ms: Total pipeline latency

        Returns:
            EnhancedAnswer object
        """
        # Assess confidence
        confidence = self.confidence_assessor.assess(
            candidates=retrieval_result.candidates,
            year_filter=plan.year_filter,
        )

        # Assess quality
        quality = self._assess_quality(answer_text, citations)

        # Get coverage info
        years_covered = list(set(c.year for c in citations))
        categories_covered = list(set(c.category for c in citations))

        stats.total_latency_ms = total_latency_ms

        return EnhancedAnswer(
            answer=answer_text,
            query=question,
            citations=citations,
            confidence=confidence.value,
            quality=quality,
            latency_ms=total_latency_ms,
            stats=stats,
            query_type=plan.query_type.value,
            year_filter=plan.year_filter,
            category_filter=plan.category_filter,
            num_sources_used=len(citations),
            years_covered=sorted(years_covered),
            categories_covered=sorted(categories_covered),
            coverage_gaps=retrieval_result.coverage_gaps,
        )

    def _assess_quality(
        self,
        answer_text: str,
        citations: List[Citation],
    ) -> AnswerQuality:
        """Assess answer quality."""
        if not answer_text or len(answer_text) < 20:
            return AnswerQuality.POOR

        if "Unable to" in answer_text or "don't have" in answer_text.lower():
            return AnswerQuality.FAIR

        if citations and len(citations) >= 2:
            return AnswerQuality.GOOD

        return AnswerQuality.FAIR


def create_answer_generator(
    config: MNEMEConfig,
    llm_provider: BaseLLMProvider,
) -> AnswerGenerator:
    """Factory function to create answer generator."""
    return AnswerGenerator(config=config, llm_provider=llm_provider)
