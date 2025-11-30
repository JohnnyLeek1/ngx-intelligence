"""
Configuration management for ngx-intelligence.

This module provides configuration loading from YAML files with environment
variable overrides and Pydantic validation.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application general settings."""

    name: str = Field(default="ngx-intelligence", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    secret_key: str = Field(..., description="Secret key for JWT signing")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"], description="CORS allowed origins"
    )


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    provider: Literal["sqlite", "postgresql"] = Field(
        default="sqlite", description="Database provider"
    )
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="ngx_intelligence.db", description="Database name")
    user: str = Field(default="", description="Database user")
    password: str = Field(default="", description="Database password")
    echo: bool = Field(default=False, description="Echo SQL statements")

    @property
    def url(self) -> str:
        """Generate database URL based on provider."""
        if self.provider == "sqlite":
            db_path = Path(self.name)
            if not db_path.is_absolute():
                db_path = Path("/app/data") / db_path
            return f"sqlite+aiosqlite:///{db_path}"
        elif self.provider == "postgresql":
            return (
                f"postgresql+asyncpg://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        raise ValueError(f"Unsupported database provider: {self.provider}")


class OllamaConfig(BaseSettings):
    """Ollama AI provider configuration."""

    base_url: str = Field(
        default="http://localhost:11434", description="Ollama API base URL"
    )
    model: str = Field(default="llama3.2", description="Default model to use")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    timeout: int = Field(default=120, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class AIConfig(BaseSettings):
    """AI configuration."""

    provider: Literal["ollama"] = Field(
        default="ollama", description="AI provider (currently only Ollama)"
    )
    model: str = Field(
        default="llama3.2", description="AI model to use"
    )
    ollama_url: Optional[str] = Field(
        default=None, description="Ollama API base URL (overrides ollama.base_url)"
    )
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


class PromptsConfig(BaseSettings):
    """AI prompts configuration."""

    system: str = Field(
        default=(
            "You are an AI assistant specialized in document classification "
            "and metadata extraction for document management systems. "
            "Analyze documents and provide structured metadata."
        ),
        description="Base system prompt",
    )
    classification: str = Field(
        default=(
            "Analyze this document and determine its type. "
            "Return a JSON object with: document_type, confidence"
        ),
        description="Document classification prompt",
    )
    tagging: str = Field(
        default=(
            "Suggest relevant tags for this document. "
            "Return a JSON object with: tags (array), confidences (array)"
        ),
        description="Document tagging prompt",
    )
    correspondent: str = Field(
        default=(
            "Identify the correspondent (sender/recipient) for this document. "
            "Return a JSON object with: correspondent, confidence"
        ),
        description="Correspondent identification prompt",
    )
    date_extraction: str = Field(
        default=(
            "Extract the most relevant date from this document. "
            "Return a JSON object with: document_date (YYYY-MM-DD), confidence"
        ),
        description="Date extraction prompt",
    )
    title_generation: str = Field(
        default=(
            "Generate a concise, descriptive title for this document (max 100 chars). "
            "Return a JSON object with: title, confidence"
        ),
        description="Title generation prompt",
    )


class BatchRulesConfig(BaseSettings):
    """Batch processing rules configuration."""

    document_threshold: int = Field(
        default=100, description="Process after N documents"
    )
    time_threshold: int = Field(
        default=3600, description="Process after N seconds"
    )
    rule_type: Literal["both", "either"] = Field(
        default="either", description="How to apply thresholds"
    )


class ProcessingConfig(BaseSettings):
    """Document processing configuration."""

    mode: Literal["realtime", "batch", "manual"] = Field(
        default="realtime", description="Processing mode"
    )
    polling_interval: int = Field(
        default=30, ge=5, description="Polling interval in seconds"
    )
    batch_schedule: str = Field(
        default="0 2 * * *", description="Cron schedule for batch processing"
    )
    batch_rules: BatchRulesConfig = Field(default_factory=BatchRulesConfig)
    concurrent_workers: int = Field(
        default=1, ge=1, le=10, description="Concurrent processing workers"
    )
    retry_attempts: int = Field(default=3, ge=1, description="Retry attempts")
    retry_backoff: int = Field(
        default=60, ge=1, description="Retry backoff in seconds"
    )


class ApprovalWorkflowConfig(BaseSettings):
    """Approval workflow configuration."""

    enabled: bool = Field(default=False, description="Enable approval workflow")
    pending_tag: str = Field(
        default="approval-pending", description="Tag for pending approvals"
    )


class AutoCreationConfig(BaseSettings):
    """Auto-creation settings for new entities."""

    document_types: bool = Field(
        default=False, description="Auto-create new document types"
    )
    tags: bool = Field(default=False, description="Auto-create new tags")
    correspondents: bool = Field(
        default=True, description="Auto-create new correspondents"
    )
    require_admin_approval: bool = Field(
        default=True, description="Require admin approval for auto-creation"
    )


class ProcessingTagConfig(BaseSettings):
    """Processing tag configuration."""

    enabled: bool = Field(
        default=True, description="Apply processing tag to documents"
    )
    name: str = Field(default="ai-processed", description="Processing tag name")


class TagRulesConfig(BaseSettings):
    """Tag application rules."""

    min_tags: int = Field(default=0, ge=0, description="Minimum tags per document")
    max_tags: int = Field(default=10, ge=1, description="Maximum tags per document")
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence for tag application"
    )
    prefix: str = Field(default="", description="Prefix for auto-generated tags")
    excluded_tags: List[str] = Field(
        default_factory=list, description="Tags that should never be auto-applied"
    )


class TaggingConfig(BaseSettings):
    """Tagging configuration."""

    processing_tag: ProcessingTagConfig = Field(default_factory=ProcessingTagConfig)
    rules: TagRulesConfig = Field(default_factory=TagRulesConfig)


class NamingConfig(BaseSettings):
    """Document naming configuration."""

    default_template: str = Field(
        default="{date}_{correspondent}_{type}_{title}",
        description="Default naming template",
    )
    date_format: str = Field(default="YYYY-MM-DD", description="Date format")
    max_title_length: int = Field(
        default=100, ge=10, description="Maximum title length"
    )
    clean_special_chars: bool = Field(
        default=True, description="Clean special characters from filenames"
    )


class LearningConfig(BaseSettings):
    """Learning and improvement configuration."""

    enabled: bool = Field(default=True, description="Enable learning system")
    global_learning: bool = Field(default=True, description="Enable global learning")
    per_user: bool = Field(default=True, description="Enable per-user learning")
    pattern_analysis: bool = Field(
        default=False, description="Enable pattern analysis"
    )
    example_library_size: int = Field(
        default=100, ge=1, description="Maximum examples per user"
    )


class WebhookConfig(BaseSettings):
    """Webhook notification configuration."""

    enabled: bool = Field(default=False, description="Enable webhooks")
    url: str = Field(default="", description="Webhook URL")
    events: List[str] = Field(
        default_factory=lambda: ["error", "processing_complete"],
        description="Events to send",
    )
    secret: str = Field(default="", description="HMAC secret for signatures")
    timeout: int = Field(default=30, description="Webhook timeout in seconds")


class NotificationsConfig(BaseSettings):
    """Notifications configuration."""

    webhook: WebhookConfig = Field(default_factory=WebhookConfig)


class JWTConfig(BaseSettings):
    """JWT authentication configuration."""

    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=15, description="Access token expiration"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration"
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="NGX_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    approval_workflow: ApprovalWorkflowConfig = Field(
        default_factory=ApprovalWorkflowConfig
    )
    auto_creation: AutoCreationConfig = Field(default_factory=AutoCreationConfig)
    tagging: TaggingConfig = Field(default_factory=TaggingConfig)
    naming: NamingConfig = Field(default_factory=NamingConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)

    @classmethod
    def from_yaml(cls, config_path: Path) -> "Settings":
        """
        Load settings from YAML file with environment variable overrides.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Settings instance with loaded configuration
        """
        if config_path.exists():
            with open(config_path, "r") as f:
                yaml_data = yaml.safe_load(f) or {}
        else:
            yaml_data = {}

        # Environment variables will override YAML values via Pydantic
        return cls(**yaml_data)

    def to_yaml(self, output_path: Path) -> None:
        """
        Export settings to YAML file.

        Args:
            output_path: Path where to save configuration
        """
        data = self.model_dump(mode="json", exclude_none=True)
        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        config_path = Path(os.getenv("CONFIG_PATH", "/app/config/config.yaml"))
        _settings = Settings.from_yaml(config_path)
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from configuration file.

    Returns:
        New Settings instance
    """
    global _settings
    config_path = Path(os.getenv("CONFIG_PATH", "/app/config/config.yaml"))
    _settings = Settings.from_yaml(config_path)
    return _settings
