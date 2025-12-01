"""
Daily Metrics API endpoints.

Handles daily metrics retrieval and comparison.
"""

from datetime import date, datetime, timedelta
from typing import Optional

import pytz
from fastapi import APIRouter, Depends

from app.database.models import User
from app.dependencies import get_current_user, get_metrics_repository
from app.repositories import DailyMetricsRepository
from app.schemas import (
    DailyMetricsComparisonResponse,
    DailyMetricsResponse,
    MetricsRangeRequest,
    MetricsRangeResponse,
)


router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/daily", response_model=DailyMetricsComparisonResponse)
async def get_daily_metrics(
    current_user: User = Depends(get_current_user),
    metrics_repo: DailyMetricsRepository = Depends(get_metrics_repository),
) -> DailyMetricsComparisonResponse:
    """
    Get today's and yesterday's metrics with comparison.

    This endpoint calculates metrics on-demand for today and yesterday,
    providing both the raw metrics and calculated comparison values.
    The "day" boundaries are determined by the user's timezone preference.

    Returns:
        DailyMetricsComparisonResponse with today's metrics, yesterday's metrics,
        and comparison values (changes in documents, confidence, processing time)
    """
    # Get user's timezone
    user_tz = pytz.timezone(current_user.timezone)

    # Calculate "today" and "yesterday" in user's timezone
    now_in_user_tz = datetime.now(user_tz)
    today_local = now_in_user_tz.date()
    yesterday_local = today_local - timedelta(days=1)

    # Calculate metrics for today using user's timezone
    today_metrics = await metrics_repo.calculate_and_update_metrics(
        user_id=current_user.id,
        target_date=today_local,
        user_timezone=current_user.timezone,
    )

    # Calculate metrics for yesterday using user's timezone
    yesterday_metrics = await metrics_repo.calculate_and_update_metrics(
        user_id=current_user.id,
        target_date=yesterday_local,
        user_timezone=current_user.timezone,
    )

    # Convert to response models
    today_response: Optional[DailyMetricsResponse] = None
    yesterday_response: Optional[DailyMetricsResponse] = None

    if today_metrics and today_metrics.total_documents > 0:
        today_response = DailyMetricsResponse.model_validate(today_metrics)

    if yesterday_metrics and yesterday_metrics.total_documents > 0:
        yesterday_response = DailyMetricsResponse.model_validate(yesterday_metrics)

    # Calculate comparison values
    documents_change: Optional[int] = None
    documents_change_percent: Optional[float] = None
    confidence_change: Optional[float] = None
    processing_time_change: Optional[float] = None

    if today_response and yesterday_response:
        # Calculate document changes
        documents_change = today_metrics.total_documents - yesterday_metrics.total_documents

        if yesterday_metrics.total_documents > 0:
            documents_change_percent = (
                (documents_change / yesterday_metrics.total_documents) * 100
            )

        # Calculate confidence change
        if (
            today_metrics.avg_confidence_score is not None
            and yesterday_metrics.avg_confidence_score is not None
        ):
            confidence_change = (
                today_metrics.avg_confidence_score - yesterday_metrics.avg_confidence_score
            )

        # Calculate processing time change
        if (
            today_metrics.avg_processing_time_ms is not None
            and yesterday_metrics.avg_processing_time_ms is not None
        ):
            processing_time_change = (
                today_metrics.avg_processing_time_ms - yesterday_metrics.avg_processing_time_ms
            )

    return DailyMetricsComparisonResponse(
        today=today_response,
        yesterday=yesterday_response,
        documents_change=documents_change,
        documents_change_percent=documents_change_percent,
        confidence_change=confidence_change,
        processing_time_change=processing_time_change,
    )


@router.post("/range", response_model=MetricsRangeResponse)
async def get_metrics_range(
    request: MetricsRangeRequest,
    current_user: User = Depends(get_current_user),
    metrics_repo: DailyMetricsRepository = Depends(get_metrics_repository),
) -> MetricsRangeResponse:
    """
    Get metrics for a date range.

    Calculate and return daily metrics for each day in the specified range.
    Useful for generating charts and trends over time.
    The "day" boundaries are determined by the user's timezone preference.

    Args:
        request: MetricsRangeRequest with start_date and end_date

    Returns:
        MetricsRangeResponse with list of daily metrics ordered by date
    """
    # Validate date range
    if request.end_date < request.start_date:
        # Swap them if provided in wrong order
        request.start_date, request.end_date = request.end_date, request.start_date

    # Calculate total days
    total_days = (request.end_date - request.start_date).days + 1

    # Calculate metrics for each day in the range
    current_date = request.start_date
    all_metrics = []

    while current_date <= request.end_date:
        metrics = await metrics_repo.calculate_and_update_metrics(
            user_id=current_user.id,
            target_date=current_date,
            user_timezone=current_user.timezone,
        )

        # Only include days with data
        if metrics and metrics.total_documents > 0:
            all_metrics.append(DailyMetricsResponse.model_validate(metrics))

        current_date += timedelta(days=1)

    return MetricsRangeResponse(
        metrics=all_metrics,
        total_days=total_days,
    )


@router.get("/daily/{target_date}", response_model=Optional[DailyMetricsResponse])
async def get_metrics_for_date(
    target_date: date,
    current_user: User = Depends(get_current_user),
    metrics_repo: DailyMetricsRepository = Depends(get_metrics_repository),
) -> Optional[DailyMetricsResponse]:
    """
    Get metrics for a specific date.

    The "day" boundaries are determined by the user's timezone preference.

    Args:
        target_date: Date to get metrics for (YYYY-MM-DD format)

    Returns:
        DailyMetricsResponse if data exists for that date, None otherwise
    """
    # Calculate and update metrics for the target date using user's timezone
    metrics = await metrics_repo.calculate_and_update_metrics(
        user_id=current_user.id,
        target_date=target_date,
        user_timezone=current_user.timezone,
    )

    if metrics and metrics.total_documents > 0:
        return DailyMetricsResponse.model_validate(metrics)

    return None
