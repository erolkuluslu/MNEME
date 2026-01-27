"""
MNEME Resource Inspection Utilities

Functions to inspect and display information about MNEME's built resources:
chunks, embeddings, knowledge graph, communities, hubs, and bridges.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from collections import Counter
import numpy as np

if TYPE_CHECKING:
    import networkx as nx
    from src.models.chunk import Chunk
    from src.models.graph import KnowledgeStructures, Community, GraphNode


def inspect_chunks(chunks: List["Chunk"]) -> Dict[str, Any]:
    """
    Analyze chunk distribution by year, category, and other metadata.

    Args:
        chunks: List of Chunk objects

    Returns:
        Dictionary with chunk statistics and distribution
    """
    if not chunks:
        return {"error": "No chunks available"}

    years = [c.year for c in chunks]
    categories = [c.category for c in chunks]
    doc_ids = [c.doc_id for c in chunks]
    text_lengths = [len(c.text) for c in chunks]

    return {
        "total_chunks": len(chunks),
        "unique_documents": len(set(doc_ids)),
        "year_distribution": dict(Counter(years)),
        "category_distribution": dict(Counter(categories)),
        "text_stats": {
            "avg_length": int(np.mean(text_lengths)),
            "min_length": min(text_lengths),
            "max_length": max(text_lengths),
            "median_length": int(np.median(text_lengths)),
        },
        "years_available": sorted(set(years)),
        "categories_available": sorted(set(categories)),
    }


def inspect_embeddings(embeddings: np.ndarray) -> Dict[str, Any]:
    """
    Analyze embedding matrix shape and statistics.

    Args:
        embeddings: NumPy array of embeddings

    Returns:
        Dictionary with embedding statistics
    """
    if embeddings is None or embeddings.size == 0:
        return {"error": "No embeddings available"}

    # Compute basic statistics
    norms = np.linalg.norm(embeddings, axis=1)

    # Sample pairwise similarities (avoid full matrix for large datasets)
    n_samples = min(100, len(embeddings))
    sample_indices = np.random.choice(len(embeddings), n_samples, replace=False)
    sample_embeddings = embeddings[sample_indices]
    sample_similarities = np.dot(sample_embeddings, sample_embeddings.T)

    # Get off-diagonal elements for similarity stats
    mask = ~np.eye(n_samples, dtype=bool)
    pairwise_sims = sample_similarities[mask]

    return {
        "shape": embeddings.shape,
        "num_chunks": embeddings.shape[0],
        "dimension": embeddings.shape[1],
        "dtype": str(embeddings.dtype),
        "norm_stats": {
            "mean": float(np.mean(norms)),
            "std": float(np.std(norms)),
            "min": float(np.min(norms)),
            "max": float(np.max(norms)),
        },
        "similarity_stats": {
            "mean": float(np.mean(pairwise_sims)),
            "std": float(np.std(pairwise_sims)),
            "min": float(np.min(pairwise_sims)),
            "max": float(np.max(pairwise_sims)),
        },
    }


def inspect_graph(graph: "nx.DiGraph") -> Dict[str, Any]:
    """
    Analyze knowledge graph structure and connectivity.

    Args:
        graph: NetworkX DiGraph

    Returns:
        Dictionary with graph statistics
    """
    import networkx as nx

    if graph is None or graph.number_of_nodes() == 0:
        return {"error": "No graph available"}

    # Basic stats
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    # Degree statistics
    degrees = dict(graph.degree())
    degree_values = list(degrees.values())

    # Edge type distribution
    edge_types = Counter()
    for _, _, data in graph.edges(data=True):
        edge_type = data.get("edge_type", "unknown")
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

    # Connected components (for undirected view)
    undirected = graph.to_undirected()
    components = list(nx.connected_components(undirected))

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "density": nx.density(graph),
        "degree_stats": {
            "avg": float(np.mean(degree_values)),
            "max": max(degree_values),
            "min": min(degree_values),
            "median": float(np.median(degree_values)),
        },
        "edge_type_distribution": dict(edge_types),
        "num_components": len(components),
        "largest_component_size": max(len(c) for c in components) if components else 0,
        "is_connected": len(components) == 1,
    }


def inspect_communities(structures: "KnowledgeStructures") -> Dict[str, Any]:
    """
    Analyze community structure.

    Args:
        structures: KnowledgeStructures containing communities

    Returns:
        Dictionary with community statistics
    """
    if structures is None or not structures.communities:
        return {"error": "No communities available"}

    communities = structures.communities
    sizes = [c.size for c in communities]

    # Analyze dominant topics
    category_counts = Counter()
    year_counts = Counter()
    for c in communities:
        if c.dominant_category:
            category_counts[c.dominant_category] += 1
        if c.dominant_year:
            year_counts[c.dominant_year] += 1

    return {
        "num_communities": len(communities),
        "size_stats": {
            "avg": float(np.mean(sizes)),
            "min": min(sizes),
            "max": max(sizes),
            "median": float(np.median(sizes)),
        },
        "size_distribution": dict(Counter(sizes)),
        "dominant_categories": dict(category_counts),
        "dominant_years": dict(year_counts),
        "communities": [
            {
                "id": c.community_id,
                "size": c.size,
                "dominant_category": c.dominant_category,
                "dominant_year": c.dominant_year,
                "num_hubs": len(c.hub_ids),
            }
            for c in communities
        ],
    }


def inspect_hubs(structures: "KnowledgeStructures") -> Dict[str, Any]:
    """
    Analyze hub nodes in the graph.

    Args:
        structures: KnowledgeStructures containing hubs

    Returns:
        Dictionary with hub statistics
    """
    if structures is None or not structures.hubs:
        return {"error": "No hubs available"}

    hubs = structures.hubs

    return {
        "num_hubs": len(hubs),
        "hubs": [
            {
                "chunk_id": h.chunk_id,
                "doc_id": h.doc_id,
                "year": h.year,
                "category": h.category,
                "degree": h.degree,
                "betweenness": round(h.betweenness, 4),
                "pagerank": round(h.pagerank, 4),
                "hub_score": round(h.hub_score, 4),
                "community_id": h.community_id,
            }
            for h in hubs[:15]  # Limit to top 15
        ],
    }


def inspect_bridges(structures: "KnowledgeStructures") -> Dict[str, Any]:
    """
    Analyze bridge nodes that connect communities.

    Args:
        structures: KnowledgeStructures containing bridges

    Returns:
        Dictionary with bridge statistics
    """
    if structures is None or not structures.bridges:
        return {"error": "No bridges available"}

    bridges = structures.bridges

    return {
        "num_bridges": len(bridges),
        "bridges": [
            {
                "chunk_id": b.chunk_id,
                "doc_id": b.doc_id,
                "year": b.year,
                "category": b.category,
                "degree": b.degree,
                "betweenness": round(b.betweenness, 4),
                "bridge_score": round(b.bridge_score, 4),
                "connected_communities": list(b.connected_communities),
                "num_connections": len(b.connected_communities),
            }
            for b in bridges[:15]  # Limit to top 15
        ],
    }


def format_chunk_inspection(info: Dict[str, Any]) -> str:
    """Format chunk inspection as displayable text."""
    if "error" in info:
        return f"Error: {info['error']}"

    lines = [
        "📄 Chunk Distribution",
        "=" * 40,
        f"  Total Chunks:     {info['total_chunks']:,}",
        f"  Unique Documents: {info['unique_documents']:,}",
        "",
        "  Text Length Stats:",
        f"    Average:  {info['text_stats']['avg_length']:,} chars",
        f"    Min:      {info['text_stats']['min_length']:,} chars",
        f"    Max:      {info['text_stats']['max_length']:,} chars",
        "",
        "  By Year:",
    ]
    for year, count in sorted(info["year_distribution"].items()):
        lines.append(f"    {year}: {count}")

    lines.append("")
    lines.append("  By Category:")
    for cat, count in sorted(info["category_distribution"].items()):
        lines.append(f"    {cat}: {count}")

    return "\n".join(lines)


def format_graph_inspection(info: Dict[str, Any]) -> str:
    """Format graph inspection as displayable text."""
    if "error" in info:
        return f"Error: {info['error']}"

    lines = [
        "🕸️  Knowledge Graph",
        "=" * 40,
        f"  Nodes:            {info['num_nodes']:,}",
        f"  Edges:            {info['num_edges']:,}",
        f"  Density:          {info['density']:.4f}",
        f"  Avg Degree:       {info['degree_stats']['avg']:.1f}",
        f"  Max Degree:       {info['degree_stats']['max']}",
        f"  Components:       {info['num_components']}",
        f"  Largest Comp:     {info['largest_component_size']}",
        "",
        "  Edge Types:",
    ]
    for et, count in sorted(info["edge_type_distribution"].items(), key=lambda x: -x[1]):
        lines.append(f"    {et}: {count}")

    return "\n".join(lines)


def format_community_inspection(info: Dict[str, Any]) -> str:
    """Format community inspection as displayable text."""
    if "error" in info:
        return f"Error: {info['error']}"

    lines = [
        "🏘️  Communities",
        "=" * 40,
        f"  Total Communities: {info['num_communities']}",
        f"  Size Range:        {info['size_stats']['min']} - {info['size_stats']['max']}",
        f"  Average Size:      {info['size_stats']['avg']:.1f}",
        "",
        "  Community Details:",
    ]
    for c in info["communities"][:10]:
        cat = c["dominant_category"] or "mixed"
        year = c["dominant_year"] or "mixed"
        lines.append(f"    [{c['id']}] {c['size']} chunks | {cat}/{year} | {c['num_hubs']} hubs")

    return "\n".join(lines)


def format_hub_inspection(info: Dict[str, Any]) -> str:
    """Format hub inspection as displayable text."""
    if "error" in info:
        return f"Error: {info['error']}"

    lines = [
        "🎯 Hub Nodes",
        "=" * 40,
        f"  Total Hubs: {info['num_hubs']}",
        "",
    ]
    for h in info["hubs"][:10]:
        lines.append(f"  [{h['chunk_id']}] {h['category']}/{h['year']}")
        lines.append(f"    Degree: {h['degree']} | Betweenness: {h['betweenness']:.3f} | PageRank: {h['pagerank']:.4f}")

    return "\n".join(lines)


def format_bridge_inspection(info: Dict[str, Any]) -> str:
    """Format bridge inspection as displayable text."""
    if "error" in info:
        return f"Error: {info['error']}"

    lines = [
        "🌉 Bridge Nodes",
        "=" * 40,
        f"  Total Bridges: {info['num_bridges']}",
        "",
    ]
    for b in info["bridges"][:10]:
        comms = ", ".join(str(c) for c in b["connected_communities"])
        lines.append(f"  [{b['chunk_id']}] {b['category']}/{b['year']}")
        lines.append(f"    Connects communities: [{comms}] | Degree: {b['degree']}")

    return "\n".join(lines)
