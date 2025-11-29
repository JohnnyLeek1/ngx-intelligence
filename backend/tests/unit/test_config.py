"""
Unit tests for configuration management.

Tests configuration loading, validation, and defaults.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from app.config import (
    AppConfig,
    DatabaseConfig,
    JWTConfig,
    OllamaConfig,
    ProcessingConfig,
    Settings,
)


class TestDefaultSettings:
    """Test default configuration values."""

    def test_default_settings_initialization(self):
        """Test that settings can be initialized with defaults."""
        settings = Settings(app={"secret_key": "test-secret"})

        assert settings.app.name == "ngx-intelligence"
        assert settings.app.debug is False
        assert settings.app.log_level == "INFO"
        assert settings.database.provider in ["sqlite", "postgresql"]

    def test_app_config_defaults(self):
        """Test AppConfig default values."""
        config = AppConfig(secret_key="test-key")

        assert config.name == "ngx-intelligence"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.allowed_origins == ["http://localhost:3000"]

    def test_database_config_defaults(self):
        """Test DatabaseConfig default values."""
        config = DatabaseConfig()

        assert config.provider == "sqlite"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.echo is False

    def test_jwt_config_defaults(self):
        """Test JWTConfig default values."""
        config = JWTConfig()

        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 15
        assert config.refresh_token_expire_days == 7

    def test_processing_config_defaults(self):
        """Test ProcessingConfig default values."""
        config = ProcessingConfig()

        assert config.mode == "realtime"
        assert config.polling_interval == 30
        assert config.concurrent_workers == 1
        assert config.retry_attempts == 3


class TestDatabaseConfiguration:
    """Test database configuration and URL generation."""

    def test_sqlite_database_url(self):
        """Test SQLite database URL generation."""
        settings = Settings(
            app={"secret_key": "test"}, database={"provider": "sqlite", "name": "test.db"}
        )
        url = settings.database.url

        assert "sqlite+aiosqlite" in url
        assert "test.db" in url

    def test_sqlite_memory_database_url(self):
        """Test SQLite in-memory database URL."""
        settings = Settings(
            app={"secret_key": "test"},
            database={"provider": "sqlite", "name": ":memory:"},
        )
        url = settings.database.url

        assert "sqlite+aiosqlite:///:memory:" in url

    def test_postgresql_database_url(self):
        """Test PostgreSQL database URL generation."""
        settings = Settings(
            app={"secret_key": "test"},
            database={
                "provider": "postgresql",
                "host": "localhost",
                "port": 5432,
                "name": "testdb",
                "user": "testuser",
                "password": "testpass",
            },
        )
        url = settings.database.url

        assert "postgresql+asyncpg" in url
        assert "testuser:testpass" in url
        assert "localhost:5432" in url
        assert "testdb" in url

    def test_postgresql_custom_port(self):
        """Test PostgreSQL with custom port."""
        settings = Settings(
            app={"secret_key": "test"},
            database={
                "provider": "postgresql",
                "host": "db.example.com",
                "port": 5433,
                "name": "mydb",
                "user": "admin",
                "password": "secret",
            },
        )
        url = settings.database.url

        assert "db.example.com:5433" in url

    def test_invalid_database_provider(self):
        """Test that invalid provider raises error."""
        with pytest.raises(ValueError):
            settings = Settings(
                app={"secret_key": "test"}, database={"provider": "mysql"}
            )


class TestAIConfiguration:
    """Test AI and Ollama configuration."""

    def test_ollama_config_defaults(self):
        """Test Ollama configuration defaults."""
        settings = Settings(app={"secret_key": "test"})

        assert settings.ai.provider == "ollama"
        assert settings.ai.ollama.base_url == "http://localhost:11434"
        assert settings.ai.ollama.model == "llama3.2"
        assert 0.0 <= settings.ai.ollama.temperature <= 2.0

    def test_ollama_custom_config(self):
        """Test custom Ollama configuration."""
        settings = Settings(
            app={"secret_key": "test"},
            ai={
                "ollama": {
                    "base_url": "http://custom:8080",
                    "model": "mixtral",
                    "temperature": 0.5,
                    "timeout": 60,
                }
            },
        )

        assert settings.ai.ollama.base_url == "http://custom:8080"
        assert settings.ai.ollama.model == "mixtral"
        assert settings.ai.ollama.temperature == 0.5
        assert settings.ai.ollama.timeout == 60

    def test_ollama_temperature_validation(self):
        """Test Ollama temperature bounds validation."""
        # Valid temperature
        config = OllamaConfig(temperature=0.7)
        assert config.temperature == 0.7

        # Temperature at upper bound
        config = OllamaConfig(temperature=2.0)
        assert config.temperature == 2.0

        # Temperature at lower bound
        config = OllamaConfig(temperature=0.0)
        assert config.temperature == 0.0


class TestProcessingConfiguration:
    """Test processing configuration."""

    def test_processing_mode_options(self):
        """Test valid processing mode options."""
        valid_modes = ["realtime", "batch", "manual"]

        for mode in valid_modes:
            settings = Settings(
                app={"secret_key": "test"}, processing={"mode": mode}
            )
            assert settings.processing.mode == mode

    def test_concurrent_workers_bounds(self):
        """Test concurrent workers validation."""
        # Minimum workers
        config = ProcessingConfig(concurrent_workers=1)
        assert config.concurrent_workers == 1

        # Maximum workers
        config = ProcessingConfig(concurrent_workers=10)
        assert config.concurrent_workers == 10

    def test_polling_interval_minimum(self):
        """Test polling interval minimum validation."""
        config = ProcessingConfig(polling_interval=5)
        assert config.polling_interval == 5

    def test_batch_rules_config(self):
        """Test batch processing rules configuration."""
        settings = Settings(
            app={"secret_key": "test"},
            processing={
                "batch_rules": {
                    "document_threshold": 50,
                    "time_threshold": 1800,
                    "rule_type": "both",
                }
            },
        )

        assert settings.processing.batch_rules.document_threshold == 50
        assert settings.processing.batch_rules.time_threshold == 1800
        assert settings.processing.batch_rules.rule_type == "both"


class TestYAMLConfiguration:
    """Test YAML configuration loading."""

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "app": {"name": "test-app", "debug": True, "secret_key": "yaml-secret"},
            "database": {"provider": "sqlite", "name": "test.db"},
            "ai": {"ollama": {"model": "llama3"}},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            settings = Settings.from_yaml(temp_path)

            assert settings.app.name == "test-app"
            assert settings.app.debug is True
            assert settings.database.provider == "sqlite"
            assert settings.ai.ollama.model == "llama3"
        finally:
            temp_path.unlink()

    def test_load_from_nonexistent_yaml(self):
        """Test loading from nonexistent YAML file returns defaults."""
        nonexistent_path = Path("/tmp/nonexistent_config_file.yaml")

        # Should not raise, just use defaults
        settings = Settings.from_yaml(nonexistent_path)

        assert settings.app.name == "ngx-intelligence"

    def test_export_to_yaml(self):
        """Test exporting configuration to YAML file."""
        settings = Settings(
            app={"name": "export-test", "secret_key": "test", "debug": True},
            database={"provider": "sqlite", "name": "export.db"},
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            settings.to_yaml(temp_path)

            # Read back and verify
            with open(temp_path, "r") as f:
                data = yaml.safe_load(f)

            assert data["app"]["name"] == "export-test"
            assert data["app"]["debug"] is True
            assert data["database"]["provider"] == "sqlite"
        finally:
            temp_path.unlink()


class TestConfigurationValidation:
    """Test configuration validation rules."""

    def test_secret_key_required(self):
        """Test that secret key is required for AppConfig."""
        with pytest.raises(ValueError):
            AppConfig()

    def test_log_level_validation(self):
        """Test log level must be valid value."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = AppConfig(secret_key="test", log_level=level)
            assert config.log_level == level

    def test_paperless_url_trailing_slash_removal(self):
        """Test URL normalization in user base schema."""
        from app.schemas.user import UserBase

        user = UserBase(
            username="test",
            paperless_url="http://example.com/",
            paperless_username="user",
        )

        assert user.paperless_url == "http://example.com"

    def test_confidence_threshold_bounds(self):
        """Test confidence threshold validation."""
        settings = Settings(
            app={"secret_key": "test"},
            tagging={"rules": {"confidence_threshold": 0.8}},
        )

        assert settings.tagging.rules.confidence_threshold == 0.8

    def test_tag_rules_min_max_validation(self):
        """Test tag rules min/max validation."""
        settings = Settings(
            app={"secret_key": "test"},
            tagging={"rules": {"min_tags": 1, "max_tags": 5}},
        )

        assert settings.tagging.rules.min_tags == 1
        assert settings.tagging.rules.max_tags == 5


