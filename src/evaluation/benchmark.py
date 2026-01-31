"""
Benchmark Evaluation Framework

Tests MNEME without keyword/category hints to evaluate
real-world query handling capability.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, TYPE_CHECKING
import time
import logging
import json

if TYPE_CHECKING:
    from src.pipeline.mneme import MNEME

from src.models.answer import EnhancedAnswer
from .llm_judge import (
    LLMJudgeEvaluator,
    ComprehensiveEvaluation,
)

logger = logging.getLogger(__name__)


# Benchmark queries designed for the personal knowledge base
# Categories: ideas, learning, personal, saved
# Years: 2020-2025
# Content: habits, philosophy, productivity, learning methods, mental models
#
# Difficulty levels per paper:
#   Easy (2): Year-filtered specific queries
#   Medium (3): Cross-domain synthesis
#   Hard (5): Pattern synthesis, exploratory
BENCHMARK_QUERIES = [
    # === HARD: Temporal progression across all years ===
    {
        "id": "Q1",
        "query": "How has my approach to learning and personal growth evolved from 2020 to 2025?",
        "expected": {
            "type": "temporal_progression",
            "difficulty": "hard",
            "years": [2020, 2021, 2022, 2023, 2024, 2025],
            "categories": ["learning", "personal"],
            "requires": "temporal_synthesis",
        },
    },
    # === MEDIUM: Cross-domain synthesis ===
    {
        "id": "Q2",
        "query": "What connections exist between my learning methods and personal productivity habits?",
        "expected": {
            "type": "cross_domain",
            "difficulty": "medium",
            "categories": ["learning", "personal", "ideas"],
            "requires": "cross_domain_synthesis",
        },
    },
    # === MEDIUM: Synthesis with narrative ===
    {
        "id": "Q3",
        "query": "How do the mental models I've documented relate to my daily practices?",
        "expected": {
            "type": "synthesis",
            "difficulty": "medium",
            "categories": ["ideas", "personal"],
            "requires": "narrative",
        },
    },
    # === EASY: Year-specific query ===
    {
        "id": "Q4",
        "query": "What did I learn about habits and learning techniques in 2021?",
        "expected": {
            "type": "specific",
            "difficulty": "easy",
            "years": [2021],
            "categories": ["learning"],
            "requires": "year_filtered",
        },
    },
    # === EASY: Year-specific query ===
    {
        "id": "Q5",
        "query": "What were my key personal reflections and insights in 2023?",
        "expected": {
            "type": "specific",
            "difficulty": "easy",
            "years": [2023],
            "categories": ["personal"],
            "requires": "year_filtered",
        },
    },
    # === HARD: Temporal comparison ===
    {
        "id": "Q6",
        "query": "How did my focus areas differ between 2020 and 2024?",
        "expected": {
            "type": "temporal_comparison",
            "difficulty": "hard",
            "years": [2020, 2024],
            "requires": "comparison",
        },
    },
    # === HARD: Exploratory pattern synthesis ===
    {
        "id": "Q7",
        "query": "What patterns connect my learning, ideas, and personal growth?",
        "expected": {
            "type": "discovery",
            "difficulty": "hard",
            "categories": ["learning", "ideas", "personal"],
            "requires": "pattern_synthesis",
        },
    },
    # === MEDIUM: Cross-domain bridging ===
    {
        "id": "Q8",
        "query": "How do saved articles and external ideas influence my personal philosophy?",
        "expected": {
            "type": "cross_domain",
            "difficulty": "medium",
            "categories": ["saved", "ideas", "personal"],
            "requires": "bridging",
        },
    },
    # === HARD: Philosophy-technical bridge ===
    {
        "id": "Q9",
        "query": "What philosophical concepts influenced my technical learning approach?",
        "expected": {
            "type": "cross_domain",
            "difficulty": "hard",
            "categories": ["learning", "saved", "personal"],
            "requires": "multi_hop",
        },
    },
    # === HARD: Comprehensive overview ===
    {
        "id": "Q10",
        "query": "Create a comprehensive overview of the key themes and insights across all my notes",
        "expected": {
            "type": "full_synthesis",
            "difficulty": "hard",
            "scope": "all",
            "categories": ["ideas", "learning", "personal", "saved"],
            "requires": "comprehensive",
        },
    },
]


@dataclass
class BenchmarkResult:
    """Result for a single benchmark query."""

    query_id: str
    query: str
    expected: Dict[str, Any]

    # Answer result
    answer: Optional[EnhancedAnswer] = None

    # Evaluation scores
    evaluation: Optional[ComprehensiveEvaluation] = None

    # Timing
    latency_ms: float = 0.0

    # Query understanding metrics
    query_type_detected: str = ""
    year_filter_detected: Optional[int] = None
    category_filter_detected: Optional[str] = None

    # Success flags
    retrieval_success: bool = False
    generation_success: bool = False
    type_detection_correct: bool = False

    # Error info
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "expected": self.expected,
            "latency_ms": self.latency_ms,
            "query_type_detected": self.query_type_detected,
            "year_filter_detected": self.year_filter_detected,
            "category_filter_detected": self.category_filter_detected,
            "retrieval_success": self.retrieval_success,
            "generation_success": self.generation_success,
            "type_detection_correct": self.type_detection_correct,
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "error": self.error,
        }


@dataclass
class BenchmarkAggregate:
    """Aggregated benchmark results."""

    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0

    # Average scores
    avg_synthesis_score: float = 0.0
    avg_cross_domain_score: float = 0.0
    avg_multi_hop_score: float = 0.0
    avg_temporal_score: float = 0.0
    avg_overall_score: float = 0.0

    # Performance metrics
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0

    # Type detection accuracy
    type_detection_accuracy: float = 0.0

    # Coverage
    years_coverage: Dict[int, int] = field(default_factory=dict)
    categories_coverage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "avg_synthesis_score": self.avg_synthesis_score,
            "avg_cross_domain_score": self.avg_cross_domain_score,
            "avg_multi_hop_score": self.avg_multi_hop_score,
            "avg_temporal_score": self.avg_temporal_score,
            "avg_overall_score": self.avg_overall_score,
            "avg_latency_ms": self.avg_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "min_latency_ms": self.min_latency_ms,
            "type_detection_accuracy": self.type_detection_accuracy,
            "years_coverage": self.years_coverage,
            "categories_coverage": self.categories_coverage,
        }


@dataclass
class BenchmarkResults:
    """Complete benchmark results."""

    results: List[BenchmarkResult] = field(default_factory=list)
    aggregate: Optional[BenchmarkAggregate] = None

    # Metadata
    benchmark_name: str = "MNEME Benchmark"
    timestamp: str = ""
    total_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "benchmark_name": self.benchmark_name,
            "timestamp": self.timestamp,
            "total_time_ms": self.total_time_ms,
            "results": [r.to_dict() for r in self.results],
            "aggregate": self.aggregate.to_dict() if self.aggregate else None,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, filepath: str) -> None:
        """Save results to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
        logger.info(f"Benchmark results saved to {filepath}")


