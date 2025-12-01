"""
Pydantic schemas for Daily Metrics API operations.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UTCBaseModel, UTCDatetime


class DailyMetricsResponse(UTCBaseModel):
    """Schema for daily metrics response."""

    id: UUID
    user_id: UUID
    date: datetime
    total_documents: int = Field(..., ge=0)
    successful_documents: int = Field(..., ge=0)
    failed_documents: int = Field(..., ge=0)
    avg_confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    avg_processing_time_ms: Optional[float] = Field(None, ge=0.0)
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = {"from_attributes": True}


class DailyMetricsComparisonResponse(BaseModel):
    """Schema for comparing daily metrics (today vs yesterday)."""

    today: Optional[DailyMetricsResponse] = Field(
        None, description="Today's metrics, None if no data"
    )
    yesterday: Optional[DailyMetricsResponse] = Field(
        None, description="Yesterday's metrics, None if no data"
    )

    # Calculated comparison fields
    documents_change: Optional[int] = Field(
        None, description="Change in total documents (today - yesterday)"
    )
    documents_change_percent: Optional[float] = Field(
        None, description="Percentage change in total documents"
    )
    confidence_change: Optional[float] = Field(
        None, description="Change in average confidence score"
    )
    processing_time_change: Optional[float] = Field(
        None, description="Change in average processing time (ms)"
    )


class MetricsRangeRequest(BaseModel):
    """Schema for requesting metrics over a date range."""

    start_date: date = Field(..., description="Start date for metrics range")
    end_date: date = Field(..., description="End date for metrics range")


class MetricsRangeResponse(BaseModel):
    """Schema for metrics range response."""

    metrics: list[DailyMetricsResponse] = Field(
        default_factory=list, description="List of daily metrics ordered by date"
    )
    total_days: int = Field(..., ge=0, description="Total number of days in range")
