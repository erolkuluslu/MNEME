#!/usr/bin/env python3
"""
Hard 10-Query Benchmark Runner

Tests critical functionality and edge cases with focused set of hard queries.
"""

import yaml
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline import MNEMEBuilder
from src.config import MNEMEConfig
from src.evaluation.benchmark import BenchmarkRunner
from src.evaluation.llm_judge import LLMJudgeEvaluator


def load_hard_queries():
    """Load hard benchmark queries from YAML."""
    queries_file = Path(__file__).parent / "tests" / "hard_benchmark_queries.yaml"

    with open(queries_file, 'r') as f:
        data = yaml.safe_load(f)

    # Convert to benchmark query format
    benchmark_queries = []
    for q in data['queries']:
        benchmark_queries.append({
            'id': q['id'],
            'query': q['query'],
            'expected': q['expected']
        })

    return benchmark_queries


def print_summary(results):
    """Print benchmark summary."""
    print("\n" + "="*80)
    print("HARD BENCHMARK SUMMARY")
    print("="*80)

    agg = results.aggregate

    print(f"\n📊 Overall Performance:")
    print(f"  Total Queries:     {agg.total_queries}")
    print(f"  Successful:        {agg.successful_queries}/{agg.total_queries} ({agg.successful_queries/agg.total_queries*100:.1f}%)")
    print(f"  Failed:            {agg.failed_queries}")

    print(f"\n⏱️  Latency:")
    print(f"  Average:           {agg.avg_latency_ms:.0f}ms")
    print(f"  Min:               {agg.min_latency_ms:.0f}ms")
    print(f"  Max:               {agg.max_latency_ms:.0f}ms")

    print(f"\n🎯 Query Type Detection:")
    print(f"  Accuracy:          {agg.type_detection_accuracy*100:.1f}%")

    print(f"\n📈 Quality Scores:")
    print(f"  Synthesis:         {agg.avg_synthesis_score:.3f}")
    print(f"  Cross-Domain:      {agg.avg_cross_domain_score:.3f}")
    print(f"  Multi-Hop:         {agg.avg_multi_hop_score:.3f}")
    print(f"  Temporal:          {agg.avg_temporal_score:.3f}")
    print(f"  Overall:           {agg.avg_overall_score:.3f}")

    print(f"\n🔗 Multi-Hop Success (NEW METRIC):")
    print(f"  Successful:        {agg.multi_hop_successful}/{agg.multi_hop_total} ({agg.multi_hop_successful/agg.multi_hop_total*100:.1f}%)")
    print(f"  (Answers with ≥3 unique sources)")

    # Individual query results
    print(f"\n📋 Individual Results:")
    for result in results.results:
        status = "✅" if result.generation_success else "❌"
        multi_hop = ""
        if result.evaluation and result.evaluation.multi_hop:
            sources = result.evaluation.multi_hop.unique_sources_cited
            multi_hop = f" | {sources} sources"

        print(f"  {status} {result.query_id}: {result.query[:60]}... ({result.latency_ms:.0f}ms{multi_hop})")

    print("\n" + "="*80)


def main():
    """Run hard benchmark."""
    print("🔧 Building MNEME pipeline...")

    # Initialize MNEME with community summaries
    config = MNEMEConfig.for_development()
    config.use_community_summaries = True

    # Build pipeline
    builder = MNEMEBuilder(config)
    builder.discover_documents("documents/samples")
    builder.build_embeddings()
    builder.build_similarity_engine()
    builder.build_graph()
    builder.build_knowledge_structures()
    builder.build_llm_provider()

    mneme = builder.build()

    print(f"✅ MNEME ready\n")

    # Load hard queries
    print("📋 Loading hard benchmark queries...")
    queries = load_hard_queries()
    print(f"✅ Loaded {len(queries)} hard queries\n")

    # Initialize evaluator using MNEME's LLM provider
    print("🔧 Initializing LLM evaluator...")
    evaluator = LLMJudgeEvaluator(llm_provider=mneme.llm_provider, config=config)
    print("✅ Evaluator ready\n")

    # Run benchmark
    print("🚀 Running hard benchmark...")
    print("="*80)

    runner = BenchmarkRunner(mneme, evaluator)
    results = runner.run_benchmark(queries, verbose=True)

    # Print summary
    print_summary(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results/hard_benchmark_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results.to_dict(), f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    # Return exit code based on success rate
    success_rate = results.aggregate.successful_queries / results.aggregate.total_queries
    if success_rate < 0.8:
        print(f"\n⚠️  Warning: Success rate {success_rate*100:.1f}% below 80% threshold")
        return 1

    print(f"\n✅ Success rate {success_rate*100:.1f}% meets 80% threshold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