class BenchmarkRunner:
    """
    Runs benchmark queries WITHOUT keyword or category hints.

    Tests the system's ability to understand and handle natural
    language queries without explicit guidance.
    """

    def __init__(
        self,
        mneme: "MNEME",
        evaluator: Optional[LLMJudgeEvaluator] = None,
    ):
        """
        Initialize benchmark runner.

        Args:
            mneme: MNEME instance to benchmark
            evaluator: Optional LLM judge evaluator
        """
        self.mneme = mneme
        self.evaluator = evaluator

        logger.info("BenchmarkRunner initialized")

    def run_benchmark(
        self,
        queries: Optional[List[Dict]] = None,
        verbose: bool = False,
    ) -> BenchmarkResults:
        """
        Run all benchmark queries and evaluate.

        Tests:
        - Retrieval quality
        - Answer quality (synthesis, cross-domain, multi-hop)
        - Model selection appropriateness
        - Citation accuracy

        Args:
            queries: Optional custom queries (default: BENCHMARK_QUERIES)
            verbose: Whether to print progress

        Returns:
            BenchmarkResults with all metrics
        """
        queries = queries or BENCHMARK_QUERIES
        results = []

        total_start = time.time()

        for i, q in enumerate(queries):
            if verbose:
                logger.info(f"Running query {i+1}/{len(queries)}: {q['id']}")

            result = self._run_single_query(q)
            results.append(result)

            if verbose:
                status = "SUCCESS" if result.generation_success else "FAILED"
                logger.info(f"  {status} - {result.latency_ms:.0f}ms")

        total_time_ms = (time.time() - total_start) * 1000

        # Aggregate results
        aggregate = self._aggregate_results(results)

        # Build final results
        from datetime import datetime
        benchmark_results = BenchmarkResults(
            results=results,
            aggregate=aggregate,
            timestamp=datetime.now().isoformat(),
            total_time_ms=total_time_ms,
        )

        logger.info(
            f"Benchmark complete: {aggregate.successful_queries}/{aggregate.total_queries} "
            f"successful, avg score: {aggregate.avg_overall_score:.3f}"
        )

        return benchmark_results

    def _run_single_query(self, query_spec: Dict) -> BenchmarkResult:
        """Run a single benchmark query."""
        query_id = query_spec["id"]
        query = query_spec["query"]
        expected = query_spec["expected"]

        result = BenchmarkResult(
            query_id=query_id,
            query=query,
            expected=expected,
        )

        start_time = time.time()

        try:
            # Run query WITHOUT hints - let the system figure it out
            answer = self.mneme.query(query)

            result.latency_ms = (time.time() - start_time) * 1000
            result.answer = answer
            result.generation_success = answer.is_successful

            # Extract detected query info
            result.query_type_detected = answer.query_type
            result.year_filter_detected = answer.year_filter
            result.category_filter_detected = answer.category_filter

            # Check type detection
            result.type_detection_correct = self._check_type_detection(
                expected, answer.query_type
            )

            # Retrieval success
            result.retrieval_success = answer.num_citations > 0

            # Run LLM evaluation if available
            if self.evaluator and answer.citations:
                # Determine evaluation flags from expected type
                requires = expected.get("requires", "")
                is_multi_hop = requires == "multi_hop"
                is_cross_domain = "cross_domain" in expected.get("type", "")

                # CRITICAL FIX: Pass actual sources to evaluator, not empty list
                # Sources come from retrieval_result.candidates (ScoredChunk objects)
                sources = []
                if hasattr(answer, 'retrieval_result') and answer.retrieval_result:
                    sources = answer.retrieval_result.candidates

                result.evaluation = self.evaluator.comprehensive_evaluation(
                    answer=answer.answer,
                    sources=sources,
                    year_filter=result.year_filter_detected,
                    expected_categories=set(expected.get("categories", [])),
                    is_multi_hop=is_multi_hop,
                    is_cross_domain=is_cross_domain,
                )

        except Exception as e:
            result.latency_ms = (time.time() - start_time) * 1000
            result.error = str(e)
            result.generation_success = False
            logger.error(f"Query {query_id} failed: {e}")

        return result

    def _check_type_detection(
        self,
        expected: Dict,
        detected_type: str,
    ) -> bool:
        """Check if query type was correctly detected."""
        expected_type = expected.get("type", "")

        # Map expected benchmark types to valid query classifier outputs
        type_mapping = {
            "temporal_progression": ["temporal", "synthesis", "exploratory"],
            "cross_domain": ["synthesis", "comparison", "exploratory"],
            "synthesis": ["synthesis", "exploratory"],
            "specific": ["temporal", "specific"],
            "temporal_comparison": ["temporal", "comparison", "synthesis"],
            "discovery": ["exploratory", "synthesis"],
            "full_synthesis": ["synthesis", "exploratory"],
        }

        valid_types = type_mapping.get(expected_type, [expected_type])
        return detected_type in valid_types

    def _aggregate_results(
        self,
        results: List[BenchmarkResult],
    ) -> BenchmarkAggregate:
        """Aggregate benchmark results."""
        aggregate = BenchmarkAggregate()

        aggregate.total_queries = len(results)
        aggregate.successful_queries = sum(1 for r in results if r.generation_success)
        aggregate.failed_queries = aggregate.total_queries - aggregate.successful_queries

        # Latency stats
        latencies = [r.latency_ms for r in results if r.latency_ms > 0]
        if latencies:
            aggregate.avg_latency_ms = sum(latencies) / len(latencies)
            aggregate.max_latency_ms = max(latencies)
            aggregate.min_latency_ms = min(latencies)

        # Type detection accuracy
        correct_types = sum(1 for r in results if r.type_detection_correct)
        aggregate.type_detection_accuracy = correct_types / len(results) if results else 0

        # Evaluation scores
        synthesis_scores = []
        cross_domain_scores = []
        multi_hop_scores = []
        temporal_scores = []
        overall_scores = []

        for r in results:
            if r.evaluation:
                synthesis_scores.append(r.evaluation.synthesis.final_score)
                overall_scores.append(r.evaluation.overall_score)

                if r.evaluation.cross_domain:
                    cross_domain_scores.append(r.evaluation.cross_domain.final_score)
                if r.evaluation.multi_hop:
                    multi_hop_scores.append(r.evaluation.multi_hop.final_score)
                if r.evaluation.temporal:
                    temporal_scores.append(r.evaluation.temporal.final_score)

        if synthesis_scores:
            aggregate.avg_synthesis_score = sum(synthesis_scores) / len(synthesis_scores)
        if cross_domain_scores:
            aggregate.avg_cross_domain_score = sum(cross_domain_scores) / len(cross_domain_scores)
        if multi_hop_scores:
            aggregate.avg_multi_hop_score = sum(multi_hop_scores) / len(multi_hop_scores)
        if temporal_scores:
            aggregate.avg_temporal_score = sum(temporal_scores) / len(temporal_scores)
        if overall_scores:
            aggregate.avg_overall_score = sum(overall_scores) / len(overall_scores)

        # Coverage analysis
        for r in results:
            if r.answer:
                for year in r.answer.years_covered:
                    aggregate.years_coverage[year] = aggregate.years_coverage.get(year, 0) + 1
                for cat in r.answer.categories_covered:
                    aggregate.categories_coverage[cat] = aggregate.categories_coverage.get(cat, 0) + 1

        return aggregate


