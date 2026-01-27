"""
Layer 2: Knowledge Graph

Handles embedding generation, similarity search, edge discovery, and graph construction.
"""

from .embeddings import (
    BaseEmbeddingEngine,
    SentenceTransformerEngine,
    create_sentence_transformer_engine,
    OpenAIEmbeddingEngine,
    create_openai_embedding_engine,
)

from .similarity import (
    BaseSimilarityEngine,
    NumpySimilarityEngine,
    create_numpy_engine,
    FaissSimilarityEngine,
    create_faiss_engine,
)

from .edge_discovery import EdgeDiscovery, EdgeTyper, create_edge_discovery
from .graph_builder import KnowledgeGraphBuilder, create_knowledge_graph

__all__ = [
    # Embeddings
    "BaseEmbeddingEngine",
    "SentenceTransformerEngine",
    "create_sentence_transformer_engine",
    "OpenAIEmbeddingEngine",
    "create_openai_embedding_engine",
    # Similarity
    "BaseSimilarityEngine",
    "NumpySimilarityEngine",
    "create_numpy_engine",
    "FaissSimilarityEngine",
    "create_faiss_engine",
    # Edge Discovery
    "EdgeDiscovery",
    "EdgeTyper",
    "create_edge_discovery",
    # Graph Builder
    "KnowledgeGraphBuilder",
    "create_knowledge_graph",
]
