"""
Knowledge Graph Data Models

Models for graph structure, edges, communities, and graph-based retrieval.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set, Tuple


class EdgeType(str, Enum):
    """Types of edges in the knowledge graph.

    Based on semantic heuristic classification from the paper:
    - elaborates: Same document, later chunk (j > i)
    - contradicts: Keywords like "however", "but", "although"
    - causes: Keywords like "because", "therefore", "led to"
    - supports: Keywords like "confirms", "agrees", "evidence"
    - temporal_sequence: Earlier year + temporal markers
    - same_topic: Same category, high similarity (default)
    - cross_domain: Different categories with similarity >= threshold
    """

    # Semantic relationship types (paper-specified heuristic types)
    ELABORATES = "elaborates"  # Same doc, later chunk index
    CONTRADICTS = "contradicts"  # Contradiction keywords detected
    CAUSES = "causes"  # Causal keywords detected
    SUPPORTS = "supports"  # Support/evidence keywords detected
    TEMPORAL_SEQUENCE = "temporal_sequence"  # Temporal progression
    SAME_TOPIC = "same_topic"  # Same category, high similarity (default)
    CROSS_DOMAIN = "cross_domain"  # Different categories

    # Structural relationships
    SEQUENTIAL = "sequential"  # Same document, adjacent chunks

    # Legacy types (kept for backward compatibility)
    SIMILAR = "similar"  # High semantic similarity
    RELATED = "related"  # Moderate semantic similarity
    HIERARCHICAL = "hierarchical"  # Parent-child in hierarchy
    SAME_ENTITY = "same_entity"  # References same entity
    TEMPORAL = "temporal"  # Time-based connection
    EVOLUTION = "evolution"  # Concept evolution over time


class NodeRole(str, Enum):
    """Role classification for nodes in the graph."""

    HUB = "hub"  # High connectivity, central node
    BRIDGE = "bridge"  # Connects communities
    AUTHORITY = "authority"  # Frequently referenced
    PERIPHERAL = "peripheral"  # Low connectivity
    STANDARD = "standard"  # Normal node


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""

    source_id: str
    target_id: str
    edge_type: EdgeType

    # Edge weight (0-1)
    weight: float = 0.0

    # Similarity score that created this edge
    similarity: float = 0.0

    # Metadata
    created_by: str = "similarity"  # How edge was discovered
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_tuple(self) -> Tuple[str, str]:
        """Get edge as tuple for NetworkX."""
        return (self.source_id, self.target_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "similarity": self.similarity,
            "created_by": self.created_by,
            "metadata": self.metadata,
        }


@dataclass
class GraphNode:
    """A node in the knowledge graph with computed properties."""

    chunk_id: str

    # Basic properties
    doc_id: str
    year: int
    category: str

    # Computed properties
    degree: int = 0
    in_degree: int = 0
    out_degree: int = 0

    # Centrality measures
    betweenness: float = 0.0
    pagerank: float = 0.0
    closeness: float = 0.0

    # Role classification
    role: NodeRole = NodeRole.STANDARD

    # Community assignment
    community_id: Optional[int] = None

    # Hub/bridge scores
    hub_score: float = 0.0
    bridge_score: float = 0.0

    # Connected communities (for bridges)
    connected_communities: Set[int] = field(default_factory=set)

    def is_hub(self, threshold: float = 0.8) -> bool:
        """Check if node is a hub."""
        return self.hub_score >= threshold

    def is_bridge(self, min_communities: int = 2) -> bool:
        """Check if node is a bridge."""
        return len(self.connected_communities) >= min_communities

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "year": self.year,
            "category": self.category,
            "degree": self.degree,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "betweenness": self.betweenness,
            "pagerank": self.pagerank,
            "closeness": self.closeness,
            "role": self.role.value,
            "community_id": self.community_id,
            "hub_score": self.hub_score,
            "bridge_score": self.bridge_score,
            "connected_communities": list(self.connected_communities),
        }


@dataclass
class Community:
    """A community (cluster) in the knowledge graph."""

    community_id: int
    member_ids: List[str] = field(default_factory=list)

    # Community properties
    size: int = 0
    density: float = 0.0  # Edge density within community
    modularity_contribution: float = 0.0

    # Summary (RAPTOR-style)
    summary: Optional[str] = None
    summary_embedding: Optional[List[float]] = None
    summary_hash: Optional[str] = None  # For invalidation when content changes

    # Dominant properties
    dominant_year: Optional[int] = None
    dominant_category: Optional[str] = None
    year_distribution: Dict[int, int] = field(default_factory=dict)
    category_distribution: Dict[str, int] = field(default_factory=dict)

    # Key nodes
    hub_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate size from members."""
        if self.size == 0:
            self.size = len(self.member_ids)

    @property
    def is_large(self) -> bool:
        """Check if community is large (>10 members)."""
        return self.size > 10

    def get_years(self) -> List[int]:
        """Get years represented in community."""
        return sorted(self.year_distribution.keys())

    def get_categories(self) -> List[str]:
        """Get categories represented in community."""
        return sorted(self.category_distribution.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "community_id": self.community_id,
            "member_ids": self.member_ids,
            "size": self.size,
            "density": self.density,
            "modularity_contribution": self.modularity_contribution,
            "summary": self.summary,
            "summary_hash": self.summary_hash,
            "dominant_year": self.dominant_year,
            "dominant_category": self.dominant_category,
            "year_distribution": self.year_distribution,
            "category_distribution": self.category_distribution,
            "hub_ids": self.hub_ids,
        }