def run_benchmark(
    mneme: "MNEME",
    evaluator: Optional[LLMJudgeEvaluator] = None,
    queries: Optional[List[Dict]] = None,
    verbose: bool = True,
) -> BenchmarkResults:
    """
    Convenience function to run benchmark.

    Args:
        mneme: MNEME instance
        evaluator: Optional LLM judge
        queries: Custom queries (default: BENCHMARK_QUERIES)
        verbose: Print progress

    Returns:
        BenchmarkResults
    """
    runner = BenchmarkRunner(mneme, evaluator)
    return runner.run_benchmark(queries, verbose)


# Quick test function
def quick_test(mneme: "MNEME") -> Dict[str, Any]:
    """
    Run a quick test with 3 representative queries.

    Args:
        mneme: MNEME instance

    Returns:
        Quick test results
    """
    quick_queries = [
        BENCHMARK_QUERIES[0],  # Temporal
        BENCHMARK_QUERIES[2],  # Synthesis
        BENCHMARK_QUERIES[3],  # Multi-hop
    ]

    runner = BenchmarkRunner(mneme, None)
    results = runner.run_benchmark(quick_queries, verbose=True)

    return {
        "queries_run": len(quick_queries),
        "successful": results.aggregate.successful_queries,
        "avg_latency_ms": results.aggregate.avg_latency_ms,
        "type_detection_accuracy": results.aggregate.type_detection_accuracy,
    }
