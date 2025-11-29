"""
Pydantic schemas for User-related API operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.database.models import UserRole


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    paperless_url: str = Field(..., min_length=1, max_length=255)
    paperless_username: str = Field(..., min_length=1, max_length=255)

    @field_validator("paperless_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL doesn't have trailing slash."""
        return v.rstrip("/")


# Request schemas
class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, max_length=255)
    paperless_token: str = Field(..., min_length=1, max_length=255)
    role: UserRole = Field(default=UserRole.USER)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""

    email: Optional[EmailStr] = None
    paperless_url: Optional[str] = None
    paperless_username: Optional[str] = None
    paperless_token: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=255)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# Response schemas
class UserResponse(UserBase):
    """Schema for user responses."""

    id: UUID
    role: UserRole
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class UserWithStats(UserResponse):
    """User response with processing statistics."""

    total_documents: int = 0
    success_rate: float = 0.0


# Authentication schemas
class LoginRequest(BaseModel):
    """Schema for login requests."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token responses."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh requests."""

    refresh_token: str


# Paperless validation
class PaperlessValidationRequest(BaseModel):
    """Schema for validating Paperless credentials."""

    paperless_url: str
    paperless_username: str
    paperless_token: str


class PaperlessValidationResponse(BaseModel):
    """Schema for Paperless validation response."""

    is_valid: bool
    message: str
    user_info: Optional[dict] = None
