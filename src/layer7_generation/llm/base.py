"""
Base LLM Provider

Abstract base class for LLM integrations.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM implementations must inherit from this class.
    """

    def __init__(self, model_name: str):
        """
        Initialize LLM provider.

        Args:
            model_name: Name of the model
        """
        self.model_name = model_name

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum response tokens

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Default implementation uses word-based approximation.
        """
        return len(text.split()) * 4 // 3
