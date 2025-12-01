"""
Document repository for processed document operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ProcessedDocument, ProcessingStatus
from app.repositories.base import SQLAlchemyRepository


class DocumentRepository(SQLAlchemyRepository[ProcessedDocument]):
    """Repository for ProcessedDocument model operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProcessedDocument, session)

    async def get_by_paperless_id(
        self, paperless_id: int, user_id: UUID
    ) -> Optional[ProcessedDocument]:
        """
        Get document by Paperless document ID and user.

        Args:
            paperless_id: Paperless document ID
            user_id: User UUID

        Returns:
            ProcessedDocument if found, None otherwise
        """
        result = await self.session.execute(
            select(ProcessedDocument).where(
                ProcessedDocument.paperless_document_id == paperless_id,
                ProcessedDocument.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_documents(
        self,
        user_id: UUID,
        status: Optional[ProcessingStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ProcessedDocument]:
        """
        Get documents for a specific user.

        Args:
            user_id: User UUID
            status: Optional status filter
            limit: Maximum results
            offset: Results offset

        Returns:
            List of documents
        """
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status

        return await self.list(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by="-processed_at",
        )

    async def get_recent_documents(
        self, user_id: UUID, days: int = 7
    ) -> List[ProcessedDocument]:
        """
        Get documents processed in the last N days.

        Args:
            user_id: User UUID
            days: Number of days to look back

        Returns:
            List of recent documents
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(ProcessedDocument)
            .where(
                ProcessedDocument.user_id == user_id,
                ProcessedDocument.processed_at >= cutoff_date,
            )
            .order_by(ProcessedDocument.processed_at.desc())
        )
        return list(result.scalars().all())

    async def get_failed_documents(self, user_id: UUID) -> List[ProcessedDocument]:
        """
        Get all failed documents for a user.

        Args:
            user_id: User UUID

        Returns:
            List of failed documents
        """
        return await self.list(
            filters={"user_id": user_id, "status": ProcessingStatus.FAILED},
            order_by="-processed_at",
        )

    async def get_pending_approval(self, user_id: UUID) -> List[ProcessedDocument]:
        """
        Get documents pending approval.

        Args:
            user_id: User UUID

        Returns:
            List of documents pending approval
        """
        return await self.list(
            filters={"user_id": user_id, "status": ProcessingStatus.PENDING_APPROVAL},
            order_by="-processed_at",
        )

    async def mark_as_processed(
        self,
        paperless_id: int,
        user_id: UUID,
        status: ProcessingStatus,
        suggested_data: dict,
        confidence_score: float,
        processing_time_ms: int,
    ) -> ProcessedDocument:
        """
        Mark a document as processed.

        Args:
            paperless_id: Paperless document ID
            user_id: User UUID
            status: Processing status
            suggested_data: AI-suggested metadata
            confidence_score: Overall confidence score
            processing_time_ms: Processing time in milliseconds

        Returns:
            Created/updated ProcessedDocument
        """
        # Check if already exists
        existing = await self.get_by_paperless_id(paperless_id, user_id)

        if existing:
            existing.status = status
            existing.suggested_data = suggested_data
            existing.confidence_score = confidence_score
            existing.processing_time_ms = processing_time_ms
            existing.processed_at = datetime.utcnow()
            existing.reprocess_count += 1
            return await self.update(existing)
        else:
            document = ProcessedDocument(
                user_id=user_id,
                paperless_document_id=paperless_id,
                status=status,
                suggested_data=suggested_data,
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms,
            )
            return await self.create(document)

    async def filter_documents(
        self,
        user_id: UUID,
        status: Optional[ProcessingStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_confidence: Optional[float] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProcessedDocument]:
        """
        Filter documents with multiple criteria.

        Args:
            user_id: User UUID
            status: Optional status filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            min_confidence: Optional minimum confidence score
            search: Optional search term for title (case-insensitive partial match)
            limit: Maximum results
            offset: Results offset

        Returns:
            List of filtered documents
        """
        query = select(ProcessedDocument).where(ProcessedDocument.user_id == user_id)

        # Apply status filter
        if status:
            query = query.where(ProcessedDocument.status == status)

        # Apply date range filters
        if start_date:
            query = query.where(ProcessedDocument.processed_at >= start_date)
        if end_date:
            query = query.where(ProcessedDocument.processed_at <= end_date)

        # Apply confidence filter
        if min_confidence is not None:
            query = query.where(ProcessedDocument.confidence_score >= min_confidence)

        # Apply search filter on suggested_data title
        if search:
            # Search within the suggested_data JSON field for the title
            # Use json_extract for SQLite compatibility
            search_term = f"%{search.lower()}%"
            query = query.where(
                func.lower(
                    func.json_extract(
                        ProcessedDocument.suggested_data,
                        '$.title'
                    )
                ).like(search_term)
            )

        # Apply ordering (most recent first)
        query = query.order_by(ProcessedDocument.processed_at.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_processing_stats(self, user_id: UUID) -> dict:
        """
        Get processing statistics for a user.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with statistics
        """
        total = await self.count({"user_id": user_id})
        success = await self.count(
            {"user_id": user_id, "status": ProcessingStatus.SUCCESS}
        )
        failed = await self.count(
            {"user_id": user_id, "status": ProcessingStatus.FAILED}
        )
        pending = await self.count(
            {"user_id": user_id, "status": ProcessingStatus.PENDING_APPROVAL}
        )

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "pending_approval": pending,
            "success_rate": (success / total * 100) if total > 0 else 0,
        }
