"""
LLM-as-Judge Evaluation Module

Implements LLM-based evaluation metrics from notebook v16.
Uses calibrated prompts with low temperature for consistent evaluation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import re
import logging

from src.config import MNEMEConfig
from src.models.retrieval import ScoredChunk
from src.layer7_generation.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


@dataclass
class SynthesisQualityScore:
    """Score for answer synthesis quality."""

    citation_count: int = 0  # Number of [N] references
    source_coverage: float = 0.0  # % of provided sources cited
    integration_quality: int = 0  # LLM judges coherence (1-5)

    @property
    def final_score(self) -> float:
        """Weighted final score (0-1)."""
        # Normalize citation count (cap at 5)
        citation_score = min(self.citation_count / 5, 1.0) * 0.3
        coverage_score = self.source_coverage * 0.3
        integration_score = (self.integration_quality / 5) * 0.4
        return citation_score + coverage_score + integration_score

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "citation_count": self.citation_count,
            "source_coverage": self.source_coverage,
            "integration_quality": self.integration_quality,
            "final_score": self.final_score,
        }


@dataclass
class CrossDomainScore:
    """Score for cross-domain answer quality."""

    category_coverage: float = 0.0  # % of expected categories in sources
    category_usage: float = 0.0  # % of categories actually cited
    integration_quality: float = 0.0  # LLM judges cross-domain synthesis

    @property
    def final_score(self) -> float:
        """Weighted final score (0-1)."""
        return (
            self.category_coverage * 0.4 +
            self.category_usage * 0.3 +
            self.integration_quality * 0.3
        )

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "category_coverage": self.category_coverage,
            "category_usage": self.category_usage,
            "integration_quality": self.integration_quality,
            "final_score": self.final_score,
        }


@dataclass
class MultiHopScore:
    """Score for multi-hop reasoning quality."""

    unique_sources_cited: int = 0  # Number of unique docs cited
    source_diversity: float = 0.0  # Diversity score (0-1)
    reasoning_quality: float = 0.0  # LLM judges reasoning chain (0-1)

    @property
    def final_score(self) -> float:
        """Weighted final score (0-1)."""
        return (
            self.source_diversity * 0.3 +
            self.reasoning_quality * 0.7
        )

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "unique_sources_cited": self.unique_sources_cited,
            "source_diversity": self.source_diversity,
            "reasoning_quality": self.reasoning_quality,
            "final_score": self.final_score,
        }


@dataclass
class TemporalAccuracyScore:
    """Score for temporal accuracy in answers."""

    year_citations_correct: int = 0  # Citations with correct year
    year_citations_total: int = 0  # Total year-filtered citations
    temporal_coherence: float = 0.0  # LLM judges temporal consistency

    @property
    def accuracy_rate(self) -> float:
        """Accuracy rate for year citations."""
        if self.year_citations_total == 0:
            return 1.0  # No temporal requirements
        return self.year_citations_correct / self.year_citations_total

    @property
    def final_score(self) -> float:
        """Weighted final score (0-1)."""
        return self.accuracy_rate * 0.6 + self.temporal_coherence * 0.4

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "year_citations_correct": self.year_citations_correct,
            "year_citations_total": self.year_citations_total,
            "accuracy_rate": self.accuracy_rate,
            "temporal_coherence": self.temporal_coherence,
            "final_score": self.final_score,
        }


@dataclass
class ComprehensiveEvaluation:
    """Comprehensive evaluation combining all metrics."""

    synthesis: SynthesisQualityScore = field(default_factory=SynthesisQualityScore)
    cross_domain: Optional[CrossDomainScore] = None
    multi_hop: Optional[MultiHopScore] = None
    temporal: Optional[TemporalAccuracyScore] = None

    # Overall metrics
    overall_score: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        result = {
            "synthesis": self.synthesis.to_dict(),
            "overall_score": self.overall_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }
        if self.cross_domain:
            result["cross_domain"] = self.cross_domain.to_dict()
        if self.multi_hop:
            result["multi_hop"] = self.multi_hop.to_dict()
        if self.temporal:
            result["temporal"] = self.temporal.to_dict()
        return result


class LLMJudgeEvaluator:
    """
    Implements LLM-as-judge evaluation from notebook v16.

    Uses calibrated prompts with temperature=0.1 for consistency.
    Evaluates synthesis quality, cross-domain integration, multi-hop
    reasoning, and temporal accuracy.
    """

    # Integration quality prompt
    INTEGRATION_QUALITY_PROMPT = """Rate the integration quality of this answer on a scale of 1-5.

Answer: {answer}

