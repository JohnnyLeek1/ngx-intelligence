"""
Pydantic schemas for Approval-related API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models import ApprovalStatus
from app.schemas.common import UTCBaseModel, UTCDatetime


# Request schemas
class ApprovalActionRequest(BaseModel):
    """Schema for approval/rejection actions."""

    feedback: Optional[str] = Field(None, max_length=2000)


class BatchApprovalRequest(BaseModel):
    """Schema for batch approval actions."""

    approval_ids: List[UUID] = Field(..., min_length=1)
    feedback: Optional[str] = Field(None, max_length=2000)


# Response schemas
class ApprovalQueueResponse(UTCBaseModel):
    """Schema for approval queue item responses."""

    id: UUID
    document_id: UUID
    user_id: UUID
    suggestions: Dict[str, Any]
    created_at: UTCDatetime
    approved_at: Optional[UTCDatetime]
    feedback: Optional[str]
    status: ApprovalStatus

    model_config = {"from_attributes": True}


class ApprovalWithDocumentResponse(ApprovalQueueResponse):
    """Approval response with document details."""

    paperless_document_id: int
    original_data: Optional[Dict[str, Any]]
    confidence_score: Optional[float]


class ApprovalStatsResponse(BaseModel):
    """Schema for approval statistics."""

    pending: int
    approved: int
    rejected: int
    total: int
    approval_rate: float
