"""
Community Detection Module

Implements Louvain community detection for knowledge graph clustering.
Includes adaptive resolution tuning to achieve target community counts.
"""

from typing import List, Dict, Optional, Tuple
import logging

try:
    import networkx as nx
    from networkx.algorithms import community as nx_community
except ImportError:
    nx = None
    nx_community = None

from src.models.graph import Community, GraphNode

logger = logging.getLogger(__name__)


class CommunityDetector:
    """
    Detects communities in the knowledge graph using Louvain algorithm.

    Communities represent clusters of semantically related chunks.
    """

    def __init__(
        self,
        resolution: float = 0.20,
        min_community_size: int = 3,
        seed: Optional[int] = 42,
    ):
        """
        Initialize community detector.

        Args:
            resolution: Louvain resolution parameter (higher = more communities)
            min_community_size: Minimum nodes for valid community
            seed: Random seed for reproducibility
        """
        if nx is None:
            raise ImportError("networkx is required")

        self.resolution = resolution
        self.min_community_size = min_community_size
        self.seed = seed

    def detect_communities(
        self,
        graph: "nx.DiGraph",
    ) -> List[Community]:
        """
        Detect communities in the graph.

        Args:
            graph: NetworkX knowledge graph

        Returns:
            List of Community objects
        """
        if graph.number_of_nodes() == 0:
            return []

        logger.info(
            f"Detecting communities with resolution={self.resolution}..."
        )

        # Convert to undirected for community detection
        undirected = graph.to_undirected()

        # Run Louvain
        try:
            partition = nx_community.louvain_communities(
                undirected,
                resolution=self.resolution,
                seed=self.seed,
            )
        except Exception as e:
            logger.warning(f"Louvain failed: {e}, using connected components")
            partition = list(nx.connected_components(undirected))

        # Build Community objects
        communities = []
        for community_id, member_set in enumerate(partition):
            members = list(member_set)

            # Skip small communities
            if len(members) < self.min_community_size:
                continue

            # Compute community properties
            community = self._build_community(
                community_id=community_id,
                member_ids=members,
                graph=graph,
            )
            communities.append(community)

        # Sort by size descending
        communities.sort(key=lambda c: c.size, reverse=True)

        logger.info(f"Detected {len(communities)} communities")
        return communities

    def _build_community(
        self,
        community_id: int,
        member_ids: List[str],
        graph: "nx.DiGraph",
    ) -> Community:
        """Build a Community object with computed properties."""
        community = Community(
            community_id=community_id,
            member_ids=member_ids,
            size=len(member_ids),
        )

        # Compute distributions
        year_dist: Dict[int, int] = {}
        category_dist: Dict[str, int] = {}

        for node_id in member_ids:
            if node_id in graph.nodes:
                node_data = graph.nodes[node_id]

                year = node_data.get("year")
                if year:
                    year_dist[year] = year_dist.get(year, 0) + 1

                category = node_data.get("category")
                if category:
                    category_dist[category] = category_dist.get(category, 0) + 1

        community.year_distribution = year_dist
        community.category_distribution = category_dist

        # Dominant properties
        if year_dist:
            community.dominant_year = max(year_dist, key=year_dist.get)
        if category_dist:
            community.dominant_category = max(category_dist, key=category_dist.get)

        # Compute density
        subgraph = graph.subgraph(member_ids)
        n = len(member_ids)
        if n > 1:
            max_edges = n * (n - 1)  # Directed graph
            community.density = subgraph.number_of_edges() / max_edges

        return community

    def get_node_community_map(
        self,
        communities: List[Community],
    ) -> Dict[str, int]:
        """
        Create mapping from node ID to community ID.

        Args:
            communities: List of communities

        Returns:
            Dict mapping node_id -> community_id
        """
        node_to_community = {}
        for community in communities:
            for node_id in community.member_ids:
                node_to_community[node_id] = community.community_id
        return node_to_community


