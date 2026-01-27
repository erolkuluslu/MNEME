"""
MNEME: 7-Layer RAG Architecture

A production-ready Retrieval-Augmented Generation system with:
- Layer 1: Document Processing (chunking, metadata)
- Layer 2: Knowledge Graph (embeddings, similarity, edges)
- Layer 3: Knowledge Structures (communities, hubs, bridges)
- Layer 4: Query Analysis (classification, expansion, filters)
- Layer 5: Retrieval Engine (hybrid RRF, boosting)
- Layer 6: Thinking Engine (gap detection, context building)
- Layer 7: Answer Generation (prompts, confidence, citations)
"""

from src.config import MNEMEConfig
from src.pipeline import MNEME, MNEMEBuilder, create_mneme_from_documents

__version__ = "1.0.0"

__all__ = [
    "MNEMEConfig",
    "MNEME",
    "MNEMEBuilder",
    "create_mneme_from_documents",
]
