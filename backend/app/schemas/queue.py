"""
Pydantic schemas for Queue-related API operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models import QueueStatus
from app.schemas.common import UTCBaseModel, UTCDatetime


# Request schemas
class QueueAddRequest(BaseModel):
    """Schema for adding documents to queue."""

    paperless_document_ids: List[int] = Field(..., min_length=1)
    priority: int = Field(default=0, ge=0, le=100)


class QueueClearRequest(BaseModel):
    """Schema for clearing queue items."""

    status: Optional[QueueStatus] = None
    older_than_days: Optional[int] = Field(None, ge=1)


# Response schemas
class QueueItemResponse(UTCBaseModel):
    """Schema for queue item responses."""

    id: UUID
    user_id: UUID
    paperless_document_id: int
    priority: int
    status: QueueStatus
    queued_at: UTCDatetime
    started_at: Optional[UTCDatetime]
    completed_at: Optional[UTCDatetime]
    retry_count: int
    last_error: Optional[str]

    model_config = {"from_attributes": True}


class QueueStatsResponse(BaseModel):
    """Schema for queue statistics."""

    queued: int
    processing: int
    completed: int
    failed: int
    total: int
    estimated_time_remaining: Optional[int] = None  # in seconds


class QueueStatusResponse(BaseModel):
    """Schema for overall queue status."""

    stats: QueueStatsResponse
    current_items: List[QueueItemResponse]
    is_paused: bool = False
    processing_mode: str = "realtime"
