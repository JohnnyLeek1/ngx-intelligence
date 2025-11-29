"""
Unit tests for Pydantic schema validation.

Tests schema validation, serialization, and custom validators.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    UserPasswordChange,
)
from app.schemas.document import DocumentResponse, DocumentUpdate
from app.schemas.queue import QueueStatusResponse
from app.database.models import UserRole


class TestUserSchemas:
    """Test user-related schemas."""

    def test_user_create_valid(self):
        """Test valid user creation schema."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "paperless_url": "http://paperless.local",
            "paperless_username": "testuser",
            "paperless_token": "token123",
        }

        user = UserCreate(**user_data)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"

    def test_user_create_password_validation_too_short(self):
        """Test password must be at least 8 characters."""
        user_data = {
            "username": "testuser",
            "password": "Short1!",
            "paperless_url": "http://paperless.local",
            "paperless_username": "testuser",
            "paperless_token": "token123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        assert "Password must be at least 8 characters" in str(exc_info.value)

    def test_user_create_password_needs_uppercase(self):
        """Test password must contain uppercase letter."""
        user_data = {
            "username": "testuser",
            "password": "lowercase123!",
            "paperless_url": "http://paperless.local",
            "paperless_username": "testuser",
            "paperless_token": "token123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        assert "uppercase" in str(exc_info.value).lower()

    def test_user_create_paperless_url_trailing_slash(self):
        """Test that trailing slash is removed from Paperless URL."""
        user_data = {
            "username": "testuser",
            "password": "SecurePass123!",
            "paperless_url": "http://paperless.local/",
            "paperless_username": "testuser",
            "paperless_token": "token123",
        }

        user = UserCreate(**user_data)

        assert user.paperless_url == "http://paperless.local"
