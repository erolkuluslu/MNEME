"""
Layer 3: Knowledge Structures

Community detection, hub/bridge identification, and hierarchical summaries.
"""

from .community import (
    CommunityDetector,
    AdaptiveCommunityDetector,
    detect_communities,
    detect_communities_adaptive,
)
from .hubs_bridges import HubBridgeDetector, detect_hubs_and_bridges
from .summaries import CommunitySummarizer, HierarchicalSummarizer, create_community_summarizer

__all__ = [
    "CommunityDetector",
    "AdaptiveCommunityDetector",
    "detect_communities",
    "detect_communities_adaptive",
    "HubBridgeDetector",
    "detect_hubs_and_bridges",
    "CommunitySummarizer",
    "HierarchicalSummarizer",
    "create_community_summarizer",
]