@dataclass
class GraphStats:
    """Statistics about the knowledge graph."""

    # Basic stats
    num_nodes: int = 0
    num_edges: int = 0
    density: float = 0.0

    # Connectivity
    num_connected_components: int = 0
    largest_component_size: int = 0
    avg_degree: float = 0.0
    max_degree: int = 0

    # Community stats
    num_communities: int = 0
    modularity: float = 0.0
    avg_community_size: float = 0.0

    # Hub/bridge stats
    num_hubs: int = 0
    num_bridges: int = 0

    # Edge type distribution
    edge_type_counts: Dict[str, int] = field(default_factory=dict)

    # Year/category coverage
    years_covered: List[int] = field(default_factory=list)
    categories_covered: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "density": self.density,
            "num_connected_components": self.num_connected_components,
            "largest_component_size": self.largest_component_size,
            "avg_degree": self.avg_degree,
            "max_degree": self.max_degree,
            "num_communities": self.num_communities,
            "modularity": self.modularity,
            "avg_community_size": self.avg_community_size,
            "num_hubs": self.num_hubs,
            "num_bridges": self.num_bridges,
            "edge_type_counts": self.edge_type_counts,
            "years_covered": self.years_covered,
            "categories_covered": self.categories_covered,
        }


@dataclass
class KnowledgeStructures:
    """
    Container for all knowledge structures derived from the graph.

    Combines communities, hubs, bridges, and summaries.
    """

    communities: List[Community] = field(default_factory=list)
    hubs: List[GraphNode] = field(default_factory=list)
    bridges: List[GraphNode] = field(default_factory=list)
    graph_stats: Optional[GraphStats] = None

    # Mapping from chunk_id to community_id
    chunk_to_community: Dict[str, int] = field(default_factory=dict)

    # Hierarchical summaries (RAPTOR-style)
    hierarchical_summaries: Dict[int, str] = field(default_factory=dict)

    @property
    def num_communities(self) -> int:
        """Number of communities."""
        return len(self.communities)

    @property
    def num_hubs(self) -> int:
        """Number of hub nodes."""
        return len(self.hubs)

    @property
    def num_bridges(self) -> int:
        """Number of bridge nodes."""
        return len(self.bridges)

    def get_community(self, community_id: int) -> Optional[Community]:
        """Get community by ID."""
        for community in self.communities:
            if community.community_id == community_id:
                return community
        return None

    def get_chunk_community(self, chunk_id: str) -> Optional[Community]:
        """Get the community containing a chunk."""
        community_id = self.chunk_to_community.get(chunk_id)
        if community_id is not None:
            return self.get_community(community_id)
        return None

    def get_hub_ids(self) -> List[str]:
        """Get list of hub chunk IDs."""
        return [h.chunk_id for h in self.hubs]

    def get_bridge_ids(self) -> List[str]:
        """Get list of bridge chunk IDs."""
        return [b.chunk_id for b in self.bridges]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "communities": [c.to_dict() for c in self.communities],
            "hubs": [h.to_dict() for h in self.hubs],
            "bridges": [b.to_dict() for b in self.bridges],
            "graph_stats": self.graph_stats.to_dict() if self.graph_stats else None,
            "chunk_to_community": self.chunk_to_community,
            "hierarchical_summaries": self.hierarchical_summaries,
        }
