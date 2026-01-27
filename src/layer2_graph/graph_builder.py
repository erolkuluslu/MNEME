"""
Knowledge Graph Builder

Constructs NetworkX graph from chunks and edges.
"""

from typing import List, Dict, Any, Optional
import logging

try:
    import networkx as nx
except ImportError:
    nx = None

from src.models.chunk import Chunk
from src.models.graph import GraphEdge, GraphStats, EdgeType

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """
    Builds a NetworkX knowledge graph from chunks and edges.

    The graph structure:
    - Nodes: Chunks with metadata (doc_id, year, category, etc.)
    - Edges: Connections with type, weight, and similarity
    """

    def __init__(self):
        """Initialize graph builder."""
        if nx is None:
            raise ImportError(
                "networkx is required. Install with: pip install networkx"
            )

    def build(
        self,
        chunks: List[Chunk],
        edges: List[GraphEdge],
    ) -> "nx.DiGraph":
        """
        Build knowledge graph from chunks and edges.

        Args:
            chunks: List of Chunk objects
            edges: List of GraphEdge objects

        Returns:
            NetworkX DiGraph
        """
        logger.info(f"Building graph with {len(chunks)} nodes and {len(edges)} edges...")

        graph = nx.DiGraph()

        # Add nodes
        for chunk in chunks:
            graph.add_node(
                chunk.chunk_id,
                doc_id=chunk.doc_id,
                year=chunk.year,
                category=chunk.category,
                chunk_index=chunk.chunk_index,
                word_count=chunk.word_count,
                level=chunk.level,
                title=chunk.title,
            )

        # Add edges
        for edge in edges:
            graph.add_edge(
                edge.source_id,
                edge.target_id,
                edge_type=edge.edge_type.value,
                weight=edge.weight,
                similarity=edge.similarity,
                created_by=edge.created_by,
            )

        logger.info(
            f"Built graph: {graph.number_of_nodes()} nodes, "
            f"{graph.number_of_edges()} edges"
        )

        return graph

    def get_stats(self, graph: "nx.DiGraph") -> GraphStats:
        """
        Compute statistics about the graph.

        Args:
            graph: NetworkX graph

        Returns:
            GraphStats object
        """
        stats = GraphStats()

        # Basic stats
        stats.num_nodes = graph.number_of_nodes()
        stats.num_edges = graph.number_of_edges()

        if stats.num_nodes == 0:
            return stats

        # Density
        stats.density = nx.density(graph)

        # Connectivity (use underlying undirected for components)
        undirected = graph.to_undirected()
        components = list(nx.connected_components(undirected))
        stats.num_connected_components = len(components)
        stats.largest_component_size = max(len(c) for c in components) if components else 0

        # Degree statistics
        degrees = [d for _, d in graph.degree()]
        if degrees:
            stats.avg_degree = sum(degrees) / len(degrees)
            stats.max_degree = max(degrees)

        # Edge type counts
        edge_types: Dict[str, int] = {}
        for _, _, data in graph.edges(data=True):
            edge_type = data.get("edge_type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        stats.edge_type_counts = edge_types

        # Year/category coverage
        years = set()
        categories = set()
        for _, data in graph.nodes(data=True):
            if "year" in data:
                years.add(data["year"])
            if "category" in data:
                categories.add(data["category"])

        stats.years_covered = sorted(years)
        stats.categories_covered = sorted(categories)

        return stats

    def get_subgraph(
        self,
        graph: "nx.DiGraph",
        node_ids: List[str],
        include_neighbors: bool = False,
        neighbor_depth: int = 1,
    ) -> "nx.DiGraph":
        """
        Extract subgraph containing specified nodes.

        Args:
            graph: Full graph
            node_ids: Node IDs to include
            include_neighbors: Whether to include neighbors
            neighbor_depth: Depth of neighbor expansion

        Returns:
            Subgraph
        """
        nodes_to_include = set(node_ids)

        if include_neighbors:
            for _ in range(neighbor_depth):
                new_nodes = set()
                for node in nodes_to_include:
                    if node in graph:
                        # Add predecessors and successors
                        new_nodes.update(graph.predecessors(node))
                        new_nodes.update(graph.successors(node))
                nodes_to_include.update(new_nodes)

        # Filter to nodes that exist in graph
        nodes_to_include = {n for n in nodes_to_include if n in graph}

        return graph.subgraph(nodes_to_include).copy()

    def get_neighbors(
        self,
        graph: "nx.DiGraph",
        node_id: str,
        max_neighbors: int = 10,
        edge_types: Optional[List[EdgeType]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get neighbors of a node with edge information.

        Args:
            graph: Knowledge graph
            node_id: Node to get neighbors for
            max_neighbors: Maximum neighbors to return
            edge_types: Filter by edge types

        Returns:
            List of neighbor info dicts
        """
        if node_id not in graph:
            return []

        neighbors = []

        # Get outgoing edges (successors)
        for neighbor_id in graph.successors(node_id):
            edge_data = graph[node_id][neighbor_id]

            # Filter by edge type
            if edge_types:
                edge_type = edge_data.get("edge_type")
                if edge_type not in [et.value for et in edge_types]:
                    continue

            node_data = graph.nodes[neighbor_id]
            neighbors.append({
                "node_id": neighbor_id,
                "direction": "outgoing",
                "edge_type": edge_data.get("edge_type"),
                "similarity": edge_data.get("similarity", 0.0),
                "doc_id": node_data.get("doc_id"),
                "year": node_data.get("year"),
                "category": node_data.get("category"),
            })

        # Get incoming edges (predecessors)
        for neighbor_id in graph.predecessors(node_id):
            edge_data = graph[neighbor_id][node_id]

            if edge_types:
                edge_type = edge_data.get("edge_type")
                if edge_type not in [et.value for et in edge_types]:
                    continue

            node_data = graph.nodes[neighbor_id]
            neighbors.append({
                "node_id": neighbor_id,
                "direction": "incoming",
                "edge_type": edge_data.get("edge_type"),
                "similarity": edge_data.get("similarity", 0.0),
                "doc_id": node_data.get("doc_id"),
                "year": node_data.get("year"),
                "category": node_data.get("category"),
            })

        # Sort by similarity and limit
        neighbors.sort(key=lambda x: x["similarity"], reverse=True)
        return neighbors[:max_neighbors]

    def export_gexf(self, graph: "nx.DiGraph", path: str) -> None:
        """Export graph to GEXF format for visualization."""
        nx.write_gexf(graph, path)
        logger.info(f"Exported graph to {path}")

    def export_graphml(self, graph: "nx.DiGraph", path: str) -> None:
        """Export graph to GraphML format."""
        nx.write_graphml(graph, path)
        logger.info(f"Exported graph to {path}")


def create_knowledge_graph(
    chunks: List[Chunk],
    edges: List[GraphEdge],
) -> "nx.DiGraph":
    """
    Convenience function to build knowledge graph.

    Args:
        chunks: List of chunks
        edges: List of edges

    Returns:
        NetworkX DiGraph
    """
    builder = KnowledgeGraphBuilder()
    return builder.build(chunks, edges)
