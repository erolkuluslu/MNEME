"""
Hub and Bridge Detection Module

Identifies important nodes in the knowledge graph.
"""

from typing import List, Dict, Set, Optional
import logging

try:
    import networkx as nx
except ImportError:
    nx = None

from src.models.graph import GraphNode, NodeRole, Community

logger = logging.getLogger(__name__)


class HubBridgeDetector:
    """
    Detects hub and bridge nodes in the knowledge graph.

    Hubs: High-connectivity nodes that serve as information centers
    Bridges: Nodes that connect different communities
    """

    def __init__(
        self,
        hub_threshold: float = 0.8,
        bridge_min_communities: int = 3,
        bridge_betweenness_threshold: float = 0.1,
    ):
        """
        Initialize detector.

        Args:
            hub_threshold: Percentile threshold for hub classification
            bridge_min_communities: Min communities to be a bridge (stricter = 3+)
            bridge_betweenness_threshold: Alternative betweenness threshold for bridges
        """
        if nx is None:
            raise ImportError("networkx is required")

        self.hub_threshold = hub_threshold
        self.bridge_min_communities = bridge_min_communities
        self.bridge_betweenness_threshold = bridge_betweenness_threshold

    def detect(
        self,
        graph: "nx.DiGraph",
        communities: List[Community],
    ) -> tuple:
        """
        Detect hubs and bridges in the graph.

        Args:
            graph: Knowledge graph
            communities: Detected communities

        Returns:
            Tuple of (hubs_list, bridges_list)
        """
        if graph.number_of_nodes() == 0:
            return [], []

        logger.info("Detecting hubs and bridges...")

        # Build node-to-community mapping
        node_to_community = self._build_community_map(communities)

        # Compute centrality metrics
        node_metrics = self._compute_metrics(graph, node_to_community)

        # Identify hubs
        hubs = self._identify_hubs(node_metrics)

        # Identify bridges
        bridges = self._identify_bridges(node_metrics)

        logger.info(f"Found {len(hubs)} hubs and {len(bridges)} bridges")
        return hubs, bridges

    def _build_community_map(
        self,
        communities: List[Community],
    ) -> Dict[str, int]:
        """Build mapping from node to community."""
        node_to_community = {}
        for community in communities:
            for node_id in community.member_ids:
                node_to_community[node_id] = community.community_id
        return node_to_community

    def _compute_metrics(
        self,
        graph: "nx.DiGraph",
        node_to_community: Dict[str, int],
    ) -> Dict[str, GraphNode]:
        """Compute centrality metrics for all nodes."""
        nodes = {}

        # Degree centrality
        in_degree = dict(graph.in_degree())
        out_degree = dict(graph.out_degree())

        # Betweenness centrality (expensive for large graphs)
        try:
            if graph.number_of_nodes() < 5000:
                betweenness = nx.betweenness_centrality(graph)
            else:
                # Use approximation for large graphs
                betweenness = nx.betweenness_centrality(
                    graph, k=min(500, graph.number_of_nodes())
                )
        except Exception:
            betweenness = {n: 0.0 for n in graph.nodes()}

        # PageRank
        try:
            pagerank = nx.pagerank(graph)
        except Exception:
            pagerank = {n: 0.0 for n in graph.nodes()}

        # Build GraphNode objects
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]

            # Find connected communities
            connected_communities = self._find_connected_communities(
                graph, node_id, node_to_community
            )

            node = GraphNode(
                chunk_id=node_id,
                doc_id=node_data.get("doc_id", ""),
                year=node_data.get("year", 0),
                category=node_data.get("category", ""),
                degree=in_degree.get(node_id, 0) + out_degree.get(node_id, 0),
                in_degree=in_degree.get(node_id, 0),
                out_degree=out_degree.get(node_id, 0),
                betweenness=betweenness.get(node_id, 0.0),
                pagerank=pagerank.get(node_id, 0.0),
                community_id=node_to_community.get(node_id),
                connected_communities=connected_communities,
            )

            nodes[node_id] = node

        # Compute hub and bridge scores
        self._compute_scores(nodes)

        return nodes

    def _find_connected_communities(
        self,
        graph: "nx.DiGraph",
        node_id: str,
        node_to_community: Dict[str, int],
    ) -> Set[int]:
        """Find communities that a node connects to."""
        communities = set()

        # Own community
        if node_id in node_to_community:
            communities.add(node_to_community[node_id])

        # Neighbor communities
        for neighbor in graph.predecessors(node_id):
            if neighbor in node_to_community:
                communities.add(node_to_community[neighbor])

        for neighbor in graph.successors(node_id):
            if neighbor in node_to_community:
                communities.add(node_to_community[neighbor])

        return communities

    def _compute_scores(self, nodes: Dict[str, GraphNode]) -> None:
        """Compute hub and bridge scores for all nodes."""
        if not nodes:
            return

        import numpy as np
        degrees = [n.degree for n in nodes.values()]
        if degrees:
            # User requested logic: Top 10% most connected nodes (90th percentile)
            import numpy as np
            degree_threshold = np.percentile(degrees, 90)
            
            for node in nodes.values():
                # Hub if degree is in top 10%
                if node.degree >= degree_threshold:
                    node.role = NodeRole.HUB
                    node.hub_score = 1.0 # Mark as hub
                else:
                    node.hub_score = node.degree / max(degrees) if max(degrees) > 0 else 0.0

        # Compute bridge scores based on connected communities
        for node in nodes.values():
            num_communities = len(node.connected_communities)
            node.bridge_score = num_communities / 5.0  # Normalize to ~1.0 max

    def _identify_hubs(
        self,
        nodes: Dict[str, GraphNode],
    ) -> List[GraphNode]:
        """Identify hub nodes."""
        hubs = []

        for node in nodes.values():
            # Role is already set in _compute_scores based on percentile
            if node.role == NodeRole.HUB:
                hubs.append(node)

        # Sort by degree (since hub_score is 1.0 for all hubs now)
        hubs.sort(key=lambda n: n.degree, reverse=True)
        return hubs

    def _identify_bridges(
        self,
        nodes: Dict[str, GraphNode],
    ) -> List[GraphNode]:
        """
        Identify bridge nodes using stricter criteria.

        A node is a bridge if:
        1. It connects 3+ communities (stricter than before), OR
        2. It has high betweenness centrality (>0.1) AND connects 2+ communities

        This prevents the over-identification problem where 94/101 nodes
        were marked as bridges with the old 2-community threshold.
        """
        bridges = []

        for node in nodes.values():
            num_communities = len(node.connected_communities)

            # Stricter bridge criteria:
            # Option 1: Connects 3+ communities
            # Option 2: High betweenness AND connects 2+ communities
            is_bridge = (
                num_communities >= self.bridge_min_communities or
                (node.betweenness >= self.bridge_betweenness_threshold and num_communities >= 2)
            )

            if is_bridge:
                # Only mark as bridge if not already a hub
                if node.role != NodeRole.HUB:
                    node.role = NodeRole.BRIDGE
                bridges.append(node)

        # Sort by number of connected communities, then by betweenness
        bridges.sort(
            key=lambda n: (len(n.connected_communities), n.betweenness),
            reverse=True
        )
        return bridges


def detect_hubs_and_bridges(
    graph: "nx.DiGraph",
    communities: List[Community],
    hub_threshold: float = 0.8,
    bridge_min_communities: int = 3,
    bridge_betweenness_threshold: float = 0.1,
) -> tuple:
    """
    Convenience function to detect hubs and bridges.

    Args:
        graph: Knowledge graph
        communities: Detected communities
        hub_threshold: Threshold for hub classification
        bridge_min_communities: Min communities for bridge (default 3 for stricter detection)
        bridge_betweenness_threshold: Alternative betweenness threshold for bridges

    Returns:
        Tuple of (hubs, bridges)
    """
    detector = HubBridgeDetector(
        hub_threshold=hub_threshold,
        bridge_min_communities=bridge_min_communities,
        bridge_betweenness_threshold=bridge_betweenness_threshold,
    )
    return detector.detect(graph, communities)
