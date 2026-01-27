"""
MNEME Utilities

Logging, timing, serialization, inspection, trace, and visualization utilities.
"""

from .logging import setup_logging, get_logger, LogContext
from .timing import timed, timed_async, Timer
from .serialization import (
    save_chunks,
    load_chunks,
    save_embeddings,
    load_embeddings,
    save_graph,
    load_graph,
    save_json,
    load_json,
    ArtifactManager,
)
from .inspection import (
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
)
from .trace import (
    format_query_plan,
    format_retrieval_trace,
    format_thinking_trace,
    format_citations,
    format_full_trace,
    format_answer_with_trace,
)
from .visualization import visualize_mneme_graph

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "LogContext",
    # Timing
    "timed",
    "timed_async",
    "Timer",
    # Serialization
    "save_chunks",
    "load_chunks",
    "save_embeddings",
    "load_embeddings",
    "save_graph",
    "load_graph",
    "save_json",
    "load_json",
    "ArtifactManager",
    # Inspection
    "inspect_chunks",
    "inspect_embeddings",
    "inspect_graph",
    "inspect_communities",
    "inspect_hubs",
    "inspect_bridges",
    "format_chunk_inspection",
    "format_graph_inspection",
    "format_community_inspection",
    "format_hub_inspection",
    "format_bridge_inspection",
    # Trace
    "format_query_plan",
    "format_retrieval_trace",
    "format_thinking_trace",
    "format_citations",
    "format_full_trace",
    "format_answer_with_trace",
    # Visualization
    "visualize_mneme_graph",
]
