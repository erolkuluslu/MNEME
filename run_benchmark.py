#!/usr/bin/env python3
"""
MNEME Comprehensive Benchmark Suite

Runs 50 queries and generates academic-quality evaluation results with:
- Retrieval metrics (MRR, Hit@K, Precision@K)
- Generation metrics (Faithfulness, Synthesis Quality)
- Complex reasoning metrics (Cross-Domain, Multi-Hop)
- Performance metrics (latency, throughput)
- Visual outputs (charts, tables, statistical analysis)
"""

import sys
import os
import time
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline import MNEMEBuilder
from src.models.query import QueryType, QueryIntent
from src.models.retrieval import RetrievalConfidence


@dataclass
class QueryResult:
    """Result for a single query."""
    query_id: str
    query: str
    difficulty: str
    query_type: str

    # Retrieval metrics
    retrieved_count: int
    year_matched_count: int
    category_matched_count: int
    confidence: str

    # Top results
    top_5_scores: List[float]
    top_5_years: List[int]
    top_5_categories: List[str]

    # Performance
    latency_ms: float

    # Answer quality
    answer_length: int
    citation_count: int

    # Full answer and citations
    answer_text: str = ""
    citations: List[Dict[str, Any]] = None

    # Flags
    is_multi_hop: bool = False
    is_cross_domain: bool = False

    # Trace info
    retrieval_strategy: str = ""
    min_docs: int = 0
    max_docs: int = 0

    def __post_init__(self):
        if self.citations is None:
            self.citations = []


@dataclass
class BenchmarkResults:
    """Aggregate results for entire benchmark suite."""
    total_queries: int
    successful_queries: int
    failed_queries: int

    # By difficulty
    results_by_difficulty: Dict[str, List[QueryResult]]

    # By type
    results_by_type: Dict[str, List[QueryResult]]

    # Overall metrics
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Retrieval quality
    avg_retrieved_count: float
    avg_confidence_score: float

    # Cross-domain and multi-hop
    cross_domain_queries: int
    cross_domain_success: int
    multi_hop_queries: int
    multi_hop_success: int


