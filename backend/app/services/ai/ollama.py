"""
Ollama LLM provider implementation.

Integrates with local or remote Ollama instances for AI processing.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.core.logging import get_logger
from app.services.ai.base import AIProviderError, AIResponse, BaseLLMProvider


logger = get_logger(__name__)


class OllamaError(AIProviderError):
    """Base exception for Ollama-specific errors."""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message=message, provider="ollama", original_error=original_error)


class OllamaTimeoutError(OllamaError):
    """Exception raised when Ollama request times out."""

    def __init__(self, message: str = "Ollama request timed out"):
        super().__init__(
            f"{message}. Try increasing the timeout or using a smaller model."
        )


class OllamaModelNotFoundError(OllamaError):
    """Exception raised when requested model is not available."""

    def __init__(self, model: str, available_models: Optional[List[str]] = None):
        msg = f"Model '{model}' not found in Ollama"
        if available_models:
            msg += f". Available models: {', '.join(available_models[:5])}"
            if len(available_models) > 5:
                msg += f" (and {len(available_models) - 5} more)"
        msg += ". Use 'ollama pull {model}' to download it."
        super().__init__(msg)


class OllamaConnectionError(OllamaError):
    """Exception raised when cannot connect to Ollama."""

    def __init__(self, base_url: str):
        super().__init__(
            f"Cannot connect to Ollama at {base_url}. "
            "Ensure Ollama is running with 'ollama serve'."
        )


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider implementation.

    Connects to Ollama API for document processing tasks.

    Example:
        >>> provider = OllamaProvider(
        ...     base_url="http://localhost:11434",
        ...     model="llama3.2"
        ... )
        >>> response = await provider.generate(
        ...     prompt="Classify this document",
        ...     system_prompt="You are a document classifier"
        ... )
        >>> print(response.content)
    """

    # Model aliases for convenience
    MODEL_ALIASES = {
        "llama3": "llama3.2",
        "llama2": "llama2:latest",
        "mistral": "mistral:latest",
        "mixtral": "mixtral:latest",
        "codellama": "codellama:latest",
    }

    # Context length limits for common models (in tokens)
    CONTEXT_LIMITS = {
        "llama3.2": 128000,
        "llama3.1": 128000,
        "llama2": 4096,
        "mistral": 32000,
        "mixtral": 32000,
        "codellama": 16000,
    }

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 120,
        max_retries: int = 3,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        seed: Optional[int] = None,
    ):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Default model to use (e.g., "llama3.2")
            timeout: Request timeout in seconds (default: 120)
            max_retries: Maximum retry attempts (default: 3)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            top_p: Nucleus sampling parameter (optional)
            top_k: Top-k sampling parameter (optional)
            repeat_penalty: Penalty for repeating tokens (optional)
            seed: Random seed for reproducibility (optional)
        """
        self.base_url = base_url.rstrip("/")
        self.model = self._resolve_model_alias(model)
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repeat_penalty = repeat_penalty
        self.seed = seed
        self._client: Optional[httpx.AsyncClient] = None

        # Model cache with TTL
        self._models_cache: Optional[List[str]] = None
        self._models_cache_time: Optional[datetime] = None
        self._models_cache_ttl: int = 300  # 5 minutes

        # Track first use for logging
        self._first_use_logged: bool = False

    def _resolve_model_alias(self, model: str) -> str:
        """
        Resolve model aliases to actual model names.

        Args:
            model: Model name or alias

        Returns:
            Resolved model name
        """
        return self.MODEL_ALIASES.get(model, model)

    def _build_options(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Build Ollama options dictionary.

        Args:
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters

        Returns:
            Options dictionary for Ollama API
        """
        options: Dict[str, Any] = {}

        # Temperature
        if temperature is not None:
            options["temperature"] = temperature
        elif self.temperature is not None:
            options["temperature"] = self.temperature

        # Max tokens (Ollama uses num_predict)
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        # Optional parameters
        if self.top_p is not None:
            options["top_p"] = self.top_p
        if self.top_k is not None:
            options["top_k"] = self.top_k
        if self.repeat_penalty is not None:
            options["repeat_penalty"] = self.repeat_penalty
        if self.seed is not None:
            options["seed"] = self.seed

        # Override with any kwargs
        for key in ["top_p", "top_k", "repeat_penalty", "seed", "num_predict"]:
            if key in kwargs:
                options[key] = kwargs[key]

        return options

    def _estimate_token_count(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token on average
        return len(text) // 4

    def _check_context_length(self, prompt: str, system_prompt: Optional[str] = None) -> None:
        """
        Check if prompt exceeds model context length and warn.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
        """
        # Get context limit for model (use base model name)
        model_base = self.model.split(":")[0]
        context_limit = self.CONTEXT_LIMITS.get(model_base, 4096)

        # Estimate tokens
        total_text = prompt
        if system_prompt:
            total_text = system_prompt + "\n\n" + total_text

        estimated_tokens = self._estimate_token_count(total_text)

        # Warn if approaching limit (use 80% threshold)
        if estimated_tokens > context_limit * 0.8:
            logger.warning(
                f"Prompt may exceed context length for {self.model}. "
                f"Estimated tokens: {estimated_tokens}, limit: {context_limit}"
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def _log_first_use(self) -> None:
        """Log model information on first use."""
        if not self._first_use_logged:
            try:
                models = await self.list_models()
                if self.model in models:
                    logger.info(
                        f"Using Ollama model '{self.model}' at {self.base_url}"
                    )
                    self._first_use_logged = True
                else:
                    logger.warning(
                        f"Model '{self.model}' not found. Available: {models[:3]}"
                    )
            except Exception as e:
                logger.debug(f"Could not log first use: {e}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AIResponse:
        """
        Generate a completion from Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters (top_p, top_k, etc.)

        Returns:
            AIResponse with generated content

        Raises:
            OllamaTimeoutError: If request times out
            OllamaConnectionError: If cannot connect to Ollama
            OllamaError: If generation fails

        Example:
            >>> response = await provider.generate(
            ...     prompt="What type of document is this?",
            ...     system_prompt="You are a classifier",
            ...     temperature=0.7
            ... )
        """
        await self._log_first_use()
        logger.debug(f"Generating completion with Ollama model '{self.model}'")

        # Check context length
        self._check_context_length(prompt, system_prompt)

        # Build request payload
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": self._build_options(temperature, max_tokens, **kwargs),
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Make API call with retries
        start_time = time.time()
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                client = await self._get_client()
                logger.debug(f"Ollama request (attempt {attempt + 1}): {payload}")

                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()

                result = response.json()
                elapsed_time = time.time() - start_time

                logger.debug(
                    f"Ollama response received in {elapsed_time:.2f}s: "
                    f"{result.get('response', '')[:100]}"
                )

                # Extract response content
                content = result.get("response", "").strip()

                # Extract token usage if available
                prompt_tokens = result.get("prompt_eval_count", 0)
                completion_tokens = result.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens

                # Build metadata
                metadata = {
                    "model_used": result.get("model", self.model),
                    "elapsed_time": elapsed_time,
                    "done": result.get("done", False),
                    "context": result.get("context", []),
                }

                return AIResponse(
                    content=content,
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    metadata=metadata,
                )

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Ollama request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except httpx.ConnectError as e:
                last_error = e
                logger.error(f"Cannot connect to Ollama at {self.base_url}")
                raise OllamaConnectionError(self.base_url) from e

            except httpx.HTTPStatusError as e:
                last_error = e
                error_detail = e.response.text
                logger.error(f"Ollama HTTP error: {error_detail}")

                # Check for model not found
                if e.response.status_code == 404 or "not found" in error_detail.lower():
                    models = await self.list_models()
                    raise OllamaModelNotFoundError(self.model, models) from e

                raise OllamaError(f"Ollama HTTP error: {error_detail}", e) from e

            except Exception as e:
                last_error = e
                logger.error(f"Ollama generation error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        # All retries failed
        if isinstance(last_error, httpx.TimeoutException):
            raise OllamaTimeoutError()
        raise OllamaError(f"Failed after {self.max_retries} attempts", last_error)

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from Ollama.

        Args:
            prompt: User prompt (should request JSON format)
            system_prompt: Optional system prompt
            schema: Optional JSON schema for validation
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters

        Returns:
            Parsed JSON response

        Raises:
            OllamaError: If generation fails or JSON is invalid

        Example:
            >>> result = await provider.generate_json(
            ...     prompt="Classify this document",
            ...     schema={"type": "object", "properties": {"type": {"type": "string"}}},
            ...     temperature=0.7
            ... )
        """
        logger.debug(f"Generating JSON with Ollama model '{self.model}'")

        # Enhance system prompt with JSON schema if provided
        enhanced_system = system_prompt or ""
        if schema:
            schema_str = json.dumps(schema, indent=2)
            enhanced_system += f"\n\nYou MUST respond with valid JSON matching this schema:\n{schema_str}"

        if not enhanced_system:
            enhanced_system = "You MUST respond with valid JSON only. No other text."

        # Build request payload with JSON format
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "system": enhanced_system,
            "stream": False,
            "format": "json",  # Ollama JSON mode
            "options": self._build_options(temperature, max_tokens, **kwargs),
        }

        # Attempt to generate and parse JSON
        max_json_retries = 2
        last_error: Optional[Exception] = None

        for attempt in range(max_json_retries):
            try:
                client = await self._get_client()
                logger.debug(f"Ollama JSON request (attempt {attempt + 1})")

                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()

                result = response.json()
                content = result.get("response", "").strip()

                logger.debug(f"Ollama JSON response: {content[:200]}")

                # Parse JSON
                try:
                    parsed = json.loads(content)
                    logger.debug("Successfully parsed JSON response")
                    return parsed

                except json.JSONDecodeError as e:
                    last_error = e
                    logger.warning(f"Failed to parse JSON (attempt {attempt + 1}): {e}")

                    # On first failure, retry with clarification
                    if attempt == 0:
                        payload["prompt"] = (
                            f"{prompt}\n\nIMPORTANT: Your previous response was not valid JSON. "
                            f"Please respond with ONLY valid JSON, no additional text or explanation."
                        )
                        continue

                    # Final attempt failed
                    raise OllamaError(
                        f"Failed to generate valid JSON. Response: {content[:200]}",
                        e
                    )

            except httpx.TimeoutException as e:
                raise OllamaTimeoutError() from e

            except httpx.ConnectError as e:
                raise OllamaConnectionError(self.base_url) from e

            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                if e.response.status_code == 404 or "not found" in error_detail.lower():
                    models = await self.list_models()
                    raise OllamaModelNotFoundError(self.model, models) from e
                raise OllamaError(f"Ollama HTTP error: {error_detail}", e) from e

            except OllamaError:
                raise  # Re-raise our custom errors

            except Exception as e:
                raise OllamaError(f"Unexpected error generating JSON: {str(e)}", e) from e

        # Should not reach here, but just in case
        raise OllamaError("Failed to generate valid JSON", last_error)

    async def list_models(self) -> List[str]:
        """
        List available Ollama models with caching.

        Returns:
            List of model names

        Raises:
            OllamaConnectionError: If cannot connect to Ollama
            OllamaError: If listing fails

        Example:
            >>> models = await provider.list_models()
            >>> print(models)
            ['llama3.2', 'mistral', 'codellama']
        """
        # Check cache
        if self._models_cache is not None and self._models_cache_time is not None:
            if datetime.now() - self._models_cache_time < timedelta(seconds=self._models_cache_ttl):
                logger.debug("Returning cached models list")
                return self._models_cache

        logger.debug("Fetching models from Ollama")

        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()

            result = response.json()
            models_data = result.get("models", [])

            # Extract model names
            model_names = [model.get("name", "") for model in models_data]
            model_names = [name for name in model_names if name]  # Filter empty

            # Update cache
            self._models_cache = model_names
            self._models_cache_time = datetime.now()

            logger.debug(f"Found {len(model_names)} Ollama models")
            return model_names

        except httpx.ConnectError as e:
            raise OllamaConnectionError(self.base_url) from e

        except Exception as e:
            raise OllamaError(f"Failed to list Ollama models: {str(e)}", e) from e

    async def health_check(self) -> bool:
        """
        Check if Ollama is accessible.

        Returns:
            True if Ollama is accessible, False otherwise

        Example:
            >>> is_healthy = await provider.health_check()
            >>> print(is_healthy)
            True
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.debug("Ollama client closed")

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama library.

        Note: This is a streaming endpoint and may take time for large models.

        Args:
            model_name: Name of model to pull (e.g., "llama3.2")

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = await provider.pull_model("llama3.2")
        """
        logger.info(f"Pulling Ollama model '{model_name}'")

        try:
            client = await self._get_client()

            # Use a longer timeout for pulling models
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(600.0)  # 10 minutes
            ) as pull_client:
                response = await pull_client.post(
                    "/api/pull",
                    json={"name": model_name, "stream": False}
                )
                response.raise_for_status()

                # Invalidate models cache
                self._models_cache = None

                logger.info(f"Successfully pulled model '{model_name}'")
                return True

        except Exception as e:
            logger.error(f"Failed to pull model '{model_name}': {e}")
            return False

    async def delete_model(self, model_name: str) -> bool:
        """
        Delete a model from local Ollama.

        Args:
            model_name: Name of model to delete

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = await provider.delete_model("old-model")
        """
        logger.info(f"Deleting Ollama model '{model_name}'")

        try:
            client = await self._get_client()
            response = await client.delete(
                "/api/delete",
                json={"name": model_name}
            )
            response.raise_for_status()

            # Invalidate models cache
            self._models_cache = None

            logger.info(f"Successfully deleted model '{model_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete model '{model_name}': {e}")
            return False


async def get_ollama_provider(
    base_url: str,
    model: str,
    timeout: int = 120,
    max_retries: int = 3,
) -> OllamaProvider:
    """
    Get an Ollama provider instance.

    Args:
        base_url: Ollama API base URL
        model: Default model to use
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        OllamaProvider instance
    """
    return OllamaProvider(
        base_url=base_url,
        model=model,
        timeout=timeout,
        max_retries=max_retries,
    )