Scoring criteria:
1: Disjointed, sources not connected, facts listed without synthesis
2: Basic listing of facts with minimal connection
3: Some synthesis but with gaps in coherence
4: Good integration with clear narrative flow
5: Excellent synthesis, coherent story, sources well-woven together

Respond with ONLY a single number from 1 to 5."""

    # Cross-domain integration prompt
    CROSS_DOMAIN_PROMPT = """Rate how well this answer integrates information across different domains/categories on a scale of 1-5.

Answer: {answer}

Categories present in sources: {categories}

Scoring criteria:
1: Domains completely siloed, no integration
2: Minimal cross-domain references
3: Some connections made between domains
4: Good integration across domains
5: Excellent synthesis showing relationships between domains

Respond with ONLY a single number from 1 to 5."""

    # Reasoning quality prompt
    REASONING_PROMPT = """Rate the quality of multi-hop reasoning in this answer on a scale of 1-5.

Answer: {answer}

Number of sources used: {num_sources}

Scoring criteria:
1: No reasoning, just facts
2: Simple cause-effect mentioned
3: Some reasoning connecting 2 sources
4: Good reasoning chain across multiple sources
5: Excellent multi-hop reasoning with clear logical flow

Respond with ONLY a single number from 1 to 5."""

    # Temporal coherence prompt - enhanced to check query intent alignment
    TEMPORAL_PROMPT = """Rate the temporal coherence of this answer on a scale of 1-5.

Answer: {answer}

Year filter requested: {year}
Query type: {query_type}

Scoring criteria:
1: Wrong years cited, answer doesn't address the requested time period
2: Some citations from wrong years, partial temporal coverage
3: Mostly addresses the right time period, minor temporal issues
4: Good temporal focus on requested year with supporting context from other years
5: Excellent - answer directly addresses the requested year with accurate citations

IMPORTANT: A good answer for a year-specific query should:
- Primarily cite sources from the requested year
- Clearly indicate when referencing other years for context
- Answer the question about that specific time period

Respond with ONLY a single number from 1 to 5."""

    # Query intent alignment prompt - checks if answer addresses the query's temporal scope
    QUERY_ALIGNMENT_PROMPT = """Does this answer properly address the temporal scope of the query?

Query: {query}
Answer: {answer}
Year filter: {year}

Rate on a scale of 1-5:
1: Answer ignores the time period entirely
2: Answer mentions the time but doesn't substantively address it
3: Answer partially addresses the time period
4: Answer addresses the time period with good coverage
5: Answer thoroughly addresses what was requested for that time period

