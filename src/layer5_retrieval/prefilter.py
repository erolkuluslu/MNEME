"""
Year Pre-filter Module

Pre-filters chunks by year before dense retrieval for efficiency.
"""

from typing import List, Tuple, Dict
from collections import defaultdict
import logging
import numpy as np

from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


class YearPrefilter:
    """
    Pre-filters chunks by year before dense retrieval.

    Builds an index mapping years to chunk indices for fast lookup,
    enabling efficient year-based filtering before expensive embedding search.
    """

    def __init__(self, chunks: List[Chunk]):
        """
        Initialize year prefilter.

        Args:
            chunks: List of all chunks in corpus
        """
        self.chunks = chunks
        self._year_to_indices = self._build_year_index()

        logger.debug(
            f"Built year prefilter index for {len(chunks)} chunks, "
            f"{len(self._year_to_indices)} unique years"
        )

    def _build_year_index(self) -> Dict[int, List[int]]:
        """Build index mapping years to chunk indices."""
        index = defaultdict(list)

        for i, chunk in enumerate(self.chunks):
            index[chunk.year].append(i)

        return dict(index)

    def get_candidate_indices(
        self,
        year_filter: int,
        range_size: int = 0,
    ) -> List[int]:
        """
        Get indices of chunks within year filter range.

        Args:
            year_filter: Target year
            range_size: Range to include (0 = exact match, 2 = ±2 years)

        Returns:
            List of chunk indices matching the year filter
        """
        if not self.chunks:
            return []

        # Calculate year range
        min_year = year_filter - range_size
        max_year = year_filter + range_size

        # Collect indices for all years in range
        indices = []
        for year in range(min_year, max_year + 1):
            if year in self._year_to_indices:
                indices.extend(self._year_to_indices[year])

        logger.debug(
            f"Year prefilter: filter={year_filter}, range=±{range_size}, "
            f"found {len(indices)} candidates"
        )

        return indices

    def filter_embeddings(
        self,
        embeddings: np.ndarray,
        year_filter: int,
        range_size: int = 2,
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Filter embeddings to only include year-relevant chunks.

        Args:
            embeddings: Full embedding matrix (N x D)
            year_filter: Target year
            range_size: Range to include (default ±2 years)

        Returns:
            Tuple of (filtered_embeddings, original_indices)
            - filtered_embeddings: Reduced embedding matrix
            - original_indices: Mapping from filtered index to original index
        """
        # Get candidate indices
        candidate_indices = self.get_candidate_indices(year_filter, range_size)

        if not candidate_indices:
            # Return empty arrays with correct dimensions
            empty_embeddings = np.zeros((0, embeddings.shape[1]), dtype=embeddings.dtype)
            return empty_embeddings, []

        # Extract embeddings for candidates
        filtered_embeddings = embeddings[candidate_indices]

        logger.debug(
            f"Filtered embeddings: {embeddings.shape[0]} → {filtered_embeddings.shape[0]} "
            f"({len(candidate_indices) / max(embeddings.shape[0], 1) * 100:.1f}% retained)"
        )

        return filtered_embeddings, candidate_indices

    def get_years_in_range(
        self,
        year_filter: int,
        range_size: int = 2,
    ) -> List[int]:
        """
        Get years that have data within the filter range.

        Args:
            year_filter: Target year
            range_size: Range to include

        Returns:
            List of years with data in range
        """
        min_year = year_filter - range_size
        max_year = year_filter + range_size

        return sorted([
            year for year in self._year_to_indices.keys()
            if min_year <= year <= max_year
        ])

    def get_available_years(self) -> List[int]:
        """Get all years with data."""
        return sorted(self._year_to_indices.keys())

    def get_chunk_count_by_year(self) -> Dict[int, int]:
        """Get count of chunks for each year."""
        return {year: len(indices) for year, indices in self._year_to_indices.items()}


def create_year_prefilter(chunks: List[Chunk]) -> YearPrefilter:
    """Factory function to create year prefilter."""
    return YearPrefilter(chunks)
