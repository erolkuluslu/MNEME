#!/usr/bin/env python3
"""
MNEME Demo - Interactive RAG Query System with Full Observability

Copyright (c) 2026 Erol Külüşlü, Akif Hasdemir, Furkan Yakkan, Gökhan Bakal
Licensed under the GNU Affero General Public License v3.0 (AGPLv3).
See LICENSE file for details.

Runnable entry point to test the MNEME 7-layer RAG system from the command line.
Provides observability into pipeline decisions, resource inspection, and query tracing.

Usage:
    python run_demo.py                              # Interactive mode
    python run_demo.py --query "What happened in AI in 2020?"  # Single query
    python run_demo.py --query "AI in 2021" --trace # With retrieval trace
    python run_demo.py --stats                      # Show stats only
    python run_demo.py --inspect                    # Full resource inspection
    python run_demo.py --visualize                  # Generate and open KG visualization
    python run_demo.py --trace                      # With retrieval trace                 


Interactive Commands:
    help       - Show available commands
    stats      - Show system statistics
    inspect    - Full resource inspection
    graph      - Show knowledge graph info
    hubs       - List hub nodes
    bridges    - List bridge nodes
    communities - Show community breakdown
    visualize  - Generate interactive KG visualization
    trace on/off - Toggle trace mode
    quit       - Exit the program
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent  # Go up to MNEME directory
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")  # PROJECT_ROOT is now MNEME directory

from src.config import MNEMEConfig
from src.pipeline import MNEMEBuilder
from src.utils import (
    setup_logging,
    inspect_chunks,
    inspect_embeddings,
    inspect_graph,
    inspect_communities,
    inspect_hubs,
    inspect_bridges,
    format_chunk_inspection,
    format_graph_inspection,
    format_community_inspection,
    format_hub_inspection,
    format_bridge_inspection,
    format_query_plan,
    format_retrieval_trace,
    format_thinking_trace,
    format_citations,
    format_answer_with_trace,
    visualize_mneme_graph,
)


def parse_args():
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace with docs, query, stats, trace, inspect, and verbose flags.
    """
    parser = argparse.ArgumentParser(
        description="MNEME RAG Demo - Interactive query system with full observability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_demo.py                              # Interactive mode
    python run_demo.py --query "What is AI?"        # Single query
    python run_demo.py --query "AI 2021" --trace    # Query with trace
    python run_demo.py --stats                      # Show stats only
    python run_demo.py --inspect                    # Full inspection
    python run_demo.py --docs ./my_docs             # Use custom documents

Interactive Commands:
    stats, inspect, graph, hubs, bridges, communities, trace on/off, help, quit
        """,
    )
    parser.add_argument(
        "--docs",
        type=str,
        default="documents/samples",
        help="Path to documents directory (default: documents/samples)",
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="Single query to execute (skips interactive mode)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show system stats and exit",
    )
    parser.add_argument(
        "--trace",
        "-t",
        action="store_true",
        help="Show detailed retrieval trace with scoring breakdown",
    )
    parser.add_argument(
        "--inspect",
        "-i",
        action="store_true",
        help="Show full resource inspection (chunks, graph, structures) and exit",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate interactive knowledge graph visualization and exit",
    )
    return parser.parse_args()


def build_mneme(document_path: str, verbose: bool = False):
    """
    Build the MNEME pipeline from documents.

    Discovers documents, generates embeddings, builds the similarity engine,
    constructs the knowledge graph, detects communities/hubs, and initializes
    the LLM provider for answer generation.

    Args:
        document_path: Path to documents directory containing source files.
        verbose: Enable debug logging for detailed build output.

    Returns:
        Configured MNEME instance ready for queries.

    Raises:
        Exception: If any build step fails (document discovery, embedding, etc.)
    """
    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)

    # Use development config
    config = MNEMEConfig.for_development()
    if not verbose:
        config.log_level = "INFO"

    print(f"\n🔧 Building MNEME pipeline from: {document_path}")
    print("-" * 50)

    builder = MNEMEBuilder(config)

    # Build pipeline step by step with progress
    print("[1/6] 📄 Discovering and chunking documents...")
    builder.discover_documents(document_path)

    print("[2/6] 🧮 Generating embeddings...")
    builder.build_embeddings()

    print("[3/6] 🔍 Building similarity search engine...")
    builder.build_similarity_engine()

    print("[4/6] 🕸️  Building knowledge graph...")
    builder.build_graph()

    print("[5/6] 🏘️  Building knowledge structures (communities, hubs)...")
    builder.build_knowledge_structures()

    print("[6/6] 🤖 Initializing LLM provider...")
    builder.build_llm_provider()

    mneme = builder.build()
    print("-" * 50)

    return mneme


def display_stats(mneme):
    """
    Display MNEME system statistics.

    Shows counts of chunks, nodes, edges, embedding dimensions,
    and available years/categories in the corpus.

    Args:
        mneme: The MNEME instance to get stats from.
    """
    stats = mneme.get_stats()

    print("\n📊 MNEME System Statistics")
    print("=" * 40)
    print(f"  Chunks:     {stats['num_chunks']:,}")
    print(f"  Nodes:      {stats['num_nodes']:,}")
    print(f"  Edges:      {stats['num_edges']:,}")
    print(f"  Embedding:  {stats['embedding_dimension']}d")
    print(f"  Years:      {sorted(stats['available_years'])}")
    print(f"  Categories: {sorted(stats['available_categories'])}")
    print("=" * 40)


def display_full_inspection(mneme):
    """
    Display comprehensive resource inspection.

    Shows detailed information about all MNEME resources:
    chunks, embeddings, graph, communities, hubs, and bridges.

    Args:
        mneme: The MNEME instance to inspect.
    """
    print("\n" + "=" * 60)
    print("🔬 MNEME Full Resource Inspection")
    print("=" * 60)

    # Chunks
    chunk_info = inspect_chunks(mneme.chunks)
    print("\n" + format_chunk_inspection(chunk_info))

    # Embeddings
    embed_info = inspect_embeddings(mneme.embeddings)
    print("\n📐 Embeddings")
    print("=" * 40)
    print(f"  Shape: {embed_info['shape']}")
    print(f"  Dimension: {embed_info['dimension']}")
    print(f"  Norm (mean): {embed_info['norm_stats']['mean']:.3f}")
    print(f"  Similarity (mean): {embed_info['similarity_stats']['mean']:.3f}")

    # Graph
    graph_info = inspect_graph(mneme.graph)
    print("\n" + format_graph_inspection(graph_info))

    # Communities
    if mneme.knowledge_structures:
        comm_info = inspect_communities(mneme.knowledge_structures)
        print("\n" + format_community_inspection(comm_info))

        # Hubs
        hub_info = inspect_hubs(mneme.knowledge_structures)
        print("\n" + format_hub_inspection(hub_info))

        # Bridges
        bridge_info = inspect_bridges(mneme.knowledge_structures)
        print("\n" + format_bridge_inspection(bridge_info))
    else:
        print("\n⚠️  No knowledge structures available")

    print("\n" + "=" * 60)


def display_graph_info(mneme):
    """
    Display knowledge graph statistics.

    Shows node/edge counts, density, degree statistics,
    edge type distribution, and connectivity info.

    Args:
        mneme: The MNEME instance containing the graph.
    """
    graph_info = inspect_graph(mneme.graph)
    print("\n" + format_graph_inspection(graph_info))


def display_hubs(mneme):
    """
    Display hub nodes in the knowledge graph.

    Hubs are highly connected nodes that serve as central
    points in the knowledge graph topology.

    Args:
        mneme: The MNEME instance containing knowledge structures.
    """
    if not mneme.knowledge_structures:
        print("⚠️  No knowledge structures built.")
        return

    hub_info = inspect_hubs(mneme.knowledge_structures)
    print("\n" + format_hub_inspection(hub_info))


def display_bridges(mneme):
    """
    Display bridge nodes connecting communities.

    Bridges are nodes that connect different communities,
    enabling cross-topic retrieval and knowledge linking.

    Args:
        mneme: The MNEME instance containing knowledge structures.
    """
    if not mneme.knowledge_structures:
        print("⚠️  No knowledge structures built.")
        return

    bridge_info = inspect_bridges(mneme.knowledge_structures)
    print("\n" + format_bridge_inspection(bridge_info))


def display_communities(mneme):
    """
    Display community structure breakdown.

    Communities are clusters of semantically related chunks
    detected through graph community detection algorithms.

    Args:
        mneme: The MNEME instance containing knowledge structures.
    """
    if not mneme.knowledge_structures:
        print("⚠️  No knowledge structures built.")
        return

    comm_info = inspect_communities(mneme.knowledge_structures)
    print("\n" + format_community_inspection(comm_info))


def display_visualization(mneme, output_file: str = "knowledge_graph.html"):
    """
    Generate and open interactive knowledge graph visualization.

    Creates an HTML file with interactive PyVis visualization showing:
    - Nodes colored by community
    - Hub nodes as stars
    - Bridge nodes as diamonds
    - Interactive controls and dark mode

    Args:
        mneme: The MNEME instance with graph and structures.
        output_file: Path for the output HTML file.

    Returns:
        The output file path if successful.
    """
    import webbrowser

    print("\n🎨 Generating knowledge graph visualization...")

    try:
        stats = visualize_mneme_graph(
            graph=mneme.graph,
            structures=mneme.knowledge_structures,
            output_file=output_file,
            title="MNEME Knowledge Graph",
        )

        print(f"\n📊 Visualization Statistics:")
        print(f"   Nodes: {stats['nodes']}")
        print(f"   Edges: {stats['edges']}")
        print(f"   Communities: {stats['communities']}")
        print(f"   Hubs: {stats['hubs']}")
        print(f"   Bridges: {stats['bridges']}")
        print(f"\n🌐 Opening {output_file} in browser...")

        # Open in default browser
        webbrowser.open(f"file://{Path(output_file).absolute()}")
        return output_file

    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Install pyvis with: pip install pyvis")
        return None
    except Exception as e:
        print(f"❌ Error generating visualization: {e}")
        return None


def display_answer(answer, show_trace: bool = False, plan=None, retrieval_result=None):
    """
    Display an answer with optional full trace.

    When trace is enabled, shows query analysis, retrieval scoring,
    thinking trace, and citation details with year-match indicators.

    Args:
        answer: EnhancedAnswer from MNEME query.
        show_trace: Whether to show full retrieval trace.
        plan: QueryPlan (required if show_trace=True).
        retrieval_result: RetrievalResult (required if show_trace=True).
    """
    print("\n" + "=" * 60)

    if show_trace and plan and retrieval_result:
        # Show full trace
        print(format_query_plan(plan))
        print()
        print(format_retrieval_trace(retrieval_result))
        print()
        print(format_thinking_trace(
            coverage_gaps=answer.coverage_gaps,
            missing_years=retrieval_result.missing_years,
            retrieval_result=retrieval_result
        ))
        print()

    # Confidence indicator
    confidence_emoji = {
        "year_matched": "📈",
        "good_match": "👍",
        "partial_match": "⚠️",
        "low_match": "👎",
        "no_results": "❌",
    }
    conf_icon = confidence_emoji.get(answer.confidence, "📊")

    print(f"{conf_icon} Confidence: {answer.confidence}")
    print()
    print("💬 ANSWER:")
    print("-" * 60)
    print(answer.answer)
    print("-" * 60)

    # Citations
    print()
    print(format_citations(answer.citations, answer.year_filter))

    # Coverage gaps
    if answer.coverage_gaps:
        print()
        print("⚠️  Coverage Gaps:")
        for gap in answer.coverage_gaps:
            print(f"   - {gap}")

    # Stats
    print()
    print(f"📊 Stats: {answer.latency_ms:.0f}ms | {answer.num_sources_used} sources | {len(answer.citations)} citations")
    print("=" * 60)


def query_with_trace(mneme, question: str):
    """
    Execute query and capture all intermediate results for tracing.

    Manually steps through MNEME layers to capture:
    - Query plan from analyzer
    - Retrieval result with scores
    - Gap detection results
    - Final answer with citations

    Args:
        mneme: The MNEME instance.
        question: User's question string.

    Returns:
        Tuple of (answer, plan, retrieval_result) for trace display.
    """
    import time

    start_time = time.time()

    # Layer 4: Analyze query
    plan = mneme.query_analyzer.analyze(question)

    # Layer 5: Retrieve relevant chunks
    retrieval_result = mneme.retrieval_engine.retrieve(question, plan)

    # Layer 6: Detect gaps
    gaps = mneme.gap_detector.detect_gaps(retrieval_result, plan)
    retrieval_result.coverage_gaps = gaps
    retrieval_result.missing_years = mneme.gap_detector.get_missing_years(
        retrieval_result, plan
    )

    context = mneme.context_builder.build_context(retrieval_result, plan)

    # Layer 7: Generate answer
    answer_text, stats = mneme.answer_generator.generate(
        question, plan, retrieval_result, context
    )

    # Create citations
    citations = mneme.citation_generator.create_citations(
        retrieval_result.candidates,
        plan.year_filter,
    )

    total_latency = (time.time() - start_time) * 1000

    # Build enhanced answer
    answer = mneme.answer_generator.create_enhanced_answer(
        answer_text=answer_text,
        question=question,
        plan=plan,
        retrieval_result=retrieval_result,
        stats=stats,
        citations=citations,
        total_latency_ms=total_latency,
    )

    return answer, plan, retrieval_result


def interactive_mode(mneme, initial_trace: bool = False):
    """
    Run interactive query loop with command support.

    Available Commands:
        stats       - Show system statistics
        inspect     - Full resource inspection
        graph       - Show knowledge graph info
        hubs        - List hub nodes
        bridges     - List bridge nodes
        communities - Show community breakdown
        visualize   - Generate interactive KG visualization
        trace on    - Enable trace mode
        trace off   - Disable trace mode
        help        - Show this help
        quit/exit/q - Exit the program

    Args:
        mneme: The MNEME instance to query.
        initial_trace: Initial trace mode setting.
    """
    trace_mode = initial_trace

    print("\n🎯 MNEME Interactive Mode")
    print("Type your question and press Enter.")
    print("Commands: stats, inspect, graph, hubs, bridges, communities, visualize, trace on/off, help, quit")
    print(f"Trace mode: {'ON' if trace_mode else 'OFF'}")
    print("-" * 40)

    while True:
        try:
            prompt = "Query (trace)> " if trace_mode else "Query> "
            query = input(f"\n{prompt}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not query:
            continue

        query_lower = query.lower()

        # Handle commands
        if query_lower in ('quit', 'exit', 'q'):
            print("👋 Goodbye!")
            break

        if query_lower == 'stats':
            display_stats(mneme)
            continue

        if query_lower == 'inspect':
            display_full_inspection(mneme)
            continue

        if query_lower == 'graph':
            display_graph_info(mneme)
            continue

        if query_lower == 'hubs':
            display_hubs(mneme)
            continue

        if query_lower == 'bridges':
            display_bridges(mneme)
            continue

        if query_lower == 'communities':
            display_communities(mneme)
            continue

        if query_lower in ('visualize', 'viz'):
            display_visualization(mneme)
            continue

        if query_lower == 'trace on':
            trace_mode = True
            print("✅ Trace mode enabled")
            continue

        if query_lower == 'trace off':
            trace_mode = False
            print("✅ Trace mode disabled")
            continue

        if query_lower == 'help':
            print("\n📖 Commands:")
            print("  stats       - Show system statistics")
            print("  inspect     - Full resource inspection")
            print("  graph       - Show knowledge graph info")
            print("  hubs        - List hub nodes")
            print("  bridges     - List bridge nodes")
            print("  communities - Show community breakdown")
            print("  visualize   - Generate interactive KG visualization")
            print("  trace on    - Enable trace mode")
            print("  trace off   - Disable trace mode")
            print("  help        - Show this help")
            print("  quit        - Exit the program")
            print("\n💡 Example queries:")
            print("  What happened in AI in 2020?")
            print("  Summarize the philosophy documents")
            print("  What are the key ideas about learning?")
            print("  Give me an overview of my knowledge base")
            continue

        # Execute query
        print("\n⏳ Processing query...")
        try:
            if trace_mode:
                answer, plan, retrieval_result = query_with_trace(mneme, query)
                display_answer(answer, show_trace=True, plan=plan, retrieval_result=retrieval_result)
            else:
                answer = mneme.query(query)
                display_answer(answer, show_trace=False)
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()


def main():
    """
    Main entry point for MNEME demo.

    Handles command-line argument parsing and routes to appropriate mode:
    - --stats: Show statistics and exit
    - --inspect: Show full inspection and exit
    - --query: Execute single query
    - Default: Interactive mode
    """
    args = parse_args()

    # Check document path exists
    doc_path = Path(args.docs)
    if not doc_path.exists():
        print(f"❌ Error: Document path not found: {doc_path}")
        print("Please provide a valid path with --docs")
        sys.exit(1)

    # Build MNEME
    try:
        mneme = build_mneme(str(doc_path), verbose=args.verbose)
    except Exception as e:
        print(f"\n❌ Error building MNEME: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Display initial stats
    display_stats(mneme)
    print("\n✅ MNEME ready!")

    # Visualization mode
    if args.visualize:
        display_visualization(mneme)
        return

    # Full inspection mode
    if args.inspect:
        display_full_inspection(mneme)
        return

    # Stats-only mode
    if args.stats:
        return

    # Single query mode
    if args.query:
        print(f"\n🔎 Query: {args.query}")
        try:
            if args.trace:
                answer, plan, retrieval_result = query_with_trace(mneme, args.query)
                display_answer(answer, show_trace=True, plan=plan, retrieval_result=retrieval_result)
            else:
                answer = mneme.query(args.query)
                display_answer(answer, show_trace=False)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
        return

    # Interactive mode
    interactive_mode(mneme, initial_trace=args.trace)


if __name__ == "__main__":
    main()
