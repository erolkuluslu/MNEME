"""
Layer 5: Retrieval Engine

Retrieval strategies, ranking, boosting, and pre-filtering.
"""

from .engine import RetrievalEngine, create_retrieval_engine
from .strategies import (
    BaseRetrievalStrategy,
    HybridRRFStrategy,
    create_hybrid_rrf_strategy,
    CommunityAwareStrategy,
    CommunityAwareRetrievalResult,
    create_community_aware_strategy,
)
from .prefilter import YearPrefilter, create_year_prefilter

__all__ = [
    "RetrievalEngine",
    "create_retrieval_engine",
    "BaseRetrievalStrategy",
    "HybridRRFStrategy",
    "create_hybrid_rrf_strategy",
    "CommunityAwareStrategy",
    "CommunityAwareRetrievalResult",
    "create_community_aware_strategy",
    "YearPrefilter",
    "create_year_prefilter",
]
