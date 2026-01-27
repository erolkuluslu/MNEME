"""
Layer 6: Thinking Engine

Gap detection, iterative retrieval, context building, source importance scoring,
and gap enforcement.
"""

from .gap_detector import GapDetector, create_gap_detector
from .context_builder import ContextBuilder, create_context_builder
from .gap_enforcer import GapEnforcer, create_gap_enforcer
from .source_scorer import (
    SourceImportanceScorer,
    ScoredSource,
    SourceScoringResult,
    create_source_scorer,
)

__all__ = [
    "GapDetector",
    "create_gap_detector",
    "ContextBuilder",
    "create_context_builder",
    "GapEnforcer",
    "create_gap_enforcer",
    "SourceImportanceScorer",
    "ScoredSource",
    "SourceScoringResult",
    "create_source_scorer",
]
