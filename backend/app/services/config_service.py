"""
Configuration service for managing runtime config overrides.

Handles reading and updating configuration stored in the database.
"""

from typing import Any, Dict, Optional
from uuid import UUID

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
            ValueError: If section is invalid
        """
        valid_sections = [
            "ai", "processing", "tagging", "naming", "learning",
            "approval_workflow", "auto_creation", "notifications"
        ]

        if section not in valid_sections:
            raise ValueError(f"Invalid config section: {section}")

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
