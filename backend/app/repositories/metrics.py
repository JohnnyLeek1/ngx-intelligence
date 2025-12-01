"""
Daily metrics repository for aggregated statistics.
"""

from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import UUID

import pytz
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DailyMetrics, ProcessedDocument, ProcessingStatus
from app.repositories.base import SQLAlchemyRepository


class DailyMetricsRepository(SQLAlchemyRepository[DailyMetrics]):
    """Repository for DailyMetrics model operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DailyMetrics, session)

    async def get_or_create_for_date(
        self, user_id: UUID, target_date: date
    ) -> DailyMetrics:
        """
        Get or create daily metrics entry for a specific date.

        Args:
            user_id: User UUID
            target_date: Date for metrics

        Returns:
            DailyMetrics instance
        """
        # Convert date to datetime at midnight for comparison
        date_start = datetime.combine(target_date, datetime.min.time())

        result = await self.session.execute(
            select(DailyMetrics).where(
                and_(
                    DailyMetrics.user_id == user_id,
                    DailyMetrics.date == date_start,
                )
            )
        )
        metrics = result.scalar_one_or_none()

        if metrics is None:
            metrics = DailyMetrics(
                user_id=user_id,
                date=date_start,
                total_documents=0,
                successful_documents=0,
                failed_documents=0,
            )
            self.session.add(metrics)
            await self.session.commit()
            await self.session.refresh(metrics)

        return metrics

    async def calculate_and_update_metrics(
        self, user_id: UUID, target_date: date, user_timezone: str = "UTC"
    ) -> DailyMetrics:
        """
        Calculate and update daily metrics for a specific date.

        Aggregates all document processing data for the given date using the user's timezone
        to determine the boundaries of the day.

        Args:
            user_id: User UUID
            target_date: Date to calculate metrics for (in user's timezone)
            user_timezone: IANA timezone name (e.g., "America/Los_Angeles", "UTC")

        Returns:
            Updated DailyMetrics instance
        """
        # Get or create the metrics entry
        metrics = await self.get_or_create_for_date(user_id, target_date)

        # Get user's timezone object
        user_tz = pytz.timezone(user_timezone)

        # Define date range for the day in user's timezone
        # Get midnight-to-midnight in user's timezone
        local_start = user_tz.localize(datetime.combine(target_date, time.min))
        local_end = user_tz.localize(datetime.combine(target_date + timedelta(days=1), time.min))

        # Convert to UTC for querying (database stores timestamps in UTC)
        date_start_utc = local_start.astimezone(pytz.UTC)
        date_end_utc = local_end.astimezone(pytz.UTC)

        # Query all documents processed during this date in user's timezone
        result = await self.session.execute(
            select(ProcessedDocument).where(
                and_(
                    ProcessedDocument.user_id == user_id,
                    ProcessedDocument.processed_at >= date_start_utc,
                    ProcessedDocument.processed_at < date_end_utc,
                )
            )
        )
        documents = list(result.scalars().all())

        # Calculate metrics
        total = len(documents)
        successful = sum(1 for d in documents if d.status == ProcessingStatus.SUCCESS)
        failed = sum(1 for d in documents if d.status == ProcessingStatus.FAILED)

        # Calculate averages for successful documents
        successful_docs = [d for d in documents if d.status == ProcessingStatus.SUCCESS]

        avg_confidence = None
        avg_processing_time = None

        if successful_docs:
            # Calculate average confidence score
            confidence_scores = [
                d.confidence_score for d in successful_docs if d.confidence_score is not None
            ]
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)

            # Calculate average processing time
            processing_times = [
                d.processing_time_ms for d in successful_docs if d.processing_time_ms is not None
            ]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)

        # Update metrics
        metrics.total_documents = total
        metrics.successful_documents = successful
        metrics.failed_documents = failed
        metrics.avg_confidence_score = avg_confidence
        metrics.avg_processing_time_ms = avg_processing_time

        await self.session.commit()
        await self.session.refresh(metrics)

        return metrics

    async def get_metrics_for_date(
        self, user_id: UUID, target_date: date
    ) -> Optional[DailyMetrics]:
        """
        Get metrics for a specific date without creating if not exists.

        Args:
            user_id: User UUID
            target_date: Date to get metrics for

        Returns:
            DailyMetrics if exists, None otherwise
        """
        date_start = datetime.combine(target_date, datetime.min.time())

        result = await self.session.execute(
            select(DailyMetrics).where(
                and_(
                    DailyMetrics.user_id == user_id,
                    DailyMetrics.date == date_start,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_date_range_metrics(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[DailyMetrics]:
        """
        Get metrics for a date range.

        Args:
            user_id: User UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of DailyMetrics ordered by date
        """
        date_start = datetime.combine(start_date, datetime.min.time())
        date_end = datetime.combine(end_date, datetime.max.time())

        result = await self.session.execute(
            select(DailyMetrics)
            .where(
                and_(
                    DailyMetrics.user_id == user_id,
                    DailyMetrics.date >= date_start,
                    DailyMetrics.date <= date_end,
                )
            )
            .order_by(DailyMetrics.date.asc())
        )
        return list(result.scalars().all())
