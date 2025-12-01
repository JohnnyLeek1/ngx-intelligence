"""
Processing queue repository for queue management operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ProcessingQueue, QueueStatus
from app.repositories.base import SQLAlchemyRepository


class QueueRepository(SQLAlchemyRepository[ProcessingQueue]):
    """Repository for ProcessingQueue model operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProcessingQueue, session)

    async def get_next_queued(self, user_id: Optional[UUID] = None) -> Optional[ProcessingQueue]:
        """
        Get the next queued item to process.

        Args:
            user_id: Optional user filter

        Returns:
            Next queued item or None
        """
        query = select(ProcessingQueue).where(
            ProcessingQueue.status == QueueStatus.QUEUED
        )

        if user_id:
            query = query.where(ProcessingQueue.user_id == user_id)

        query = query.order_by(
            ProcessingQueue.priority.desc(),
            ProcessingQueue.queued_at.asc(),
        ).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_queued_items(
        self, user_id: Optional[UUID] = None
    ) -> List[ProcessingQueue]:
        """
        Get all queued items.

        Args:
            user_id: Optional user filter

        Returns:
            List of queued items
        """
        filters = {"status": QueueStatus.QUEUED}
        if user_id:
            filters["user_id"] = user_id

        return await self.list(
            filters=filters,
            order_by="-priority",
        )

    async def get_processing_items(
        self, user_id: Optional[UUID] = None
    ) -> List[ProcessingQueue]:
        """
        Get currently processing items.

        Args:
            user_id: Optional user filter

        Returns:
            List of processing items
        """
        filters = {"status": QueueStatus.PROCESSING}
        if user_id:
            filters["user_id"] = user_id

        return await self.list(filters=filters, order_by="-started_at")

    async def add_to_queue(
        self, user_id: UUID, paperless_document_id: int, priority: int = 0
    ) -> ProcessingQueue:
        """
        Add a document to the processing queue.

        Args:
            user_id: User UUID
            paperless_document_id: Paperless document ID
            priority: Queue priority (higher = processed first)

        Returns:
            Created queue item
        """
        # Check if already in queue
        result = await self.session.execute(
            select(ProcessingQueue).where(
                ProcessingQueue.user_id == user_id,
                ProcessingQueue.paperless_document_id == paperless_document_id,
                ProcessingQueue.status.in_([QueueStatus.QUEUED, QueueStatus.PROCESSING]),
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        queue_item = ProcessingQueue(
            user_id=user_id,
            paperless_document_id=paperless_document_id,
            priority=priority,
            status=QueueStatus.QUEUED,
        )
        return await self.create(queue_item)

    async def add_documents_to_queue_with_reset(
        self, user_id: UUID, paperless_document_ids: List[int], priority: int = 0
    ) -> dict:
        """
        Add multiple documents to the processing queue with automatic reset.
        If the queue is empty (queued=0 and processing=0), clears completed/failed items first.

        Args:
            user_id: User UUID
            paperless_document_ids: List of Paperless document IDs to add
            priority: Queue priority (higher = processed first)

        Returns:
            Dictionary with operation results
        """
        # Check if queue is empty
        queue_empty = await self.is_queue_empty(user_id)
        cleared_stats = {"completed": 0, "failed": 0, "total": 0}

        # If queue is empty, clear completed and failed items
        if queue_empty:
            cleared_stats = await self.clear_completed_and_failed(user_id)

        # Add new documents to queue
        added_count = 0
        already_queued_count = 0

        for paperless_doc_id in paperless_document_ids:
            # Check if already in queue
            result = await self.session.execute(
                select(ProcessingQueue).where(
                    ProcessingQueue.user_id == user_id,
                    ProcessingQueue.paperless_document_id == paperless_doc_id,
                    ProcessingQueue.status.in_([QueueStatus.QUEUED, QueueStatus.PROCESSING]),
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                already_queued_count += 1
                continue

            # Create new queue item
            queue_item = ProcessingQueue(
                user_id=user_id,
                paperless_document_id=paperless_doc_id,
                priority=priority,
                status=QueueStatus.QUEUED,
            )
            self.session.add(queue_item)
            added_count += 1

        await self.session.commit()

        return {
            "added": added_count,
            "already_queued": already_queued_count,
            "queue_was_reset": queue_empty,
            "cleared": cleared_stats
        }

    async def mark_processing(self, queue_id: UUID) -> Optional[ProcessingQueue]:
        """
        Mark a queue item as processing.

        Args:
            queue_id: Queue item UUID

        Returns:
            Updated queue item or None
        """
        item = await self.get_by_id(queue_id)
        if item:
            item.status = QueueStatus.PROCESSING
            item.started_at = datetime.utcnow()
            return await self.update(item)
        return None

    async def mark_completed(self, queue_id: UUID) -> Optional[ProcessingQueue]:
        """
        Mark a queue item as completed.

        Args:
            queue_id: Queue item UUID

        Returns:
            Updated queue item or None
        """
        item = await self.get_by_id(queue_id)
        if item:
            item.status = QueueStatus.COMPLETED
            item.completed_at = datetime.utcnow()
            return await self.update(item)
        return None

    async def mark_failed(
        self, queue_id: UUID, error_message: str
    ) -> Optional[ProcessingQueue]:
        """
        Mark a queue item as failed.

        Args:
            queue_id: Queue item UUID
            error_message: Error description

        Returns:
            Updated queue item or None
        """
        item = await self.get_by_id(queue_id)
        if item:
            item.status = QueueStatus.FAILED
            item.last_error = error_message
            item.retry_count += 1
            item.completed_at = datetime.utcnow()
            return await self.update(item)
        return None

    async def retry_item(self, queue_id: UUID) -> Optional[ProcessingQueue]:
        """
        Retry a failed queue item.

        Args:
            queue_id: Queue item UUID

        Returns:
            Updated queue item or None
        """
        item = await self.get_by_id(queue_id)
        if item:
            item.status = QueueStatus.QUEUED
            item.started_at = None
            item.completed_at = None
            return await self.update(item)
        return None

    async def get_queue_stats(self, user_id: Optional[UUID] = None) -> dict:
        """
        Get queue statistics.

        Args:
            user_id: Optional user filter

        Returns:
            Dictionary with queue statistics
        """
        base_filters = {}
        if user_id:
            base_filters["user_id"] = user_id

        queued = await self.count({**base_filters, "status": QueueStatus.QUEUED})
        processing = await self.count({**base_filters, "status": QueueStatus.PROCESSING})
        completed = await self.count({**base_filters, "status": QueueStatus.COMPLETED})
        failed = await self.count({**base_filters, "status": QueueStatus.FAILED})

        return {
            "queued": queued,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "total": queued + processing + completed + failed,
        }

    async def clear_completed(self, user_id: Optional[UUID] = None, days_old: int = 7) -> int:
        """
        Clear old completed queue items.

        Args:
            user_id: Optional user filter
            days_old: Clear items older than N days

        Returns:
            Number of items cleared
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        query = select(ProcessingQueue).where(
            ProcessingQueue.status == QueueStatus.COMPLETED,
            ProcessingQueue.completed_at < cutoff_date,
        )

        if user_id:
            query = query.where(ProcessingQueue.user_id == user_id)

        result = await self.session.execute(query)
        items = result.scalars().all()

        count = len(items)
        for item in items:
            await self.session.delete(item)

        await self.session.commit()
        return count

    async def is_queue_empty(self, user_id: UUID) -> bool:
        """
        Check if the queue is empty (no queued or processing items).

        Args:
            user_id: User UUID

        Returns:
            True if queue is empty (queued=0 and processing=0)
        """
        queued_count = await self.count({
            "user_id": user_id,
            "status": QueueStatus.QUEUED
        })

        processing_count = await self.count({
            "user_id": user_id,
            "status": QueueStatus.PROCESSING
        })

        return queued_count == 0 and processing_count == 0

    async def clear_completed_and_failed(self, user_id: UUID) -> dict:
        """
        Clear all completed and failed queue items for a user.
        This represents clearing the stats for a new processing batch.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with counts of cleared items
        """
        # Get completed items
        query_completed = select(ProcessingQueue).where(
            ProcessingQueue.user_id == user_id,
            ProcessingQueue.status == QueueStatus.COMPLETED,
        )
        result_completed = await self.session.execute(query_completed)
        completed_items = result_completed.scalars().all()

        # Get failed items
        query_failed = select(ProcessingQueue).where(
            ProcessingQueue.user_id == user_id,
            ProcessingQueue.status == QueueStatus.FAILED,
        )
        result_failed = await self.session.execute(query_failed)
        failed_items = result_failed.scalars().all()

        # Delete all items
        completed_count = len(completed_items)
        failed_count = len(failed_items)

        for item in completed_items:
            await self.session.delete(item)

        for item in failed_items:
            await self.session.delete(item)

        await self.session.commit()

        return {
            "completed": completed_count,
            "failed": failed_count,
            "total": completed_count + failed_count
        }
