"""
Enhanced queue worker with per-user Paperless client support.

This module provides a queue manager wrapper that properly handles per-user
Paperless credentials during document processing.
"""

import asyncio
from datetime import datetime
from typing import Optional, Set
from uuid import UUID

from app.config import get_settings
from app.core.logging import get_logger
from app.database.models import QueueStatus
from app.database.session import sessionmanager
from app.repositories.queue import QueueRepository
from app.services.processing.pipeline import DocumentProcessor
from app.workers.processor import process_single_document

logger = get_logger(__name__)


class EnhancedQueueWorker:
    """
    Enhanced queue worker with per-user Paperless client support.

    This worker extends the base queue manager functionality to properly
    handle per-user Paperless credentials during document processing.
    """

    def __init__(
        self,
        processor: DocumentProcessor,
        max_workers: int = 1,
        polling_interval: int = 30,
    ):
        """
        Initialize enhanced queue worker.

        Args:
            processor: Document processor instance (with AI provider)
            max_workers: Maximum concurrent workers
            polling_interval: Seconds between polls in realtime mode
        """
        self.processor = processor
        self.max_workers = max_workers
        self.polling_interval = polling_interval
        self.settings = get_settings()

        # Queue state
        self.is_running = False
        self.is_paused = False
        self._worker_tasks = []
        self._shutdown_event = asyncio.Event()

        # Track actively processing documents to avoid duplicates
        self._processing_docs: Set[int] = set()
        self._processing_lock = asyncio.Lock()

        # Statistics
        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_retries": 0,
            "start_time": None,
        }

    async def start(self) -> None:
        """Start queue processing workers."""
        if self.is_running:
            logger.warning("Queue worker already running")
            return

        logger.info(f"Starting queue worker with {self.max_workers} worker(s)")
        self.is_running = True
        self.is_paused = False
        self._shutdown_event.clear()
        self.stats["start_time"] = datetime.utcnow()

        # Start worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker_loop(worker_id=i))
            self._worker_tasks.append(task)
            logger.debug(f"Started worker {i}")

        logger.info(f"Queue worker started with {self.max_workers} worker(s)")

    async def stop(self, timeout: int = 30) -> None:
        """Stop queue processing gracefully."""
        if not self.is_running:
            logger.warning("Queue worker not running")
            return

        logger.info("Stopping queue worker gracefully...")
        self.is_running = False
        self._shutdown_event.set()

        # Wait for workers to finish with timeout
        if self._worker_tasks:
            logger.info(f"Waiting for {len(self._worker_tasks)} worker(s) to finish...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._worker_tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Workers did not finish within {timeout}s, cancelling...")
                for task in self._worker_tasks:
                    task.cancel()

        self._worker_tasks.clear()
        self._processing_docs.clear()

        # Log final statistics
        if self.stats["start_time"]:
            uptime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
            logger.info(
                f"Queue worker stopped. Stats: "
                f"processed={self.stats['total_processed']}, "
                f"success={self.stats['total_success']}, "
                f"failed={self.stats['total_failed']}, "
                f"uptime={uptime:.1f}s"
            )

    async def pause(self) -> None:
        """Pause queue processing."""
        if not self.is_running:
            logger.warning("Queue worker not running")
            return
        logger.info("Pausing queue processing")
        self.is_paused = True

    async def resume(self) -> None:
        """Resume queue processing after pause."""
        if not self.is_running:
            logger.warning("Queue worker not running")
            return
        logger.info("Resuming queue processing")
        self.is_paused = False

    async def process_next(self, user_id: Optional[UUID] = None) -> bool:
        """
        Process the next item in the queue.

        Args:
            user_id: Optional user filter

        Returns:
            True if an item was processed, False if queue empty
        """
        try:
            async with sessionmanager.session() as session:
                queue_repo = QueueRepository(session)

                # Get next queued item
                queue_item = await queue_repo.get_next_queued(user_id=user_id)
                if not queue_item:
                    return False

                # Check if already processing (race condition protection)
                async with self._processing_lock:
                    if queue_item.paperless_document_id in self._processing_docs:
                        logger.debug(
                            f"Document {queue_item.paperless_document_id} "
                            "already being processed, skipping"
                        )
                        return False
                    self._processing_docs.add(queue_item.paperless_document_id)

                try:
                    # Mark as processing
                    await queue_repo.mark_processing(queue_item.id)
                    await session.commit()

                    logger.info(
                        f"Processing document {queue_item.paperless_document_id} "
                        f"from queue (ID: {queue_item.id})"
                    )

                    # Process document through enhanced processor
                    result = await process_single_document(
                        queue_item=queue_item,
                        processor=self.processor,
                        session=session,
                    )

                    # Mark as completed or failed
                    if result["success"]:
                        await queue_repo.mark_completed(queue_item.id)
                        self.stats["total_success"] += 1
                        logger.info(
                            f"Successfully completed document {queue_item.paperless_document_id}"
                        )
                    else:
                        error_msg = result.get("error", "Unknown error")
                        await queue_repo.mark_failed(queue_item.id, error_msg)
                        self.stats["total_failed"] += 1
                        logger.error(
                            f"Failed to process document {queue_item.paperless_document_id}: "
                            f"{error_msg}"
                        )

                    await session.commit()
                    self.stats["total_processed"] += 1

                    return True

                finally:
                    # Remove from processing set
                    async with self._processing_lock:
                        self._processing_docs.discard(queue_item.paperless_document_id)

        except Exception as e:
            logger.error(f"Error processing next queue item: {e}", exc_info=True)
            return False

    async def _worker_loop(self, worker_id: int) -> None:
        """
        Main worker loop - continuously processes queue items.

        Args:
            worker_id: Worker identifier for logging
        """
        logger.debug(f"Worker {worker_id} started")

        while self.is_running:
            try:
                # Check if paused
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue

                # Process next item
                processed = await self.process_next()

                if not processed:
                    # Queue empty, wait before checking again
                    await asyncio.sleep(2)

            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_id} cancelled")
                break

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Back off on error

        logger.debug(f"Worker {worker_id} stopped")

    async def get_stats(self) -> dict:
        """
        Get queue worker statistics.

        Returns:
            Dictionary with queue statistics
        """
        try:
            async with sessionmanager.session() as session:
                queue_repo = QueueRepository(session)
                queue_stats = await queue_repo.get_queue_stats()

            uptime_seconds = 0
            if self.stats["start_time"]:
                uptime_seconds = (datetime.utcnow() - self.stats["start_time"]).total_seconds()

            return {
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "mode": self.settings.processing.mode,
                "workers": self.max_workers,
                "uptime_seconds": uptime_seconds,
                "queue": queue_stats,
                "lifetime": {
                    "total_processed": self.stats["total_processed"],
                    "total_success": self.stats["total_success"],
                    "total_failed": self.stats["total_failed"],
                    "total_retries": self.stats["total_retries"],
                },
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

    async def add_document(
        self,
        user_id: UUID,
        paperless_document_id: int,
        priority: int = 0,
    ) -> bool:
        """
        Add a document to the processing queue.

        Args:
            user_id: User UUID
            paperless_document_id: Paperless document ID
            priority: Queue priority (higher = processed first)

        Returns:
            True if added successfully, False otherwise
        """
        logger.info(
            f"Adding document {paperless_document_id} to queue "
            f"(user: {user_id}, priority: {priority})"
        )

        try:
            async with sessionmanager.session() as session:
                queue_repo = QueueRepository(session)

                # Add to queue (repository handles duplicate check)
                queue_item = await queue_repo.add_to_queue(
                    user_id=user_id,
                    paperless_document_id=paperless_document_id,
                    priority=priority,
                )

                await session.commit()

                logger.debug(f"Document {paperless_document_id} added to queue (ID: {queue_item.id})")
                return True

        except Exception as e:
            logger.error(f"Failed to add document {paperless_document_id} to queue: {e}")
            return False


# Global worker instance
_queue_worker: Optional[EnhancedQueueWorker] = None


def get_queue_worker() -> EnhancedQueueWorker:
    """
    Get global queue worker instance.

    Returns:
        EnhancedQueueWorker instance

    Raises:
        RuntimeError: If queue worker not initialized
    """
    if _queue_worker is None:
        raise RuntimeError(
            "Queue worker not initialized. Call init_queue_worker() first."
        )
    return _queue_worker


def init_queue_worker(
    processor: DocumentProcessor,
    max_workers: Optional[int] = None,
    polling_interval: Optional[int] = None,
) -> EnhancedQueueWorker:
    """
    Initialize global queue worker.

    Args:
        processor: Document processor instance
        max_workers: Maximum concurrent workers (None = use config)
        polling_interval: Polling interval in seconds (None = use config)

    Returns:
        Initialized EnhancedQueueWorker instance
    """
    global _queue_worker

    settings = get_settings()

    if max_workers is None:
        max_workers = settings.processing.concurrent_workers

    if polling_interval is None:
        polling_interval = settings.processing.polling_interval

    _queue_worker = EnhancedQueueWorker(
        processor=processor,
        max_workers=max_workers,
        polling_interval=polling_interval,
    )

    logger.info(
        f"Queue worker initialized (workers: {max_workers}, "
        f"polling: {polling_interval}s)"
    )

    return _queue_worker