class TestNestedConfiguration:
    """Test nested configuration structures."""

    def test_approval_workflow_config(self):
        """Test approval workflow configuration."""
        settings = Settings(
            app={"secret_key": "test"},
            approval_workflow={"enabled": True, "pending_tag": "needs-approval"},
        )

        assert settings.approval_workflow.enabled is True
        assert settings.approval_workflow.pending_tag == "needs-approval"

    def test_auto_creation_config(self):
        """Test auto-creation configuration."""
        settings = Settings(
            app={"secret_key": "test"},
            auto_creation={
                "document_types": True,
                "tags": True,
                "correspondents": False,
            },
        )

        assert settings.auto_creation.document_types is True
        assert settings.auto_creation.tags is True
        assert settings.auto_creation.correspondents is False

    def test_webhook_notification_config(self):
        """Test webhook notification configuration."""
        settings = Settings(
            app={"secret_key": "test"},
            notifications={
                "webhook": {
                    "enabled": True,
                    "url": "https://hooks.example.com/webhook",
                    "events": ["error", "success"],
                    "secret": "webhook-secret",
                }
            },
        )

        assert settings.notifications.webhook.enabled is True
        assert settings.notifications.webhook.url == "https://hooks.example.com/webhook"
        assert "error" in settings.notifications.webhook.events
        assert "success" in settings.notifications.webhook.events