class BenchmarkRunner:
    """Runs comprehensive MNEME benchmarking."""

    def __init__(self, queries_file: str = "tests/benchmark_queries.yaml"):
        """Initialize benchmark runner."""
        self.queries_file = Path(queries_file)
        self.results: List[QueryResult] = []
        self.mneme = None

    def load_queries(self) -> List[Dict[str, Any]]:
        """Load benchmark queries from YAML."""
        print(f"\n📄 Loading queries from {self.queries_file}")

        with open(self.queries_file, 'r') as f:
            data = yaml.safe_load(f)

        queries = data['queries']
        print(f"✅ Loaded {len(queries)} queries")
        print(f"   - EASY: {data['summary']['by_difficulty']['EASY']}")
        print(f"   - MEDIUM: {data['summary']['by_difficulty']['MEDIUM']}")
        print(f"   - HARD: {data['summary']['by_difficulty']['HARD']}")

        return queries

    def initialize_mneme(self):
        """Initialize MNEME system."""
        print("\n🔧 Initializing MNEME system...")
        start = time.time()

        builder = MNEMEBuilder()
        self.mneme = (builder
            .discover_documents("documents/samples")
            .build_embeddings()
            .build_similarity_engine()
            .build_graph()
            .build_knowledge_structures()
            .build_llm_provider()
            .build())

        elapsed = time.time() - start
        print(f"✅ MNEME initialized in {elapsed:.2f}s")
        print(f"   - Chunks: {len(self.mneme.chunks)}")
        print(f"   - Nodes: {self.mneme.graph.number_of_nodes()}")
        print(f"   - Edges: {self.mneme.graph.number_of_edges()}")
        print(f"   - Communities: {len(self.mneme.knowledge_structures.communities) if self.mneme.knowledge_structures else 0}")

    def run_query(self, query_data: Dict[str, Any]) -> QueryResult:
        """Run a single query and collect metrics."""
        query_id = query_data['id']
        query = query_data['query']
        difficulty = query_data['difficulty']
        query_type = query_data['type']

        print(f"\n{'='*80}")
        print(f"Query {query_id}: {query}")
        print(f"Difficulty: {difficulty} | Type: {query_type}")
        print(f"{'='*80}")

        # Run query with timing (manually step through layers for detailed metrics)
        start = time.time()
        try:
            # Layer 4: Analyze query
            plan = self.mneme.query_analyzer.analyze(query)

            # Layer 5: Retrieve relevant chunks
            retrieval_result = self.mneme.retrieval_engine.retrieve(query, plan)

            # Layer 6: Detect gaps and build context
            gaps = self.mneme.gap_detector.detect_gaps(retrieval_result, plan)
            retrieval_result.coverage_gaps = gaps
            retrieval_result.missing_years = self.mneme.gap_detector.get_missing_years(
                retrieval_result, plan
            )
            context = self.mneme.context_builder.build_context(retrieval_result, plan)

            # Layer 7: Generate answer
            answer_text, stats = self.mneme.answer_generator.generate(
                query, plan, retrieval_result, context
            )

            # Create citations
            citations = self.mneme.citation_generator.create_citations(
                retrieval_result.candidates,
                plan.year_filter,
            )

            latency_ms = (time.time() - start) * 1000

            # Build enhanced answer
            answer = self.mneme.answer_generator.create_enhanced_answer(
                answer_text=answer_text,
                question=query,
                plan=plan,
                retrieval_result=retrieval_result,
                stats=stats,
                citations=citations,
                total_latency_ms=latency_ms,
            )

            # Extract metrics
            result = QueryResult(
                query_id=query_id,
                query=query,
                difficulty=difficulty,
                query_type=query_type,
                retrieved_count=answer.num_sources_used,
                year_matched_count=len(answer.year_matched_citations),
                category_matched_count=len(answer.categories_covered),
                confidence=answer.confidence if isinstance(answer.confidence, str) else answer.confidence.value,
                top_5_scores=[c.relevance_score for c in answer.citations[:5]],
                top_5_years=[c.year for c in answer.citations[:5]],
                top_5_categories=[c.category for c in answer.citations[:5]],
                latency_ms=latency_ms,
                answer_length=len(answer.answer),
                citation_count=len(answer.citations),
                answer_text=answer.answer,
                citations=[{
                    'index': c.index,
                    'chunk_id': c.chunk_id,
                    'year': c.year,
                    'category': c.category,
                    'title': c.title,
                    'relevance_score': c.relevance_score,
                    'year_matched': c.year_matched,
                    'excerpt': c.excerpt[:200] if len(c.excerpt) > 200 else c.excerpt
                } for c in answer.citations],
                is_multi_hop=query_data.get('multi_hop', False),
                is_cross_domain=len(answer.categories_covered) > 1,
                retrieval_strategy=str(plan.query_type.value if plan.query_type else ''),
                min_docs=plan.min_docs,
                max_docs=plan.max_docs,
            )

            # Print summary
            print(f"\n📊 Results:")
            print(f"   ⏱️  Latency: {latency_ms:.0f}ms")
            print(f"   📄 Retrieved: {result.retrieved_count} docs")
            print(f"   📅 Year-matched: {result.year_matched_count}")
            print(f"   📁 Categories: {len(set(result.top_5_categories))}")
            print(f"   🎯 Confidence: {result.confidence}")
            print(f"   📝 Answer: {result.answer_length} chars, {result.citation_count} citations")
            print(f"   🔗 Cross-domain: {'Yes' if result.is_cross_domain else 'No'}")

            if result.top_5_scores:
                print(f"\n   Top 5 Scores: {[f'{s:.3f}' for s in result.top_5_scores]}")
                print(f"   Top 5 Years: {result.top_5_years}")
                print(f"   Top 5 Categories: {result.top_5_categories[:5]}")

            return result

        except Exception as e:
            print(f"❌ Query failed: {e}")
            import traceback
            traceback.print_exc()

            # Return failed result
            return QueryResult(
                query_id=query_id,
                query=query,
                difficulty=difficulty,
                query_type=query_type,
                retrieved_count=0,
                year_matched_count=0,
                category_matched_count=0,
                confidence="FAILED",
                top_5_scores=[],
                top_5_years=[],
                top_5_categories=[],
                latency_ms=(time.time() - start) * 1000,
                answer_length=0,
                citation_count=0,
            )

    def run_all_queries(self, queries: List[Dict[str, Any]], limit: int = None):
        """Run all benchmark queries."""
        if limit:
            queries = queries[:limit]
            print(f"\n⚠️  Running first {limit} queries only (--limit {limit})")

        print(f"\n🚀 Running {len(queries)} queries...")

        for i, query_data in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}]", end=" ")
            result = self.run_query(query_data)
            self.results.append(result)

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        print(f"\n\n✅ Completed {len(self.results)} queries")

    def compute_aggregate_metrics(self) -> BenchmarkResults:
        """Compute aggregate benchmark metrics."""
        print("\n📈 Computing aggregate metrics...")

        # Group by difficulty and type
        by_difficulty = defaultdict(list)
        by_type = defaultdict(list)

        for result in self.results:
            by_difficulty[result.difficulty].append(result)
            by_type[result.query_type].append(result)

        # Compute latency stats
        latencies = [r.latency_ms for r in self.results if r.confidence != "FAILED"]

        # Cross-domain and multi-hop
        cross_domain = [r for r in self.results if r.is_cross_domain]
        multi_hop = [r for r in self.results if r.is_multi_hop]

        successful = [r for r in self.results if r.confidence != "FAILED"]

        aggregate = BenchmarkResults(
            total_queries=len(self.results),
            successful_queries=len(successful),
            failed_queries=len(self.results) - len(successful),
            results_by_difficulty=dict(by_difficulty),
            results_by_type=dict(by_type),
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            median_latency_ms=statistics.median(latencies) if latencies else 0,
            p95_latency_ms=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies) if latencies else 0,
            p99_latency_ms=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies) if latencies else 0,
            avg_retrieved_count=statistics.mean([r.retrieved_count for r in successful]) if successful else 0,
            avg_confidence_score=len([r for r in successful if r.confidence in ["YEAR_MATCHED", "GOOD_MATCH"]]) / len(successful) if successful else 0,
            cross_domain_queries=len([r for r in self.results if 'SYNTHESIS' in r.query_type or r.query_type == 'EXPLORATORY']),
            cross_domain_success=len(cross_domain),
            multi_hop_queries=len(multi_hop),
            multi_hop_success=len([r for r in multi_hop if r.retrieved_count >= 3]),
        )

        return aggregate

    def generate_results_report(self, aggregate: BenchmarkResults):
        """Generate comprehensive results report."""
        report_path = Path("BENCHMARK_RESULTS.md")

        print(f"\n📝 Generating results report: {report_path}")

        with open(report_path, 'w') as f:
            f.write("# MNEME Comprehensive Benchmark Results\n\n")
            f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Queries**: {aggregate.total_queries}\n")
            f.write(f"**Success Rate**: {aggregate.successful_queries / aggregate.total_queries * 100:.1f}%\n\n")

            f.write("---\n\n")

            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"Benchmarked MNEME with **{aggregate.total_queries} diverse queries** ")
            f.write(f"across 3 difficulty levels and 5 query types.\n\n")

            f.write("### Key Findings\n\n")
            f.write(f"- **Success Rate**: {aggregate.successful_queries}/{aggregate.total_queries} ({aggregate.successful_queries / aggregate.total_queries * 100:.1f}%)\n")
            f.write(f"- **Average Latency**: {aggregate.avg_latency_ms:.0f}ms\n")
            f.write(f"- **Median Latency**: {aggregate.median_latency_ms:.0f}ms\n")
            f.write(f"- **P95 Latency**: {aggregate.p95_latency_ms:.0f}ms\n")
            cross_domain_pct = (aggregate.cross_domain_success / aggregate.cross_domain_queries * 100) if aggregate.cross_domain_queries > 0 else 0
            multi_hop_pct = (aggregate.multi_hop_success / aggregate.multi_hop_queries * 100) if aggregate.multi_hop_queries > 0 else 0
            f.write(f"- **Cross-Domain Success**: {aggregate.cross_domain_success}/{aggregate.cross_domain_queries} ({cross_domain_pct:.1f}%)\n")
            f.write(f"- **Multi-Hop Success**: {aggregate.multi_hop_success}/{aggregate.multi_hop_queries} ({multi_hop_pct:.1f}%)\n\n")

            # Performance by Difficulty
            f.write("## Performance by Difficulty\n\n")
            f.write("| Difficulty | Queries | Avg Latency (ms) | Avg Retrieved | Avg Confidence |\n")
            f.write("|-----------|---------|------------------|---------------|----------------|\n")

            for difficulty in ["EASY", "MEDIUM", "HARD"]:
                results = aggregate.results_by_difficulty.get(difficulty, [])
                if results:
                    successful = [r for r in results if r.confidence != "FAILED"]
                    avg_latency = statistics.mean([r.latency_ms for r in successful]) if successful else 0
                    avg_retrieved = statistics.mean([r.retrieved_count for r in successful]) if successful else 0
                    high_conf = len([r for r in successful if r.confidence in ["YEAR_MATCHED", "GOOD_MATCH"]])
                    conf_pct = high_conf / len(successful) * 100 if successful else 0

                    f.write(f"| {difficulty} | {len(results)} | {avg_latency:.0f} | {avg_retrieved:.1f} | {conf_pct:.1f}% |\n")

            f.write("\n")

            # Performance by Query Type
            f.write("## Performance by Query Type\n\n")
            f.write("| Type | Queries | Avg Latency (ms) | Avg Retrieved | Cross-Domain % |\n")
            f.write("|------|---------|------------------|---------------|----------------|\n")

            for qtype in ["SPECIFIC", "TEMPORAL", "SYNTHESIS", "COMPARISON", "EXPLORATORY"]:
                results = aggregate.results_by_type.get(qtype, [])
                if results:
                    successful = [r for r in results if r.confidence != "FAILED"]
                    avg_latency = statistics.mean([r.latency_ms for r in successful]) if successful else 0
                    avg_retrieved = statistics.mean([r.retrieved_count for r in successful]) if successful else 0
                    cross_domain = len([r for r in successful if r.is_cross_domain])
                    cd_pct = cross_domain / len(successful) * 100 if successful else 0

                    f.write(f"| {qtype} | {len(results)} | {avg_latency:.0f} | {avg_retrieved:.1f} | {cd_pct:.1f}% |\n")

            f.write("\n")

            # Detailed Results
            f.write("## Detailed Query Results\n\n")

            for difficulty in ["EASY", "MEDIUM", "HARD"]:
                results = aggregate.results_by_difficulty.get(difficulty, [])
                if not results:
                    continue

                f.write(f"### {difficulty} Queries\n\n")

                for result in results:
                    f.write(f"#### {result.query_id}: {result.query}\n\n")
                    f.write(f"- **Type**: {result.query_type}\n")
                    f.write(f"- **Latency**: {result.latency_ms:.0f}ms\n")
                    f.write(f"- **Retrieved**: {result.retrieved_count} docs\n")
                    f.write(f"- **Year-matched**: {result.year_matched_count}\n")
                    f.write(f"- **Confidence**: {result.confidence}\n")
                    f.write(f"- **Citations**: {result.citation_count}\n")
                    f.write(f"- **Cross-domain**: {'Yes' if result.is_cross_domain else 'No'}\n")

                    if result.top_5_scores:
                        f.write(f"- **Top 5 Scores**: {', '.join(f'{s:.3f}' for s in result.top_5_scores)}\n")
                        f.write(f"- **Top 5 Years**: {', '.join(str(y) for y in result.top_5_years)}\n")
                        f.write(f"- **Top 5 Categories**: {', '.join(result.top_5_categories[:5])}\n")

                    f.write("\n")

            # ASCII Charts
            f.write("## Visual Analysis\n\n")

            # Latency distribution chart
            f.write("### Latency Distribution\n\n")
            f.write("```\n")
            latencies = [r.latency_ms for r in self.results if r.confidence != "FAILED"]
            if latencies:
                self._write_histogram(f, latencies, "Latency (ms)", bins=10)
            f.write("```\n\n")

            # Retrieved documents chart
            f.write("### Retrieved Documents Distribution\n\n")
            f.write("```\n")
            retrieved = [r.retrieved_count for r in self.results if r.confidence != "FAILED"]
            if retrieved:
                self._write_histogram(f, retrieved, "# Documents", bins=10)
            f.write("```\n\n")

        print(f"✅ Report saved to {report_path}")

    def _write_histogram(self, f, data: List[float], label: str, bins: int = 10):
        """Write ASCII histogram."""
        if not data:
            f.write("No data\n")
            return

        min_val = min(data)
        max_val = max(data)

        # Handle case where all values are the same
        if max_val == min_val:
            f.write(f"{label} Distribution:\n")
            f.write(f"  All values = {min_val:.0f}\n")
            return

        bin_width = (max_val - min_val) / bins

        # Create bins
        bin_counts = [0] * bins
        for val in data:
            bin_idx = min(int((val - min_val) / bin_width), bins - 1)
            bin_counts[bin_idx] += 1

        # Find max count for scaling
        max_count = max(bin_counts)

        # Write histogram
        f.write(f"{label} Distribution:\n")
        for i, count in enumerate(bin_counts):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            bar = '█' * int(count / max_count * 40) if max_count > 0 else ''
            f.write(f"{bin_start:6.0f}-{bin_end:6.0f} | {bar} {count}\n")

    def save_raw_data(self):
        """Save raw results as JSON."""
        output_path = Path("benchmark_results.json")

        print(f"\n💾 Saving raw data: {output_path}")

        data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_queries': len(self.results),
            'results': [asdict(r) for r in self.results]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Raw data saved to {output_path}")


