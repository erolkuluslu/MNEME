"""
NLI-Based Edge Type Classification Module

Implements NLI-inspired edge classification using cross-encoder models
as described in the paper's Algorithm S1. This provides more accurate
edge type classification compared to keyword heuristics alone.

Edge Types (from paper Table III):
- ELABORATES: Target expands on source topic
- CONTRADICTS: Target presents opposing view
- CAUSES: Source leads to target outcome
- SUPPORTS: Target reinforces source claim
- TEMPORAL_SEQUENCE: Time-ordered relationship
- CROSS_DOMAIN: Different category connection
- SAME_TOPIC: Similar content, same domain
"""

from typing import Tuple, Optional, List
import logging

from src.models.chunk import Chunk
from src.models.graph import EdgeType

logger = logging.getLogger(__name__)

# Try to import sentence-transformers for cross-encoder
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False
    logger.warning(
        "sentence-transformers CrossEncoder not available. "
        "NLI edge typing will fall back to heuristics."
    )


class NLIEdgeTyper:
    """
    NLI-based edge type classifier using cross-encoder models.

    Uses natural language inference to classify relationships between
    text chunks more accurately than keyword heuristics.

    The approach tests several hypothesis templates:
    1. Entailment of elaboration: "The second text elaborates on the first"
    2. Entailment of contradiction: "The second text contradicts the first"
    3. Entailment of causation: "The first text causes or leads to the second"
    4. Entailment of support: "The second text supports the first"

    The edge type is determined by which hypothesis has highest entailment score.
    """

    # Default NLI model - lightweight and accurate
    DEFAULT_MODEL = "cross-encoder/nli-deberta-v3-small"

    # Hypothesis templates for relationship classification
    HYPOTHESIS_TEMPLATES = {
        EdgeType.ELABORATES: "The second passage elaborates on or expands the first passage.",
        EdgeType.CONTRADICTS: "The second passage contradicts or disagrees with the first passage.",
        EdgeType.CAUSES: "The first passage describes something that leads to or causes what is described in the second passage.",
        EdgeType.SUPPORTS: "The second passage provides evidence that supports the first passage.",
        EdgeType.TEMPORAL_SEQUENCE: "The second passage describes events that happened after the first passage.",
    }

    # Label mapping for NLI models (entailment=2, neutral=1, contradiction=0)
    ENTAILMENT_LABEL = 2
    NEUTRAL_LABEL = 1

    # Minimum confidence threshold for NLI prediction
    MIN_CONFIDENCE_THRESHOLD = 0.6

    def __init__(
        self,
        model_name: str = None,
        device: str = None,
        batch_size: int = 32,
    ):
        """
        Initialize NLI edge typer.

        Args:
            model_name: Cross-encoder model name (default: nli-deberta-v3-small)
            device: Device to run model on ('cpu', 'cuda', 'mps')
            batch_size: Batch size for predictions
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.batch_size = batch_size
        self.model = None
        self._device = device

        if HAS_CROSS_ENCODER:
            try:
                self.model = CrossEncoder(self.model_name, device=device)
                logger.info(f"NLIEdgeTyper initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load NLI model: {e}")
                self.model = None

    @property
    def is_available(self) -> bool:
        """Check if NLI classification is available."""
        return self.model is not None

    def classify_edge(
        self,
        source_chunk: Chunk,
        target_chunk: Chunk,
        similarity: float,
        same_category: bool = None,
    ) -> Tuple[EdgeType, float]:
        """
        Classify edge type using NLI inference.

        Args:
            source_chunk: Source chunk
            target_chunk: Target chunk
            similarity: Pre-computed similarity score
            same_category: Whether chunks are same category (computed if None)

        Returns:
            Tuple of (EdgeType, confidence_score)
        """
        if same_category is None:
            same_category = source_chunk.category == target_chunk.category

        # Fast path: Same document, adjacent chunks -> ELABORATES
        if source_chunk.doc_id == target_chunk.doc_id:
            if target_chunk.chunk_index > source_chunk.chunk_index:
                return EdgeType.ELABORATES, 0.95

        # If NLI not available, fall back to heuristics
        if not self.is_available:
            return self._heuristic_fallback(
                source_chunk, target_chunk, similarity, same_category
            )

        # Prepare text pairs for NLI
        source_text = source_chunk.text[:512]  # Truncate for efficiency
        target_text = target_chunk.text[:512]

        # Test each hypothesis
        best_type = EdgeType.SAME_TOPIC
        best_confidence = 0.0

        for edge_type, hypothesis in self.HYPOTHESIS_TEMPLATES.items():
            # Format premise as comparison of the two texts
            premise = f"Text A: {source_text}\n\nText B: {target_text}"

            try:
                # Get NLI prediction
                scores = self.model.predict([(premise, hypothesis)])
                # scores is typically [contradiction, neutral, entailment] for 3-class NLI
                if isinstance(scores, list):
                    score = scores[0]
                else:
                    score = float(scores)

                # For 3-class models, entailment score is the relevant one
                # Some models return scalar (entailment probability)
                if score > best_confidence:
                    best_confidence = score
                    best_type = edge_type

            except Exception as e:
                logger.debug(f"NLI prediction failed for {edge_type}: {e}")
                continue

        # Apply confidence threshold
        if best_confidence < self.MIN_CONFIDENCE_THRESHOLD:
            # Low confidence - use structural/heuristic features
            return self._heuristic_fallback(
                source_chunk, target_chunk, similarity, same_category
            )

        return best_type, best_confidence

    def classify_edges_batch(
        self,
        chunk_pairs: List[Tuple[Chunk, Chunk, float, bool]],
    ) -> List[Tuple[EdgeType, float]]:
        """
        Classify multiple edges in batch for efficiency.

        Args:
            chunk_pairs: List of (source_chunk, target_chunk, similarity, same_category)

        Returns:
            List of (EdgeType, confidence) tuples
        """
        if not self.is_available:
            return [
                self._heuristic_fallback(src, tgt, sim, same_cat)
                for src, tgt, sim, same_cat in chunk_pairs
            ]

        results = []
        for source_chunk, target_chunk, similarity, same_category in chunk_pairs:
            edge_type, confidence = self.classify_edge(
                source_chunk, target_chunk, similarity, same_category
            )
            results.append((edge_type, confidence))

        return results

    def _heuristic_fallback(
        self,
        source_chunk: Chunk,
        target_chunk: Chunk,
        similarity: float,
        same_category: bool,
    ) -> Tuple[EdgeType, float]:
        """
        Fallback to keyword heuristics when NLI is unavailable or low confidence.

        Uses the same logic as EdgeDiscovery._determine_edge_type.
        """
        # Import keyword sets from edge_discovery to avoid duplication
        from .edge_discovery import EdgeDiscovery

        # Same document, later chunk -> elaborates
        if source_chunk.doc_id == target_chunk.doc_id:
            if target_chunk.chunk_index > source_chunk.chunk_index:
                return EdgeType.ELABORATES, 0.9

        combined_text = (source_chunk.text + " " + target_chunk.text).lower()

        # Contradiction keywords
        if any(kw in combined_text for kw in EdgeDiscovery.CONTRADICTION_KEYWORDS):
            return EdgeType.CONTRADICTS, 0.7

        # Causal keywords
        if any(kw in combined_text for kw in EdgeDiscovery.CAUSAL_KEYWORDS):
            return EdgeType.CAUSES, 0.7

        # Support keywords
        if any(kw in combined_text for kw in EdgeDiscovery.SUPPORT_KEYWORDS):
            return EdgeType.SUPPORTS, 0.7

        # Temporal sequence: different years + temporal markers
        if source_chunk.year != target_chunk.year:
            if any(kw in combined_text for kw in EdgeDiscovery.TEMPORAL_KEYWORDS):
                return EdgeType.TEMPORAL_SEQUENCE, 0.7

        # Different category -> cross_domain
        if not same_category:
            return EdgeType.CROSS_DOMAIN, 0.8

        # Default: same category, high similarity -> same_topic
        return EdgeType.SAME_TOPIC, similarity


class HybridEdgeTyper:
    """
    Hybrid edge typer combining NLI and heuristic approaches.

    Uses NLI for high-value edge classification (cross-domain, contradictions)
    and heuristics for simple cases (same document, high similarity same-topic).
    """

    def __init__(
        self,
        nli_typer: Optional[NLIEdgeTyper] = None,
        nli_threshold: float = 0.6,
    ):
        """
        Initialize hybrid typer.

        Args:
            nli_typer: NLI typer instance (created if None)
            nli_threshold: Similarity threshold below which to use NLI
        """
        self.nli_typer = nli_typer or NLIEdgeTyper()
        self.nli_threshold = nli_threshold

    def classify_edge(
        self,
        source_chunk: Chunk,
        target_chunk: Chunk,
        similarity: float,
        same_category: bool = None,
    ) -> Tuple[EdgeType, float]:
        """
        Classify edge using hybrid approach.

        High similarity same-category -> use heuristics (faster)
        Cross-domain or low similarity -> use NLI (more accurate)
        """
        if same_category is None:
            same_category = source_chunk.category == target_chunk.category

        # Fast path: same document
        if source_chunk.doc_id == target_chunk.doc_id:
            if target_chunk.chunk_index > source_chunk.chunk_index:
                return EdgeType.ELABORATES, 0.95

        # High similarity same-category: heuristics sufficient
        if same_category and similarity > self.nli_threshold:
            return self.nli_typer._heuristic_fallback(
                source_chunk, target_chunk, similarity, same_category
            )

        # Use NLI for cross-domain or ambiguous cases
        return self.nli_typer.classify_edge(
            source_chunk, target_chunk, similarity, same_category
        )


def create_edge_typer(
    mode: str = "hybrid",
    model_name: str = None,
    device: str = None,
) -> NLIEdgeTyper:
    """
    Factory function to create edge typer.

    Args:
        mode: "nli" for pure NLI, "heuristic" for pure heuristics, "hybrid" for combined
        model_name: NLI model name (for nli/hybrid modes)
        device: Device for NLI model

    Returns:
        Edge typer instance
    """
    if mode == "heuristic":
        # Return NLI typer without model (will use heuristic fallback)
        typer = NLIEdgeTyper.__new__(NLIEdgeTyper)
        typer.model = None
        typer.model_name = None
        typer.batch_size = 32
        logger.info("Created heuristic-only edge typer")
        return typer

    nli_typer = NLIEdgeTyper(model_name=model_name, device=device)

    if mode == "hybrid":
        return HybridEdgeTyper(nli_typer=nli_typer)

    return nli_typer
