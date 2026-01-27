"""
MNEME Builder

Builder pattern for constructing the MNEME system.
"""

from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

try:
    import networkx as nx
except ImportError:
    nx = None

import numpy as np

from src.config import MNEMEConfig
from src.models.chunk import Chunk
from src.models.graph import KnowledgeStructures

from src.layer1_document import DocumentDiscovery, WordCountChunking
from src.layer2_graph import (
    SentenceTransformerEngine,
    NumpySimilarityEngine,
    FaissSimilarityEngine,
    EdgeDiscovery,
    KnowledgeGraphBuilder,
)
from src.layer3_structures import (
    CommunityDetector,
    AdaptiveCommunityDetector,
    HubBridgeDetector,
    CommunitySummarizer,
)
from src.layer7_generation import GeminiProvider

from .mneme import MNEME

logger = logging.getLogger(__name__)


class MNEMEBuilder:
    """
    Builder for constructing MNEME systems.

    Handles the full pipeline from documents to ready-to-query system.
    """

    def __init__(self, config: Optional[MNEMEConfig] = None):
        """
        Initialize builder.

        Args:
            config: MNEME configuration
        """
        self.config = config or MNEMEConfig()

        # Components
        self._chunks: List[Chunk] = []
        self._embeddings: Optional[np.ndarray] = None
        self._graph = None
        self._knowledge_structures: Optional[KnowledgeStructures] = None

        # Engines
        self._embedding_engine = None
        self._similarity_engine = None
        self._llm_provider = None

    def with_config(self, config: MNEMEConfig) -> "MNEMEBuilder":
        """Set configuration."""
        self.config = config
        return self

    def discover_documents(self, path: str) -> "MNEMEBuilder":
        """
        Discover and process documents from path.

        Args:
            path: Directory path

        Returns:
            self for chaining
        """
        logger.info(f"Discovering documents from {path}")

        discovery = DocumentDiscovery(
            base_path=path,
            year_patterns=self.config.year_detection_patterns
        )
        documents = discovery.discover()

        chunker = WordCountChunking(
            target_size=self.config.target_chunk_size,
            min_size=self.config.min_chunk_size,
            max_size=self.config.max_chunk_size,
            overlap=self.config.chunk_overlap,
        )

        for doc in documents:
            chunks = chunker.chunk(
                text=doc.content,
                doc_id=doc.doc_id,
                category=doc.category,
                year=doc.year,
            )
            self._chunks.extend(chunks)

        # Set embedding indices
        for i, chunk in enumerate(self._chunks):
            chunk.embedding_index = i

        logger.info(f"Created {len(self._chunks)} chunks from {len(documents)} documents")
        return self

    def with_chunks(self, chunks: List[Chunk]) -> "MNEMEBuilder":
        """Set chunks directly."""
        self._chunks = chunks
        for i, chunk in enumerate(self._chunks):
            chunk.embedding_index = i
        return self

    def build_embeddings(self) -> "MNEMEBuilder":
        """Generate embeddings for all chunks."""
        logger.info("Building embeddings...")

        self._embedding_engine = SentenceTransformerEngine(
            model_name=self.config.embedding_model,
        )

        self._embeddings = self._embedding_engine.generate_embeddings(self._chunks)

        logger.info(f"Generated embeddings: {self._embeddings.shape}")
        return self

    def with_embeddings(self, embeddings: np.ndarray) -> "MNEMEBuilder":
        """Set embeddings directly."""
        self._embeddings = embeddings
        return self

    def build_similarity_engine(self) -> "MNEMEBuilder":
        """Build similarity search engine."""
        logger.info("Building similarity engine...")

        if self.config.similarity_engine == "faiss":
            self._similarity_engine = FaissSimilarityEngine(
                dimension=self.config.embedding_dimension,
            )
        else:
            self._similarity_engine = NumpySimilarityEngine(
                dimension=self.config.embedding_dimension,
            )

        self._similarity_engine.build_index(self._embeddings)
        return self

    def build_graph(self) -> "MNEMEBuilder":
        """Build knowledge graph."""
        logger.info("Building knowledge graph...")

        edge_discovery = EdgeDiscovery(
            semantic_threshold=self.config.semantic_similarity_threshold,
            cross_domain_threshold=self.config.cross_domain_threshold,
            max_total_edges=self.config.max_total_edges,
            top_k_neighbors=self.config.top_k_neighbors,
        )

        edges = edge_discovery.discover_edges(
            self._chunks,
            self._embeddings,
            self._similarity_engine,
        )

        graph_builder = KnowledgeGraphBuilder()
        self._graph = graph_builder.build(self._chunks, edges)

        return self

    def with_graph(self, graph) -> "MNEMEBuilder":
        """Set graph directly."""
        self._graph = graph
        return self

    def build_knowledge_structures(self) -> "MNEMEBuilder":
        """Build knowledge structures (communities, hubs, bridges, summaries)."""
        logger.info("Building knowledge structures...")

        # Use adaptive or standard community detection based on config
        if self.config.adaptive_resolution:
            adaptive_detector = AdaptiveCommunityDetector(
                target_min_communities=self.config.target_min_communities,
                target_max_communities=self.config.target_max_communities,
                min_resolution=self.config.louvain_min_resolution,
                max_resolution=self.config.louvain_max_resolution,
                min_community_size=self.config.min_community_size,
            )
            communities, final_resolution = adaptive_detector.detect_communities_adaptive(
                self._graph
            )
            logger.info(f"Adaptive detection found {len(communities)} communities at resolution {final_resolution:.3f}")
            community_detector = adaptive_detector
        else:
            community_detector = CommunityDetector(
                resolution=self.config.louvain_resolution,
                min_community_size=self.config.min_community_size,
            )
            communities = community_detector.detect_communities(self._graph)

        # Detect hubs and bridges
        hub_detector = HubBridgeDetector(
            hub_threshold=self.config.hub_threshold,
            bridge_min_communities=self.config.bridge_min_communities,
        )
        hubs, bridges = hub_detector.detect(self._graph, communities)

        # Generate community summaries if enabled
        if self.config.community_summary_enabled and communities:
            self._generate_community_summaries(communities)

        # Build structures
        self._knowledge_structures = KnowledgeStructures(
            communities=communities,
            hubs=hubs,
            bridges=bridges,
            chunk_to_community=community_detector.get_node_community_map(communities),
        )

        return self

    def _generate_community_summaries(self, communities) -> None:
        """Generate summaries for communities using LLM."""
        import hashlib

        if not communities:
            return

        logger.info(f"Generating summaries for {len(communities)} communities...")

        # Build LLM provider if not already built
        if self._llm_provider is None:
            self.build_llm_provider()

        summarizer = CommunitySummarizer(
            llm_provider=self._llm_provider,
            max_chunks_per_summary=self.config.summary_max_chunks,
            max_summary_length=self.config.summary_max_length,
        )

        # Build chunk lookup
        chunk_by_id = {c.chunk_id: c for c in self._chunks}

        for community in communities:
            # Compute content hash for invalidation support
            member_texts = []
            for chunk_id in sorted(community.member_ids):
                if chunk_id in chunk_by_id:
                    member_texts.append(chunk_by_id[chunk_id].text[:100])
            content_hash = hashlib.md5("".join(member_texts).encode()).hexdigest()[:16]
            community.summary_hash = content_hash

        # Generate summaries
        summarizer.summarize_communities(communities, self._chunks)

        summary_count = sum(1 for c in communities if c.summary)
        logger.info(f"Generated {summary_count} community summaries")

    def with_llm_provider(self, provider) -> "MNEMEBuilder":
        """Set LLM provider."""
        self._llm_provider = provider
        return self

    def build_llm_provider(self) -> "MNEMEBuilder":
        """Build default LLM provider."""
        if self.config.llm_provider == "gemini":
            self._llm_provider = GeminiProvider(
                model_name=self.config.answer_model,
                api_key=self.config.gemini_api_key,
            )
        return self

    def build(self) -> MNEME:
        """
        Build the complete MNEME system.

        Returns:
            Configured MNEME instance
        """
        # Ensure all components are built
        if self._embeddings is None:
            self.build_embeddings()

        if self._similarity_engine is None:
            self.build_similarity_engine()

        if self._graph is None:
            self.build_graph()

        if self._llm_provider is None:
            self.build_llm_provider()

        return MNEME(
            chunks=self._chunks,
            embeddings=self._embeddings,
            graph=self._graph,
            config=self.config,
            embedding_engine=self._embedding_engine,
            similarity_engine=self._similarity_engine,
            llm_provider=self._llm_provider,
            knowledge_structures=self._knowledge_structures,
        )


def create_mneme_from_documents(
    document_path: str,
    config: Optional[MNEMEConfig] = None,
) -> MNEME:
    """
    Create MNEME system from documents directory.

    Args:
        document_path: Path to documents
        config: Optional configuration

    Returns:
        Ready MNEME instance
    """
    builder = MNEMEBuilder(config)
    return (
        builder
        .discover_documents(document_path)
        .build_embeddings()
        .build_similarity_engine()
        .build_graph()
        .build_knowledge_structures()
        .build_llm_provider()
        .build()
    )
