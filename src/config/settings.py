"""
MNEME Configuration Settings

Central configuration dataclass for all 7 layers of the MNEME architecture.
Supports environment variable overrides and validation.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import os
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Available chunking strategies for document processing."""
    WORD_COUNT = "word_count"
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"


class SimilarityEngine(str, Enum):
    """Available similarity engines for vector search."""
    NUMPY = "numpy"
    FAISS = "faiss"


class RetrievalStrategy(str, Enum):
    """Available retrieval strategies."""
    VECTOR_ONLY = "vector_only"
    BM25_ONLY = "bm25_only"
    HYBRID_RRF = "hybrid_rrf"


class LLMProvider(str, Enum):
    """Available LLM providers for answer generation."""
    GEMINI = "gemini"
    OPENAI = "openai"


@dataclass
class MNEMEConfig:
    """
    Central configuration for the MNEME 7-Layer RAG Architecture.

    All settings can be overridden via environment variables with MNEME_ prefix.
    Example: MNEME_TARGET_CHUNK_SIZE=500 overrides target_chunk_size.
    """

    # ==================== Layer 1: Document Processing ====================
    target_chunk_size: int = 300  # Target words per chunk
    min_chunk_size: int = 50  # Minimum words for valid chunk
    max_chunk_size: int = 600  # Maximum words per chunk
    chunking_strategy: str = ChunkingStrategy.WORD_COUNT.value
    chunk_overlap: int = 50  # Word overlap between chunks

    # ==================== Layer 2: Knowledge Graph ====================
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32

    # Similarity thresholds (paper specification)
    semantic_similarity_threshold: float = 0.45  # Stricter: 0.38 -> 0.45
    cross_domain_threshold: float = 0.40  # Stricter: 0.30 -> 0.40

    # Graph construction
    max_total_edges: int = 3000
    top_k_neighbors: int = 5  # Stricter: 15 -> 5 to reduce hairball
    similarity_engine: str = SimilarityEngine.NUMPY.value

    # ==================== Layer 3: Knowledge Structures ====================
    louvain_resolution: float = 0.20
    min_community_size: int = 3
    hub_threshold: float = 0.9  # Top 10% by degree (paper: percentile_90)
    bridge_min_communities: int = 3  # Min communities to be a bridge (stricter than 2)
    bridge_betweenness_threshold: float = 0.1  # Alternative betweenness threshold for bridges

    # Adaptive Resolution Settings
    # Paper specifies resolution=0.20, but adaptive tuning is needed for
    # datasets smaller than the paper's 264 chunks to achieve meaningful communities
    adaptive_resolution: bool = True  # Fallback to adaptive if fixed produces <3 communities
    target_min_communities: int = 5  # Minimum communities to target
    target_max_communities: int = 15  # Maximum communities to target
    louvain_min_resolution: float = 0.1  # Lower bound for resolution search
    louvain_max_resolution: float = 2.0  # Upper bound for resolution search

    # Community Summary Settings
    community_summary_enabled: bool = True  # Generate LLM summaries for communities
    summary_max_chunks: int = 10  # Max chunks per summary
    summary_max_length: int = 500  # Max summary tokens

    # ==================== Layer 4: Query Analysis ====================
    enable_query_expansion: bool = True
    max_expansion_terms: int = 3
    year_detection_patterns: List[str] = field(default_factory=lambda: [
        r'\b(19|20)\d{2}\b',  # Year patterns like 2020, 1995
        r'\bin\s+(19|20)\d{2}\b',  # "in 2020"
        r'\bfrom\s+(19|20)\d{2}\b',  # "from 2020"
    ])

    # ==================== Layer 5: Retrieval Engine ====================
    retrieval_strategy: str = RetrievalStrategy.HYBRID_RRF.value

    # RRF (Reciprocal Rank Fusion) settings
    rrf_k_constant: int = 60
    dense_weight: float = 1.0
    sparse_weight: float = 0.5

    # Scoring mode: "blended" uses weighted dense+sparse, "rrf" uses rank fusion
    scoring_mode: str = "blended"
    dense_alpha: float = 0.6  # Weight for dense score in blended mode
    sparse_beta: float = 0.4  # Weight for sparse score in blended mode

    # Adaptive RRF: compute k from corpus size instead of hardcoded 60
    adaptive_rrf_k: bool = True
    rrf_k_ratio: float = 0.1  # k = max(10, corpus_size * ratio)

    # Year prefilter: narrow candidates before dense search
    use_year_prefilter: bool = True

    # Graph Expansion Settings (New)
    enable_graph_expansion: bool = True  # Expand results using graph neighbors
    graph_expansion_max_neighbors: int = 3  # Max neighbors to add per candidate
    graph_expansion_edge_types: List[str] = field(default_factory=lambda: ["CAUSES", "CONTRADICTS", "SUPPORTS"])

    # Boosting factors (multiplicative in blended mode, additive in rrf mode)
    year_match_boost: float = 0.5  # Boost factor for exact year match
    category_match_boost: float = 0.2  # Boost factor for category match
    year_expansion_range: int = 2  # Years to consider for partial matches

    # Semantic threshold for boosting (CRITICAL FIX)
    # Chunks below this semantic relevance score get no year/category boost
    # This prevents irrelevant documents from ranking high just because they match year
    semantic_relevance_threshold: float = 0.3

    # Document limits per query type
    specific_min_docs: int = 5
    specific_max_docs: int = 10
    synthesis_min_docs: int = 8
    synthesis_max_docs: int = 12
    comparison_min_docs: int = 6
    comparison_max_docs: int = 15

    # Community-Aware Retrieval Settings (narrative/exploratory queries)
    community_aware_retrieval: bool = True  # Enable community context for narrative queries
    community_boost: float = 0.3  # Score boost for chunks in same community as top results
    bridge_boost: float = 0.4  # Score boost for bridge nodes connecting communities
    include_community_summaries: bool = True  # Include summaries in context for narrative queries

    # ==================== Layer 6: Thinking Engine ====================
    enable_gap_detection: bool = True
    enable_iterative_retrieval: bool = True
    max_retrieval_iterations: int = 3
    gap_threshold: float = 0.3  # Threshold for detecting coverage gaps

    # Source Importance Scoring (thinking mechanism)
    source_importance_threshold: float = 0.4  # Min importance to include in context
    max_context_sources: int = 8  # Max sources to include in LLM context
    relevance_weight: float = 0.4  # Weight for retrieval relevance score
    year_match_weight: float = 0.25  # Weight for year match
    category_match_weight: float = 0.15  # Weight for category match
    diversity_weight: float = 0.2  # Weight for source diversity

    # ==================== Layer 7: Answer Generation ====================
    llm_provider: str = LLMProvider.GEMINI.value
    answer_model: str = "gemini-3-flash-preview"
    answer_temperature: float = 0.3
    max_tokens: int = 2000

    # Dual Model Selection
    model_selection_enabled: bool = True  # Enable automatic model selection
    complex_model: str = "gemini-3-flash-preview"  # For synthesis, multi-hop
    simple_model: str = "gemini-flash-latest"  # For factual, direct queries

    # Critical fix settings
    year_strict_mode: bool = True  # Enforce year-specific citations
    min_year_matched_for_confidence: int = 1  # Min docs for high confidence
    
    # Generic Time Awareness (New)
    enable_time_extraction: bool = True # General time extraction beyond just years
    date_format_patterns: List[str] = field(default_factory=lambda: [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
    ])

    # OpenAI fallback settings
    openai_model: str = "gpt-4-turbo-preview"
    openai_api_key: Optional[str] = None

    # Gemini settings
    gemini_api_key: Optional[str] = None

    # LLM-as-Judge Evaluation
    enable_llm_judge: bool = True  # Enable LLM-based evaluation
    judge_temperature: float = 0.1  # Low temp for consistent evaluation
    judge_model: str = "models/gemini-2.0-flash"  # Model for judging

    # ==================== API Settings ====================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

    # ==================== Persistence ====================
    artifacts_dir: str = "artifacts"
    cache_embeddings: bool = True
    cache_graph: bool = True

    # ==================== Logging ====================
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_timing: bool = True

    def __post_init__(self):
        """Load environment variable overrides and validate configuration."""
        self._load_env_overrides()
        self._validate()

    def _load_env_overrides(self):
        """Load configuration from environment variables with MNEME_ prefix."""
        for field_name in self.__dataclass_fields__:
            env_key = f"MNEME_{field_name.upper()}"
            env_value = os.environ.get(env_key)

            if env_value is not None:
                field_type = self.__dataclass_fields__[field_name].type

                # Type conversion
                if field_type == int:
                    setattr(self, field_name, int(env_value))
                elif field_type == float:
                    setattr(self, field_name, float(env_value))
                elif field_type == bool:
                    setattr(self, field_name, env_value.lower() in ('true', '1', 'yes'))
                elif field_type == str or field_type == Optional[str]:
                    setattr(self, field_name, env_value)

        # Special handling for API keys
        if self.gemini_api_key is None:
            self.gemini_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

        if self.openai_api_key is None:
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")

    def _validate(self):
        """Validate configuration values."""
        if self.target_chunk_size <= 0:
            raise ValueError("target_chunk_size must be positive")

        if self.min_chunk_size >= self.target_chunk_size:
            raise ValueError("min_chunk_size must be less than target_chunk_size")

        if not 0.0 <= self.semantic_similarity_threshold <= 1.0:
            raise ValueError("semantic_similarity_threshold must be between 0 and 1")

        if not 0.0 <= self.cross_domain_threshold <= 1.0:
            raise ValueError("cross_domain_threshold must be between 0 and 1")

        if self.rrf_k_constant <= 0:
            raise ValueError("rrf_k_constant must be positive")

        if self.scoring_mode not in ("blended", "rrf"):
            raise ValueError("scoring_mode must be 'blended' or 'rrf'")

        if not 0.0 <= self.dense_alpha <= 1.0:
            raise ValueError("dense_alpha must be between 0 and 1")

        if not 0.0 <= self.sparse_beta <= 1.0:
            raise ValueError("sparse_beta must be between 0 and 1")

        if self.rrf_k_ratio <= 0:
            raise ValueError("rrf_k_ratio must be positive")

        if not 0.0 <= self.answer_temperature <= 2.0:
            raise ValueError("answer_temperature must be between 0 and 2")

        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

    @classmethod
    def from_dict(cls, config_dict: dict) -> "MNEMEConfig":
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        """Export configuration to dictionary."""
        return {
            field_name: getattr(self, field_name)
            for field_name in self.__dataclass_fields__
        }

    @classmethod
    def for_development(cls) -> "MNEMEConfig":
        """Factory method for development configuration."""
        return cls(
            log_level="DEBUG",
            api_debug=True,
            enable_timing=True,
        )

    @classmethod
    def for_production(cls) -> "MNEMEConfig":
        """Factory method for production configuration."""
        return cls(
            log_level="WARNING",
            api_debug=False,
            similarity_engine=SimilarityEngine.FAISS.value,
            cache_embeddings=True,
            cache_graph=True,
        )

    @classmethod
    def for_testing(cls) -> "MNEMEConfig":
        """Factory method for testing configuration."""
        return cls(
            target_chunk_size=100,
            max_total_edges=100,
            top_k_neighbors=5,
            specific_max_docs=3,
            synthesis_max_docs=5,
            log_level="DEBUG",
        )
