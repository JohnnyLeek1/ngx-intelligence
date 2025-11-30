"""
Configuration service for managing runtime config overrides.

Handles reading and updating configuration stored in the database.
"""

from typing import Any, Dict, Optional
from uuid import UUID
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.logging import get_logger
from app.database.models import Setting

logger = get_logger(__name__)


class ConfigService:
    """Service for managing configuration overrides."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._base_settings = get_settings()

    async def get_full_config(self) -> Dict[str, Any]:
        """
        Get full configuration with database overrides applied.

        Returns:
            Complete configuration dictionary
        """
        # Start with base settings from YAML/env
        config = self._base_settings.model_dump(
            mode="json",
            exclude={"app": {"secret_key"}}
        )

        # Apply database overrides for each section
        for section in ["ai", "processing", "tagging", "naming", "learning",
                        "approval_workflow", "auto_creation", "notifications"]:
            overrides = await self._get_section_overrides(section)
            if overrides:
                config[section].update(overrides)

        return config

    async def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a specific configuration section with overrides.

        Args:
            section: Section name (e.g., 'ai', 'processing')

        Returns:
            Configuration section data
        """
        # Get base config for section
        config = self._base_settings.model_dump(mode="json")
        base_data = config.get(section, {})

        # Apply database overrides
        overrides = await self._get_section_overrides(section)
        if overrides:
            base_data.update(overrides)

        return base_data

    def _validate_ai_config(self, data: Dict[str, Any]) -> None:
        """
        Validate AI configuration data.

        Args:
            data: AI configuration data to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate ollama_url if present
        if "ollama_url" in data and data["ollama_url"]:
            url = data["ollama_url"]
            parsed = urlparse(url)

            # Check for valid scheme
            if parsed.scheme not in ("http", "https"):
                raise ValueError(
                    f"Invalid ollama_url scheme: {parsed.scheme}. "
                    "Must be http or https"
                )

            # Check for valid netloc (hostname:port)
            if not parsed.netloc:
                raise ValueError(
                    f"Invalid ollama_url: {url}. "
                    "Must include hostname (e.g., http://localhost:11434)"
                )

            logger.info(f"Validated ollama_url: {url}")

    async def test_ollama_connection(self, ollama_url: str) -> Dict[str, Any]:
        """
        Test connectivity to an Ollama instance.

        Args:
            ollama_url: Ollama base URL to test

        Returns:
            Dictionary with test results including:
                - reachable (bool): Whether the URL is reachable
                - error (str|None): Error message if unreachable
                - models (list|None): Available models if reachable

        Example:
            >>> result = await config_service.test_ollama_connection("http://localhost:11434")
            >>> if result["reachable"]:
            ...     print(f"Available models: {result['models']}")
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{ollama_url.rstrip('/')}/api/tags")
                response.raise_for_status()

                result = response.json()
                models = [m.get("name", "") for m in result.get("models", [])]

                logger.info(
                    f"Successfully connected to Ollama at {ollama_url}, "
                    f"found {len(models)} models"
                )

                return {
                    "reachable": True,
                    "error": None,
                    "models": models,
                }
        except httpx.ConnectError as e:
            logger.warning(f"Cannot connect to Ollama at {ollama_url}: {e}")
            return {
                "reachable": False,
                "error": f"Cannot connect to {ollama_url}. Ensure Ollama is running.",
                "models": None,
            }
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout connecting to Ollama at {ollama_url}: {e}")
            return {
                "reachable": False,
                "error": f"Connection to {ollama_url} timed out.",
                "models": None,
            }
        except Exception as e:
            logger.error(f"Error testing Ollama connection at {ollama_url}: {e}")
            return {
                "reachable": False,
                "error": f"Error: {str(e)}",
                "models": None,
            }

    async def _validate_section_data(
        self, section: str, data: Dict[str, Any]
    ) -> None:
        """
        Validate configuration data for a specific section.

        Args:
            section: Section name
            data: Configuration data to validate

        Raises:
            ValueError: If validation fails
        """
        if section == "ai":
            self._validate_ai_config(data)
        # Add more section-specific validation as needed

    async def update_section(
        self,
        section: str,
        data: Dict[str, Any],
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Update a configuration section.

        Args:
            section: Section name
            data: New configuration data
            user_id: ID of user making the update

        Returns:
            Updated configuration section

        Raises:
            ValueError: If section is invalid or validation fails
        """
        valid_sections = [
            "ai", "processing", "tagging", "naming", "learning",
            "approval_workflow", "auto_creation", "notifications"
        ]

        if section not in valid_sections:
            raise ValueError(f"Invalid config section: {section}")

        # Validate the data before storing
        await self._validate_section_data(section, data)

        # Store as database override
        key = f"config.{section}"

        # Check if setting exists
        stmt = select(Setting).where(Setting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            # Update existing
            setting.value = data
            setting.updated_by = user_id
        else:
            # Create new
            setting = Setting(
                key=key,
                value=data,
                updated_by=user_id
            )
            self.db.add(setting)

        await self.db.commit()
        await self.db.refresh(setting)

        logger.info(f"Config section '{section}' updated by user {user_id}")

        # Return the full section with overrides applied
        return await self.get_section(section)

    async def _get_section_overrides(self, section: str) -> Optional[Dict[str, Any]]:
        """
        Get database overrides for a config section.

        Args:
            section: Section name

        Returns:
            Override data if exists, None otherwise
        """
        key = f"config.{section}"
        stmt = select(Setting).where(Setting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        return setting.value if setting else None

    async def reset_section(self, section: str) -> Dict[str, Any]:
        """
        Reset a config section to defaults.

        Args:
            section: Section name

        Returns:
            Default configuration section
        """
        key = f"config.{section}"
        stmt = select(Setting).where(Setting.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            await self.db.delete(setting)
            await self.db.commit()
            logger.info(f"Config section '{section}' reset to defaults")

        # Return base config for section
        config = self._base_settings.model_dump(mode="json")
        return config.get(section, {})