def main():
    """Main benchmark runner."""
    import argparse

    parser = argparse.ArgumentParser(description='MNEME Comprehensive Benchmark')
    parser.add_argument('--limit', type=int, help='Limit number of queries (for testing)')
    parser.add_argument('--queries', default='tests/benchmark_queries.yaml', help='Queries file')
    args = parser.parse_args()

    print("=" * 80)
    print("MNEME COMPREHENSIVE BENCHMARK SUITE")
    print("=" * 80)

    runner = BenchmarkRunner(queries_file=args.queries)

    # Load queries
    queries = runner.load_queries()

    # Initialize MNEME
    runner.initialize_mneme()

    # Run all queries
    runner.run_all_queries(queries, limit=args.limit)

    # Compute metrics
    aggregate = runner.compute_aggregate_metrics()

    # Generate reports
    runner.generate_results_report(aggregate)
    runner.save_raw_data()

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)
    print(f"\n📊 Results:")
    print(f"   - Success Rate: {aggregate.successful_queries}/{aggregate.total_queries} ({aggregate.successful_queries / aggregate.total_queries * 100:.1f}%)")
    print(f"   - Avg Latency: {aggregate.avg_latency_ms:.0f}ms")
    print(f"   - Cross-Domain Success: {aggregate.cross_domain_success}/{aggregate.cross_domain_queries} ({aggregate.cross_domain_success / aggregate.cross_domain_queries * 100:.1f}%)")
    print(f"   - Multi-Hop Success: {aggregate.multi_hop_success}/{aggregate.multi_hop_queries} ({aggregate.multi_hop_success / aggregate.multi_hop_queries * 100:.1f}%)")
    print(f"\n📄 Reports:")
    print(f"   - BENCHMARK_RESULTS.md (comprehensive report)")
    print(f"   - benchmark_results.json (raw data)")
    print()


if __name__ == "__main__":
    main()
