"""
MNEME Evaluation

Metrics and evaluation tools for the MNEME RAG system.
Includes LLM-as-judge evaluation and benchmark framework.
"""

# Metrics module not yet implemented
# from .metrics import (
#     mean_reciprocal_rank,
#     precision_at_k,
#     recall_at_k,
#     hit_at_k,
#     ndcg_at_k,
#     year_accuracy,
#     EvaluationMetrics,
# )

from .llm_judge import (
    LLMJudgeEvaluator,
    SynthesisQualityScore,
    CrossDomainScore,
    MultiHopScore,
    TemporalAccuracyScore,
    ComprehensiveEvaluation,
    create_llm_judge,
)

from .benchmark import (
    BENCHMARK_QUERIES,
    BenchmarkRunner,
    BenchmarkResult,
    BenchmarkAggregate,
    BenchmarkResults,
    run_benchmark,
    quick_test,
)

__all__ = [
    # Metrics (not yet implemented)
    # "mean_reciprocal_rank",
    # "precision_at_k",
    # "recall_at_k",
    # "hit_at_k",
    # "ndcg_at_k",
    # "year_accuracy",
    # "EvaluationMetrics",
    # LLM Judge
    "LLMJudgeEvaluator",
    "SynthesisQualityScore",
    "CrossDomainScore",
    "MultiHopScore",
    "TemporalAccuracyScore",
    "ComprehensiveEvaluation",
    "create_llm_judge",
    # Benchmark
    "BENCHMARK_QUERIES",
    "BenchmarkRunner",
    "BenchmarkResult",
    "BenchmarkAggregate",
    "BenchmarkResults",
    "run_benchmark",
    "quick_test",
]
