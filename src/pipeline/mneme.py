"""
MNEME Main Pipeline

Main orchestrator coordinating all 7 layers of the MNEME RAG system.
Enhanced with community-aware retrieval for narrative queries.
"""

import time
from typing import List, Optional
import logging

try:
    import networkx as nx
except ImportError:
    nx = None

import numpy as np

from src.config import MNEMEConfig
from src.models.chunk import Chunk
from src.models.answer import EnhancedAnswer
from src.models.graph import KnowledgeStructures
from src.models.query import QueryType, QueryIntent

from src.layer2_graph.embeddings.base import BaseEmbeddingEngine
from src.layer2_graph.similarity.base import BaseSimilarityEngine
from src.layer4_query import QueryAnalyzer
from src.layer5_retrieval import RetrievalEngine, CommunityAwareStrategy
from src.layer6_thinking import GapDetector, ContextBuilder, ContextResult
from src.layer7_generation import AnswerGenerator, CitationGenerator, CitationValidator
from src.layer7_generation.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# Keywords that indicate narrative/exploratory queries
NARRATIVE_KEYWORDS = [
    'overview', 'summarize', 'describe', 'explain', 'who am i',
    'what do i know', 'tell me about', 'bird', 'big picture',
    'across', 'themes', 'patterns', 'synthesis', 'comprehensive',
]


