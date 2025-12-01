"""
Common Pydantic schemas shared across the application.
"""

from datetime import datetime
from typing import Annotated, Any, Callable, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer


# Generic types
T = TypeVar("T")


# Custom UTC datetime type with proper serialization for Pydantic v2
# This ensures all datetime fields are serialized with 'Z' suffix for UTC
UTCDatetime = Annotated[
    datetime,
    PlainSerializer(
        lambda dt: f"{dt.isoformat()}Z" if dt.tzinfo is None else dt.isoformat(),
        return_type=str,
    ),
]


# Base schema for models with from_attributes support
class UTCBaseModel(BaseModel):
    """
    Base Pydantic model for response schemas.

    Use UTCDatetime type annotation for datetime fields to ensure proper
    UTC serialization with 'Z' suffix.
    """

    model_config = ConfigDict(from_attributes=True)


# Common response schemas
class HealthCheckResponse(BaseModel):
    """Schema for health check endpoint."""

    status: str = "healthy"
    version: str = "1.0.0"
    database: bool = True
    ai_provider: bool = True
    paperless: Optional[bool] = None


class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# Pagination schemas
class PaginationParams(BaseModel):
    """Schema for pagination parameters."""

    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    order_by: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        limit: int,
        offset: int,
    ) -> "PaginatedResponse[T]":
        """
        Create a paginated response.

        Args:
            items: List of items
            total: Total count
            limit: Items per page
            offset: Offset from start

        Returns:
            PaginatedResponse instance
        """
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )


# File upload schemas
class FileUploadResponse(BaseModel):
    """Schema for file upload responses."""

    filename: str
    size: int
    content_type: str
    uploaded_at: str