Respond with ONLY a single number from 1 to 5."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        config: Optional[MNEMEConfig] = None,
    ):
        """
        Initialize LLM judge evaluator.

        Args:
            llm_provider: LLM for evaluation judgments
            config: Optional MNEME configuration
        """
        self.llm = llm_provider
        self.judge_temperature = config.judge_temperature if config else 0.1

        logger.info(
            f"LLMJudgeEvaluator initialized with temperature={self.judge_temperature}"
        )

    def evaluate_synthesis_quality(
        self,
        answer: str,
        sources: List[ScoredChunk],
    ) -> SynthesisQualityScore:
        """
        Evaluate synthesis quality of an answer.

        Metrics:
        - Citation count: How many [N] references used
        - Source coverage: % of provided sources actually cited
        - Integration quality: LLM judges coherence (1-5)

        Args:
            answer: Generated answer text
            sources: Source chunks provided to LLM

        Returns:
            SynthesisQualityScore
        """
        # Extract citations from answer
        cited_indices = self._extract_citations(answer)

        # Calculate metrics
        citation_count = len(cited_indices)
        source_coverage = citation_count / len(sources) if sources else 0.0

        # LLM judge for integration quality
        integration_score = self._judge_integration_quality(answer)

        return SynthesisQualityScore(
            citation_count=citation_count,
            source_coverage=source_coverage,
            integration_quality=integration_score,
        )

    def evaluate_cross_domain(
        self,
        answer: str,
        sources: List[ScoredChunk],
        expected_categories: Optional[Set[str]] = None,
    ) -> CrossDomainScore:
        """
        Evaluate cross-domain answer quality.

        3-component scoring:
        - Category coverage (40%): % of expected categories in sources
        - Category usage (30%): % of categories actually cited
        - Integration quality (30%): LLM judges cross-domain synthesis

        Args:
            answer: Generated answer text
            sources: Source chunks
            expected_categories: Categories expected in answer

        Returns:
            CrossDomainScore
        """
        # Get source categories
        source_categories = {s.category for s in sources}

        # Category coverage
        if expected_categories:
            coverage = (
                len(source_categories & expected_categories) / len(expected_categories)
            )
        else:
            coverage = 1.0  # No expectation

        # Category usage (which categories have cited sources)
        cited_indices = self._extract_citations(answer)
        cited_categories = {
            sources[i - 1].category
            for i in cited_indices
            if i <= len(sources)
        }
        usage = (
            len(cited_categories) / len(source_categories)
            if source_categories else 0.0
        )

        # LLM integration quality
        integration = self._judge_cross_domain_integration(answer, source_categories)

        return CrossDomainScore(
            category_coverage=coverage,
            category_usage=usage,
            integration_quality=integration / 5,  # Normalize to 0-1
        )

    def evaluate_multi_hop(
        self,
        answer: str,
        sources: List[ScoredChunk],
    ) -> MultiHopScore:
        """
        Evaluate multi-hop reasoning quality.

        Multi-hop = synthesis of multiple DISTINCT sources.
        - Source diversity (30%): # of unique docs cited
        - Reasoning quality (70%): LLM judges reasoning chain

        Args:
            answer: Generated answer text
            sources: Source chunks

        Returns:
            MultiHopScore
        """
        cited_indices = self._extract_citations(answer)
        cited_docs = {
            sources[i - 1].doc_id
            for i in cited_indices
            if i <= len(sources)
        }

        # Diversity: cap at 3 unique docs for full score
        diversity = min(len(cited_docs) / 3, 1.0)

        # Reasoning quality
        reasoning = self._judge_reasoning_quality(answer, len(cited_docs))

        return MultiHopScore(
            unique_sources_cited=len(cited_docs),
            source_diversity=diversity,
            reasoning_quality=reasoning / 5,  # Normalize to 0-1
        )

    def evaluate_temporal_accuracy(
        self,
        answer: str,
        sources: List[ScoredChunk],
        year_filter: Optional[int],
        query: str = "",
        is_temporal_span: bool = False,
    ) -> TemporalAccuracyScore:
        """
        Evaluate temporal accuracy of an answer.

        CRITICAL FIX: Properly evaluates temporal accuracy by:
        1. Checking citation year accuracy (do citations match requested year?)
        2. Evaluating query intent alignment (does answer address the time period?)
        3. Distinguishing single-year vs. temporal-span queries

        Args:
            answer: Generated answer text
            sources: Source chunks
            year_filter: Requested year filter
            query: Original query text (for intent analysis)
            is_temporal_span: True if query asks about multiple years (e.g., "2020 to 2025")

        Returns:
            TemporalAccuracyScore
        """
        if not year_filter:
            return TemporalAccuracyScore(
                temporal_coherence=1.0  # No temporal requirements
            )

        # Check which citations are year-correct
        cited_indices = self._extract_citations(answer)
        correct = 0
        total = 0

        for idx in cited_indices:
            if idx <= len(sources):
                total += 1
                source_year = sources[idx - 1].year
                if is_temporal_span:
                    # For temporal spans, any year in the answer is acceptable
                    # (evaluation should check coverage separately)
                    correct += 1
                elif source_year == year_filter:
                    correct += 1

        # LLM temporal coherence - check both citation accuracy and query intent
        query_type = "temporal_span" if is_temporal_span else "single_year"
        coherence = self._judge_temporal_coherence(answer, year_filter, query_type)

        return TemporalAccuracyScore(
            year_citations_correct=correct,
            year_citations_total=total,
            temporal_coherence=coherence / 5,  # Normalize to 0-1
        )

    def comprehensive_evaluation(
        self,
        answer: str,
        sources: List[ScoredChunk],
        year_filter: Optional[int] = None,
        expected_categories: Optional[Set[str]] = None,
        is_multi_hop: bool = False,
        is_cross_domain: bool = False,
    ) -> ComprehensiveEvaluation:
        """
        Perform comprehensive evaluation of an answer.

        Args:
            answer: Generated answer text
            sources: Source chunks
            year_filter: Requested year filter
            expected_categories: Expected categories
            is_multi_hop: Whether query requires multi-hop reasoning
            is_cross_domain: Whether query is cross-domain

        Returns:
            ComprehensiveEvaluation with all metrics
        """
        eval_result = ComprehensiveEvaluation()

        # Always evaluate synthesis
        eval_result.synthesis = self.evaluate_synthesis_quality(answer, sources)

        # Always evaluate multi-hop to detect actual multi-hop reasoning
        # regardless of whether query explicitly requires it
        eval_result.multi_hop = self.evaluate_multi_hop(answer, sources)

        # Conditional cross-domain evaluation
        if is_cross_domain:
            eval_result.cross_domain = self.evaluate_cross_domain(
                answer, sources, expected_categories
            )

        if year_filter:
            eval_result.temporal = self.evaluate_temporal_accuracy(
                answer, sources, year_filter
            )

        # Compute overall score
        scores = [eval_result.synthesis.final_score]
        if eval_result.cross_domain:
            scores.append(eval_result.cross_domain.final_score)
        if eval_result.multi_hop:
            scores.append(eval_result.multi_hop.final_score)
        if eval_result.temporal:
            scores.append(eval_result.temporal.final_score)

        eval_result.overall_score = sum(scores) / len(scores)

        # Identify strengths and weaknesses
        eval_result.strengths = self._identify_strengths(eval_result)
        eval_result.weaknesses = self._identify_weaknesses(eval_result)

        return eval_result

    def _extract_citations(self, answer: str) -> Set[int]:
        """Extract citation indices from answer text."""
        matches = re.findall(r'\[(\d+)\]', answer)
        return {int(m) for m in matches}

    def _judge_integration_quality(self, answer: str) -> int:
        """Use LLM to judge integration quality."""
        prompt = self.INTEGRATION_QUALITY_PROMPT.format(answer=answer)
        return self._get_numeric_judgment(prompt)

    def _judge_cross_domain_integration(
        self, answer: str, categories: Set[str]
    ) -> int:
        """Use LLM to judge cross-domain integration."""
        prompt = self.CROSS_DOMAIN_PROMPT.format(
            answer=answer,
            categories=", ".join(sorted(categories)),
        )
        return self._get_numeric_judgment(prompt)

    def _judge_reasoning_quality(self, answer: str, num_sources: int) -> int:
        """Use LLM to judge reasoning quality."""
        prompt = self.REASONING_PROMPT.format(
            answer=answer,
            num_sources=num_sources,
        )
        return self._get_numeric_judgment(prompt)

    def _judge_temporal_coherence(
        self, answer: str, year: int, query_type: str = "single_year"
    ) -> int:
        """Use LLM to judge temporal coherence."""
        prompt = self.TEMPORAL_PROMPT.format(
            answer=answer, year=year, query_type=query_type
        )
        return self._get_numeric_judgment(prompt)

    def _get_numeric_judgment(self, prompt: str) -> int:
        """Get numeric judgment from LLM."""
        try:
            response = self.llm.generate(
                prompt,
                temperature=self.judge_temperature,
                max_tokens=10,
            )
            # Extract number from response
            match = re.search(r'[1-5]', response)
            if match:
                return int(match.group())
            logger.warning(f"Could not parse LLM judgment: {response}")
            return 3  # Default to middle score
        except Exception as e:
            logger.error(f"LLM judgment failed: {e}")
            return 3

    def _identify_strengths(self, eval_result: ComprehensiveEvaluation) -> List[str]:
        """Identify strengths based on scores."""
        strengths = []

        if eval_result.synthesis.integration_quality >= 4:
            strengths.append("Excellent source integration")
        if eval_result.synthesis.source_coverage >= 0.7:
            strengths.append("Good source coverage")

        if eval_result.cross_domain and eval_result.cross_domain.final_score >= 0.7:
            strengths.append("Strong cross-domain synthesis")

        if eval_result.multi_hop and eval_result.multi_hop.reasoning_quality >= 0.7:
            strengths.append("Good multi-hop reasoning")

        if eval_result.temporal and eval_result.temporal.accuracy_rate >= 0.9:
            strengths.append("High temporal accuracy")

        return strengths

    def _identify_weaknesses(self, eval_result: ComprehensiveEvaluation) -> List[str]:
        """Identify weaknesses based on scores."""
        weaknesses = []

        if eval_result.synthesis.citation_count < 2:
            weaknesses.append("Low citation count")
        if eval_result.synthesis.integration_quality <= 2:
            weaknesses.append("Poor source integration")

        if eval_result.cross_domain and eval_result.cross_domain.category_usage < 0.5:
            weaknesses.append("Limited cross-domain coverage")

        if eval_result.multi_hop and eval_result.multi_hop.source_diversity < 0.5:
            weaknesses.append("Low source diversity")

        if eval_result.temporal and eval_result.temporal.accuracy_rate < 0.7:
            weaknesses.append("Temporal accuracy issues")

        return weaknesses


def create_llm_judge(
    llm_provider: BaseLLMProvider,
    config: Optional[MNEMEConfig] = None,
) -> LLMJudgeEvaluator:
    """Factory function to create LLM judge evaluator."""
    return LLMJudgeEvaluator(llm_provider=llm_provider, config=config)
