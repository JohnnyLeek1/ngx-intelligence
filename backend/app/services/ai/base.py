"""
Abstract base interface for AI/LLM providers.

Defines the contract that all AI providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIResponse:
    """Container for AI response data."""

    def __init__(
        self,
        content: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.metadata = metadata or {}


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All AI providers (Ollama, OpenAI, Anthropic, etc.) must implement
    this interface to ensure consistent behavior across the application.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AIResponse:
        """
        Generate a completion from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            AIResponse with generated content

        Raises:
            AIProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Parsed JSON response

        Raises:
            AIProviderError: If generation fails or JSON is invalid
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """
        List available models.

        Returns:
            List of model names

        Raises:
            AIProviderError: If listing fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the AI provider is accessible.

        Returns:
            True if provider is accessible, False otherwise
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections or cleanup resources."""
        pass


class AIProviderError(Exception):
    """Exception raised for AI provider errors."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(self.message)