class AdaptiveCommunityDetector(CommunityDetector):
    """
    Auto-tunes Louvain resolution to achieve target community count.

    Addresses the problem where low resolution (e.g., 0.20) creates too few
    communities (1-2), which prevents bridge detection from working.
    Bridges require 2+ communities to exist.
    """

    def __init__(
        self,
        target_min_communities: int = 10,
        target_max_communities: int = 20,
        min_resolution: float = 0.1,
        max_resolution: float = 2.0,
        max_iterations: int = 10,
        min_community_size: int = 3,
        seed: Optional[int] = 42,
    ):
        """
        Initialize adaptive community detector.

        Args:
            target_min_communities: Minimum target community count
            target_max_communities: Maximum target community count
            min_resolution: Lower bound for resolution search
            max_resolution: Upper bound for resolution search
            max_iterations: Maximum binary search iterations
            min_community_size: Minimum nodes for valid community
            seed: Random seed for reproducibility
        """
        # Initialize with mid-range resolution
        super().__init__(
            resolution=(min_resolution + max_resolution) / 2,
            min_community_size=min_community_size,
            seed=seed,
        )
        self.target_min_communities = target_min_communities
        self.target_max_communities = target_max_communities
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        self.max_iterations = max_iterations
        self._final_resolution = None

    def detect_communities_adaptive(
        self,
        graph: "nx.DiGraph",
    ) -> Tuple[List[Community], float]:
        """
        Detect communities with adaptive resolution tuning.

        Uses binary search to find a resolution that produces
        a community count within the target range.

        Args:
            graph: NetworkX knowledge graph

        Returns:
            Tuple of (communities, final_resolution)
        """
        if graph.number_of_nodes() == 0:
            return [], 0.0

        # Handle small graphs - may not produce many communities
        if graph.number_of_nodes() < 10:
            communities = self.detect_communities(graph)
            return communities, self.resolution

        logger.info(
            f"Starting adaptive community detection "
            f"(target: {self.target_min_communities}-{self.target_max_communities} communities)"
        )

        low = self.min_resolution
        high = self.max_resolution
        best_communities = None
        best_resolution = self.resolution
        best_count = 0

        for iteration in range(self.max_iterations):
            mid = (low + high) / 2
            self.resolution = mid

            communities = self.detect_communities(graph)
            count = len(communities)

            logger.debug(
                f"Iteration {iteration + 1}: resolution={mid:.3f}, communities={count}"
            )

            # Check if within target range
            if self.target_min_communities <= count <= self.target_max_communities:
                logger.info(
                    f"Found optimal resolution={mid:.3f} with {count} communities"
                )
                self._final_resolution = mid
                return communities, mid

            # Track best result so far
            if best_communities is None or abs(count - self.target_min_communities) < abs(best_count - self.target_min_communities):
                best_communities = communities
                best_resolution = mid
                best_count = count

            # Adjust search bounds
            # Higher resolution = more communities
            if count < self.target_min_communities:
                low = mid  # Need more communities, increase resolution
            else:
                high = mid  # Too many communities, decrease resolution

            # Check convergence
            if high - low < 0.01:
                logger.debug(f"Resolution search converged at {mid:.3f}")
                break

        # Return best result found
        logger.info(
            f"Adaptive search complete: resolution={best_resolution:.3f}, "
            f"communities={best_count} (target: {self.target_min_communities}-{self.target_max_communities})"
        )
        self._final_resolution = best_resolution
        return best_communities if best_communities else [], best_resolution

    @property
    def final_resolution(self) -> Optional[float]:
        """Get the final resolution used after adaptive detection."""
        return self._final_resolution


def detect_communities(
    graph: "nx.DiGraph",
    resolution: float = 0.20,
    min_size: int = 3,
) -> List[Community]:
    """
    Convenience function to detect communities.

    Args:
        graph: Knowledge graph
        resolution: Louvain resolution
        min_size: Minimum community size

    Returns:
        List of Community objects
    """
    detector = CommunityDetector(
        resolution=resolution,
        min_community_size=min_size,
    )
    return detector.detect_communities(graph)


def detect_communities_adaptive(
    graph: "nx.DiGraph",
    target_min: int = 10,
    target_max: int = 20,
    min_size: int = 3,
) -> Tuple[List[Community], float]:
    """
    Convenience function for adaptive community detection.

    Args:
        graph: Knowledge graph
        target_min: Minimum target community count
        target_max: Maximum target community count
        min_size: Minimum community size

    Returns:
        Tuple of (communities, final_resolution)
    """
    detector = AdaptiveCommunityDetector(
        target_min_communities=target_min,
        target_max_communities=target_max,
        min_community_size=min_size,
    )
    return detector.detect_communities_adaptive(graph)
