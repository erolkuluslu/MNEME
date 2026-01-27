"""
Gemini LLM Provider

Google Gemini integration for answer generation.
Includes dual-model selection for query complexity.
"""

import os
from typing import Optional, TYPE_CHECKING
import logging

from .base import BaseLLMProvider

if TYPE_CHECKING:
    from src.models.query import QueryPlan, QueryType

logger = logging.getLogger(__name__)


class GeminiModelSelector:
    """
    Selects appropriate Gemini model based on query complexity.

    Uses complex model for synthesis, multi-hop, and exploratory queries.
    Uses simple model for factual, direct retrieval queries.
    """

    # Default models - can be overridden via config
    DEFAULT_COMPLEX_MODEL = "models/gemini-2.5-flash-preview-04-17"
    DEFAULT_SIMPLE_MODEL = "models/gemini-2.0-flash-lite"

    # Query types that require complex reasoning
    COMPLEX_QUERY_TYPES = {"synthesis", "exploratory", "comparison"}

    # Confidence levels that indicate need for more reasoning
    LOW_CONFIDENCE_LEVELS = {"partial", "no_match", "low"}

    def __init__(
        self,
        complex_model: Optional[str] = None,
        simple_model: Optional[str] = None,
    ):
        """
        Initialize model selector.

        Args:
            complex_model: Model for complex queries (synthesis, multi-hop)
            simple_model: Model for simple queries (factual, direct)
        """
        self.complex_model = complex_model or self.DEFAULT_COMPLEX_MODEL
        self.simple_model = simple_model or self.DEFAULT_SIMPLE_MODEL

    def select_model(
        self,
        query_plan: "QueryPlan",
        retrieval_confidence: str,
    ) -> str:
        """
        Select appropriate Gemini model based on query complexity.

        Uses complex model for:
        - SYNTHESIS, EXPLORATORY, COMPARISON query types
        - Low retrieval confidence (needs more reasoning)
        - High complexity scores
        - Multi-hop reasoning detected (many expanded terms)

        Args:
            query_plan: Analyzed query plan
            retrieval_confidence: Confidence level from retrieval

        Returns:
            Model name to use for generation
        """
        complex_indicators = []

        # Check query type
        if query_plan.query_type.value in self.COMPLEX_QUERY_TYPES:
            complex_indicators.append("query_type")

        # Check retrieval confidence
        if retrieval_confidence in self.LOW_CONFIDENCE_LEVELS:
            complex_indicators.append("low_confidence")

        # Check complexity score
        if query_plan.complexity_score >= 0.7:
            complex_indicators.append("high_complexity")

        # Check expansion (many terms = multi-hop potential)
        if len(query_plan.expansion.expanded_terms) > 5:
            complex_indicators.append("multi_hop")

        # Check for year-constrained queries with sparse results
        if query_plan.year_filter and retrieval_confidence in self.LOW_CONFIDENCE_LEVELS:
            complex_indicators.append("sparse_temporal")

        # Use complex model if 2+ indicators
        if len(complex_indicators) >= 2:
            logger.info(
                f"Selected complex model due to: {complex_indicators}"
            )
            return self.complex_model

        logger.debug(
            f"Selected simple model (indicators: {complex_indicators})"
        )
        return self.simple_model

    def get_model_info(self) -> dict:
        """Get info about available models."""
        return {
            "complex_model": self.complex_model,
            "simple_model": self.simple_model,
            "complex_query_types": list(self.COMPLEX_QUERY_TYPES),
            "low_confidence_levels": list(self.LOW_CONFIDENCE_LEVELS),
        }


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider.

    Uses the google-genai package for API access.
    """

    def __init__(
        self,
        model_name: str = "models/gemini-2.0-flash",
        api_key: Optional[str] = None,
    ):
        """
        Initialize Gemini provider.

        Args:
            model_name: Gemini model name
            api_key: API key (defaults to GOOGLE_API_KEY env var)
        """
        super().__init__(model_name)

        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self._model = None
        self._available = None

    @property
    def model(self):
        """Lazy load the Gemini model."""
        if self._model is None:
            try:
                from google import genai

                if not self.api_key:
                    raise ValueError("Gemini API key not found")

                client = genai.Client(api_key=self.api_key)
                self._model = client
                self._available = True
                logger.info(f"Initialized Gemini client with model: {self.model_name}")
            except ImportError:
                logger.error("google-genai not installed")
                self._available = False
                raise ImportError(
                    "google-genai is required. "
                    "Install with: pip install google-genai"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self._available = False
                raise

        return self._model

    def is_available(self) -> bool:
        """Check if Gemini is available."""
        if self._available is not None:
            return self._available

        try:
            from google import genai
            self._available = self.api_key is not None
        except ImportError:
            self._available = False

        return self._available

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        model_override: Optional[str] = None,
    ) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            model_override: Optional model name to use instead of default

        Returns:
            Generated text
        """
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        try:
            # Determine which model to use
            model_to_use = model_override if model_override else self.model_name

            if model_override and model_override != self.model_name:
                logger.info(f"Using model override: {model_override}")

            # Generate content using the new API
            response = self.model.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=config,
            )

            if response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini")
                return ""

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise


def create_gemini_provider(
    model_name: str = "models/gemini-2.0-flash",
    api_key: Optional[str] = None,
) -> GeminiProvider:
    """Factory function to create Gemini provider."""
    return GeminiProvider(model_name=model_name, api_key=api_key)
