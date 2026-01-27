"""
Serialization Utilities

JSON and pickle serialization for MNEME artifacts.
"""

import json
import pickle
from pathlib import Path
from typing import Any, List
import logging

import numpy as np

from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


def save_chunks(chunks: List[Chunk], path: str) -> None:
    """Save chunks to JSON file."""
    data = [c.to_dict() for c in chunks]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(chunks)} chunks to {path}")


def load_chunks(path: str) -> List[Chunk]:
    """Load chunks from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    chunks = [Chunk.from_dict(d) for d in data]
    logger.info(f"Loaded {len(chunks)} chunks from {path}")
    return chunks


def save_embeddings(embeddings: np.ndarray, path: str) -> None:
    """Save embeddings to numpy file."""
    np.save(path, embeddings)
    logger.info(f"Saved embeddings {embeddings.shape} to {path}")


def load_embeddings(path: str) -> np.ndarray:
    """Load embeddings from numpy file."""
    embeddings = np.load(path)
    logger.info(f"Loaded embeddings {embeddings.shape} from {path}")
    return embeddings


def save_graph(graph, path: str) -> None:
    """Save graph to pickle file."""
    with open(path, 'wb') as f:
        pickle.dump(graph, f)
    logger.info(f"Saved graph to {path}")


def load_graph(path: str):
    """Load graph from pickle file."""
    with open(path, 'rb') as f:
        graph = pickle.load(f)
    logger.info(f"Loaded graph from {path}")
    return graph


def save_json(data: Any, path: str) -> None:
    """Save data to JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str) -> Any:
    """Load data from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


class ArtifactManager:
    """Manages MNEME artifacts (chunks, embeddings, graph)."""

    def __init__(self, base_dir: str = "artifacts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_all(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
        graph,
        prefix: str = "",
    ) -> None:
        """Save all artifacts."""
        name_prefix = f"{prefix}_" if prefix else ""

        save_chunks(chunks, str(self.base_dir / f"{name_prefix}chunks.json"))
        save_embeddings(embeddings, str(self.base_dir / f"{name_prefix}embeddings.npy"))
        save_graph(graph, str(self.base_dir / f"{name_prefix}graph.pkl"))

    def load_all(self, prefix: str = "") -> tuple:
        """Load all artifacts."""
        name_prefix = f"{prefix}_" if prefix else ""

        chunks = load_chunks(str(self.base_dir / f"{name_prefix}chunks.json"))
        embeddings = load_embeddings(str(self.base_dir / f"{name_prefix}embeddings.npy"))
        graph = load_graph(str(self.base_dir / f"{name_prefix}graph.pkl"))

        return chunks, embeddings, graph

    def exists(self, prefix: str = "") -> bool:
        """Check if artifacts exist."""
        name_prefix = f"{prefix}_" if prefix else ""
        return (
            (self.base_dir / f"{name_prefix}chunks.json").exists() and
            (self.base_dir / f"{name_prefix}embeddings.npy").exists() and
            (self.base_dir / f"{name_prefix}graph.pkl").exists()
        )