class MNEME:
    """
    Main MNEME system coordinating all 7 layers.

    Layer 1: Document Processing (external - done during indexing)
    Layer 2: Knowledge Graph (embeddings, similarity, graph)
    Layer 3: Knowledge Structures (communities, hubs, bridges)
    Layer 4: Query Analyzer
    Layer 5: Retrieval Engine
    Layer 6: Thinking Engine (gap detection, context building)
    Layer 7: Answer Generation
    """

    def __init__(
        self,
        chunks: List[Chunk],
        embeddings: np.ndarray,
        graph: "nx.DiGraph",
        config: MNEMEConfig,
        embedding_engine: BaseEmbeddingEngine,
        similarity_engine: BaseSimilarityEngine,
        llm_provider: BaseLLMProvider,
        knowledge_structures: Optional[KnowledgeStructures] = None,
    ):
        """
        Initialize MNEME system.

        Args:
            chunks: All indexed chunks
            embeddings: Embedding matrix
            graph: Knowledge graph
            config: MNEME configuration
            embedding_engine: Embedding engine for query encoding
            similarity_engine: Similarity search engine
            llm_provider: LLM for answer generation
            knowledge_structures: Optional pre-computed structures
        """
        self.chunks = chunks
        self.embeddings = embeddings
        self.graph = graph
        self.config = config
        self.embedding_engine = embedding_engine
        self.similarity_engine = similarity_engine
        self.llm_provider = llm_provider
        self.knowledge_structures = knowledge_structures

        # Build index if needed
        if not similarity_engine.is_built:
            similarity_engine.build_index(embeddings)

        # Layer 4: Query Analyzer
        self.query_analyzer = QueryAnalyzer(config)

        # Layer 5: Retrieval Engine
        self.retrieval_engine = RetrievalEngine(
            chunks=chunks,
            embeddings=embeddings,
            config=config,
            embedding_engine=embedding_engine,
            similarity_engine=similarity_engine,
            graph=graph,  # Pass graph for expansion
        )

        # Layer 5+: Community-Aware Retrieval (for narrative queries)
        self.community_aware_strategy = None
        if config.community_aware_retrieval and knowledge_structures:
            self.community_aware_strategy = CommunityAwareStrategy(
                chunks=chunks,
                embeddings=embeddings,
                embedding_engine=embedding_engine,
                similarity_engine=similarity_engine,
                knowledge_structures=knowledge_structures,
                community_boost=config.community_boost,
                bridge_boost=config.bridge_boost,
            )
            logger.info("Community-aware retrieval enabled")

        # Layer 6: Thinking Engine
        self.gap_detector = GapDetector(
            available_years=self.retrieval_engine.get_available_years(),
            available_categories=self.retrieval_engine.get_available_categories(),
        )
        self.context_builder = ContextBuilder(
            max_context_length=config.max_context_length,
            include_community_summaries=config.include_community_summaries,
        )

        # Layer 7: Answer Generator
        self.answer_generator = AnswerGenerator(config, llm_provider)
        self.citation_generator = CitationGenerator(chunks)
        self.citation_validator = CitationValidator()

        logger.info(
            f"Initialized MNEME with {len(chunks)} chunks, "
            f"{self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

    def _is_narrative_query(self, plan, question: str) -> bool:
        """Check if query is narrative/exploratory."""
        NARRATIVE_TYPES = {QueryType.SYNTHESIS, QueryType.EXPLORATORY}
        if plan.query_type in NARRATIVE_TYPES:
            return True
        if plan.intent == QueryIntent.EXPLANATORY:
            return True
        query_lower = question.lower()
        return any(kw in query_lower for kw in NARRATIVE_KEYWORDS)

    def query(self, question: str) -> EnhancedAnswer:
        """
        Process a query through all MNEME layers.

        Enhanced: Uses community-aware retrieval for narrative queries.

        Args:
            question: User question

        Returns:
            EnhancedAnswer with response and citations
        """
        start_time = time.time()

        try:
            # Layer 4: Analyze query
            plan = self.query_analyzer.analyze(question)
            logger.debug(f"Query plan: {plan}")

            # Layer 5: Retrieve relevant chunks
            # Use community-aware strategy for narrative queries if available
            if self.community_aware_strategy and self._is_narrative_query(plan, question):
                logger.debug("Using community-aware retrieval for narrative query")
                retrieval_result = self.community_aware_strategy.retrieve(
                    question, plan, self.config.synthesis_max_docs
                )
            else:
                retrieval_result = self.retrieval_engine.retrieve(question, plan)

            logger.debug(
                f"Retrieved {len(retrieval_result.candidates)} chunks, "
                f"confidence={retrieval_result.confidence.value}"
            )

            # Layer 6: Detect gaps and build context
            gaps = self.gap_detector.detect_gaps(retrieval_result, plan)
            retrieval_result.coverage_gaps = gaps
            retrieval_result.missing_years = self.gap_detector.get_missing_years(
                retrieval_result, plan
            )

            # Build context with metadata for proper citation validation
            context_result = self.context_builder.build_context_with_metadata(retrieval_result, plan)
            context = context_result.context
            included_indices = context_result.included_indices

            if context_result.was_truncated:
                logger.warning(
                    f"Context was truncated: {context_result.chunks_included} of "
                    f"{context_result.total_chunks_available} chunks included"
                )

            # Layer 7: Generate answer with included indices for citation validation
            answer_text, stats = self.answer_generator.generate(
                question, plan, retrieval_result, context, included_indices
            )

            # Validate citations in the generated answer
            valid_year_indices = None
            if self.config.year_strict_mode and plan.year_filter:
                valid_year_indices = [
                    i + 1 for i, c in enumerate(retrieval_result.candidates[:len(included_indices)])
                    if c.year_matched
                ]

            _, citation_warnings, citations_valid = self.citation_validator.validate_citations(
                answer_text, included_indices, valid_year_indices
            )

            if citation_warnings:
                for warning in citation_warnings:
                    logger.warning(f"Citation validation: {warning}")

            # Create citations only for chunks actually in context
            # Use candidates up to the number of included indices
            candidates_in_context = retrieval_result.candidates[:len(included_indices)]
            citations = self.citation_generator.create_citations(
                candidates_in_context,
                plan.year_filter,
            )

            total_latency = (time.time() - start_time) * 1000

            # Build enhanced answer
            enhanced_answer = self.answer_generator.create_enhanced_answer(
                answer_text=answer_text,
                question=question,
                plan=plan,
                retrieval_result=retrieval_result,
                stats=stats,
                citations=citations,
                total_latency_ms=total_latency,
            )

            logger.info(
                f"Query completed in {total_latency:.0f}ms, "
                f"confidence={enhanced_answer.confidence}"
            )

            return enhanced_answer

        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            return EnhancedAnswer.error_response(question, str(e))

    def get_stats(self) -> dict:
        """Get system statistics."""
        return {
            "num_chunks": len(self.chunks),
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "available_years": self.retrieval_engine.get_available_years(),
            "available_categories": self.retrieval_engine.get_available_categories(),
            "embedding_dimension": self.embedding_engine.dimension,
        }


def create_mneme(
    chunks: List[Chunk],
    embeddings: np.ndarray,
    graph: "nx.DiGraph",
    config: MNEMEConfig,
    embedding_engine: BaseEmbeddingEngine,
    similarity_engine: BaseSimilarityEngine,
    llm_provider: BaseLLMProvider,
) -> MNEME:
    """Factory function to create MNEME system."""
    return MNEME(
        chunks=chunks,
        embeddings=embeddings,
        graph=graph,
        config=config,
        embedding_engine=embedding_engine,
        similarity_engine=similarity_engine,
        llm_provider=llm_provider,
    )
