"""
Pydantic schemas for Document-related API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models import ProcessingStatus
from app.schemas.common import UTCBaseModel, UTCDatetime


# Base schemas
class DocumentBase(BaseModel):
    """Base document schema."""

    paperless_document_id: int = Field(..., gt=0)


# Request schemas
class DocumentReprocessRequest(BaseModel):
    """Schema for document reprocessing request."""

    document_ids: List[int] = Field(..., min_length=1)
    force: bool = Field(default=False, description="Force reprocess even if recently processed")


class DocumentFilterRequest(BaseModel):
    """Schema for document filtering."""

    status: Optional[ProcessingStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# Processing result schemas
class ProcessingResult(BaseModel):
    """Schema for AI processing results."""

    correspondent: Optional[str] = None
    correspondent_confidence: Optional[float] = None
    document_type: Optional[str] = None
    document_type_confidence: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    tag_confidences: List[float] = Field(default_factory=list)
    document_date: Optional[str] = None
    date_confidence: Optional[float] = None
    title: Optional[str] = None
    title_confidence: Optional[float] = None
    overall_confidence: float = Field(..., ge=0.0, le=1.0)


# Response schemas
class ProcessedDocumentResponse(UTCBaseModel):
    """Schema for processed document responses."""

    id: UUID
    user_id: UUID
    paperless_document_id: int
    processed_at: UTCDatetime
    status: ProcessingStatus
    confidence_score: Optional[float]
    original_data: Optional[Dict[str, Any]]
    suggested_data: Optional[Dict[str, Any]]
    applied_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    processing_time_ms: Optional[int]
    reprocess_count: int

    model_config = {"from_attributes": True}


class ProcessedDocumentDetail(ProcessedDocumentResponse):
    """Detailed document response with additional information."""

    can_reprocess: bool = True
    paperless_url: Optional[str] = None


class DocumentStatsResponse(BaseModel):
    """Schema for document processing statistics."""

    total: int
    success: int
    failed: int
    pending_approval: int
    success_rate: float
    avg_processing_time_ms: Optional[float] = None
    avg_confidence: Optional[float] = None


class RecentDocumentsResponse(BaseModel):
    """Schema for recent documents list."""

    documents: List[ProcessedDocumentResponse]
    total: int
    has_more: bool
