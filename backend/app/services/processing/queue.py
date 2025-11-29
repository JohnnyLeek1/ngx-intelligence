"""
Queue management service for document processing.

Manages the processing queue, scheduling, and background task execution with
support for real-time polling, batch processing, and approval workflows.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID

from app.config import get_settings
from app.core.logging import get_logger
from app.database.models import ApprovalStatus, ProcessingStatus, QueueStatus
from app.database.session import sessionmanager
from app.repositories.approval import ApprovalRepository
from app.repositories.document import DocumentRepository
from app.repositories.queue import QueueRepository
from app.services.paperless import PaperlessClient
from app.services.processing.pipeline import DocumentProcessor, ProcessingError

logger = get_logger(__name__)


class QueueManager:
    """
    Queue manager for document processing.

    Handles queue operations, worker management, and background processing with
    support for:
    - Real-time polling mode (continuously poll paperless-ngx for new documents)
    - Batch processing mode (scheduled processing at intervals)
    - Manual processing mode (user-triggered processing)
    - Concurrent workers with configurable parallelism
    - Retry logic for failed documents
    - Approval workflow integration

    Example:
        >>> manager = QueueManager(processor, paperless_client)
        >>> await manager.start()  # Start background processing
        >>> await manager.add_document(user_id, doc_id, priority=1)
        >>> await manager.stop()  # Graceful shutdown
    """

    def __init__(
        self,
        processor: DocumentProcessor,
        paperless_client: PaperlessClient,
        max_workers: int = 1,
        polling_interval: int = 30,
    ):
        """
        Initialize queue manager.

        Args:
            processor: Document processor instance
            paperless_client: Paperless API client
            max_workers: Maximum concurrent workers (default: 1)
            polling_interval: Seconds between polls in realtime mode (default: 30)
        """
        self.processor = processor
        self.paperless_client = paperless_client
        self.max_workers = max_workers
        self.polling_interval = polling_interval
        self.settings = get_settings()

        # Queue state
        self.is_running = False
        self.is_paused = False
        self._worker_tasks: List[asyncio.Task] = []
        self._polling_task: Optional[asyncio.Task] = None
        self._batch_task: Optional[asyncio.Task] = None
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
        """
        Start queue processing based on configured mode.

        Starts background workers and polling/batch tasks according to
        the processing.mode configuration setting.
        """
        if self.is_running:
            logger.warning("Queue manager already running")
            return

        logger.info(f"Starting queue manager in {self.settings.processing.mode} mode")
        self.is_running = True
        self.is_paused = False
        self._shutdown_event.clear()
        self.stats["start_time"] = datetime.utcnow()

        # Start worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker_loop(worker_id=i))
            self._worker_tasks.append(task)
            logger.debug(f"Started worker {i}")

        # Start mode-specific tasks
        if self.settings.processing.mode == "realtime":
            logger.info(f"Starting real-time polling (interval: {self.polling_interval}s)")
            self._polling_task = asyncio.create_task(self._polling_loop())

        elif self.settings.processing.mode == "batch":
            logger.info("Starting batch processing mode")
            self._batch_task = asyncio.create_task(self._batch_loop())

        else:  # manual mode
            logger.info("Running in manual mode - documents must be added explicitly")

        logger.info(f"Queue manager started with {self.max_workers} worker(s)")

    async def stop(self, timeout: int = 30) -> None:
        """
        Stop queue processing gracefully.

        Waits for current items to complete processing before shutting down.

        Args:
            timeout: Maximum seconds to wait for graceful shutdown (default: 30)
        """
        if not self.is_running:
            logger.warning("Queue manager not running")
            return

        logger.info("Stopping queue manager gracefully...")
        self.is_running = False
        self._shutdown_event.set()

        # Cancel polling/batch tasks
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await asyncio.wait_for(self._polling_task, timeout=5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        if self._batch_task:
            self._batch_task.cancel()
            try:
                await asyncio.wait_for(self._batch_task, timeout=5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

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
        uptime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        logger.info(
            f"Queue manager stopped. Stats: "
            f"processed={self.stats['total_processed']}, "
            f"success={self.stats['total_success']}, "
            f"failed={self.stats['total_failed']}, "
            f"uptime={uptime:.1f}s"
        )

    async def pause(self) -> None:
        """
        Pause queue processing.

        Workers will stop processing new items but current items will complete.
        """
        if not self.is_running:
            logger.warning("Queue manager not running")
            return

        logger.info("Pausing queue processing")
        self.is_paused = True

    async def resume(self) -> None:
        """
        Resume queue processing after pause.
        """
        if not self.is_running:
            logger.warning("Queue manager not running")
            return

        logger.info("Resuming queue processing")
        self.is_paused = False

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
            priority: Queue priority (higher = processed first, default: 0)

        Returns:
            True if added successfully, False if already queued/processing
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

    async def process_next(self, user_id: Optional[UUID] = None) -> bool:
        """
        Process the next item in the queue.

        Args:
            user_id: Optional user filter (process only this user's documents)

        Returns:
            True if an item was processed, False if queue empty
        """
        try:
            async with sessionmanager.session() as session:
                queue_repo = QueueRepository(session)
                doc_repo = DocumentRepository(session)
                approval_repo = ApprovalRepository(session)

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

                    # Process document through pipeline
                    result = await self._process_single_document(
                        queue_item=queue_item,
                        doc_repo=doc_repo,
                        approval_repo=approval_repo,
                        session=session,
                    )

                    # Mark as completed or failed
                    if result["success"]:
                        await queue_repo.mark_completed(queue_item.id)
                        self.stats["total_success"] += 1
                    else:
                        error_msg = result.get("error", "Unknown error")
                        await queue_repo.mark_failed(queue_item.id, error_msg)
                        self.stats["total_failed"] += 1

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

    async def _process_single_document(
        self,
        queue_item,
        doc_repo: DocumentRepository,
        approval_repo: ApprovalRepository,
        session,
    ) -> Dict:
        """
        Process a single document and update repositories.

        Args:
            queue_item: ProcessingQueue item
            doc_repo: DocumentRepository instance
            approval_repo: ApprovalRepository instance
            session: Database session

        Returns:
            Processing result dictionary
        """
        try:
            # Process through pipeline
            result = await self.processor.process_document(
                document_id=queue_item.paperless_document_id,
                user_id=queue_item.user_id,
                max_retries=self.settings.processing.retry_attempts,
            )

            # Determine status based on approval mode
            approval_mode = result.get("approval_mode", False)
            if approval_mode:
                status = ProcessingStatus.PENDING_APPROVAL
            else:
                status = ProcessingStatus.SUCCESS

            # Save to processed_documents table
            await doc_repo.mark_as_processed(
                paperless_id=queue_item.paperless_document_id,
                user_id=queue_item.user_id,
                status=status,
                suggested_data=result["suggested_data"],
                confidence_score=result["confidence_score"],
                processing_time_ms=result["processing_time_ms"],
            )

            # If approval mode, add to approval queue
            if approval_mode:
                logger.info(
                    f"Approval mode enabled - adding document {queue_item.paperless_document_id} "
                    "to approval queue"
                )

                # Get the processed document to link approval
                processed_doc = await doc_repo.get_by_paperless_id(
                    queue_item.paperless_document_id,
                    queue_item.user_id,
                )

                # Create approval queue entry
                from app.database.models import ApprovalQueue
                approval_item = ApprovalQueue(
                    document_id=processed_doc.id,
                    user_id=queue_item.user_id,
                    suggestions=result["suggested_data"],
                    status=ApprovalStatus.PENDING,
                )
                session.add(approval_item)

                # Apply approval-pending tag in paperless
                try:
                    pending_tag = self.settings.approval_workflow.pending_tag
                    # Get existing tags
                    doc_data = await self.paperless_client.get_document(
                        queue_item.paperless_document_id
                    )
                    existing_tags = doc_data.get("tags", [])

                    # Find or create approval-pending tag
                    all_tags = await self.paperless_client.get_tags()
                    pending_tag_id = None
                    for tag in all_tags:
                        if tag.get("name") == pending_tag:
                            pending_tag_id = tag.get("id")
                            break

                    if pending_tag_id and pending_tag_id not in existing_tags:
                        existing_tags.append(pending_tag_id)
                        await self.paperless_client.update_document(
                            queue_item.paperless_document_id,
                            {"tags": existing_tags}
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to apply approval-pending tag: {e}",
                        exc_info=True
                    )

            else:
                # Directly apply changes to paperless
                logger.info(
                    f"Applying AI suggestions directly to document "
                    f"{queue_item.paperless_document_id}"
                )
                await self._apply_suggestions_to_paperless(
                    document_id=queue_item.paperless_document_id,
                    suggestions=result["suggested_data"],
                )

            logger.info(
                f"Successfully processed document {queue_item.paperless_document_id} "
                f"(confidence: {result['confidence_score']:.2f})"
            )

            return {"success": True, **result}

        except ProcessingError as e:
            logger.error(
                f"Processing error for document {queue_item.paperless_document_id}: {e.message}"
            )
            return {
                "success": False,
                "error": e.message,
                "document_id": queue_item.paperless_document_id,
            }

        except Exception as e:
            logger.error(
                f"Unexpected error processing document {queue_item.paperless_document_id}: {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "error": str(e),
                "document_id": queue_item.paperless_document_id,
            }

    async def _apply_suggestions_to_paperless(
        self,
        document_id: int,
        suggestions: Dict,
    ) -> None:
        """
        Apply AI suggestions directly to Paperless document.

        Args:
            document_id: Paperless document ID
            suggestions: Suggested metadata from AI processing
        """
        try:
            update_data = {}

            # Apply title
            if suggestions.get("title"):
                update_data["title"] = suggestions["title"]

            # Apply correspondent
            if suggestions.get("correspondent_id"):
                update_data["correspondent"] = suggestions["correspondent_id"]

            # Apply document type
            if suggestions.get("document_type_id"):
                update_data["document_type"] = suggestions["document_type_id"]

            # Apply tags
            if suggestions.get("tag_ids"):
                update_data["tags"] = suggestions["tag_ids"]

            # Apply document date
            if suggestions.get("document_date"):
                update_data["created"] = suggestions["document_date"]

            if update_data:
                await self.paperless_client.update_document(document_id, update_data)
                logger.info(f"Applied {len(update_data)} metadata updates to document {document_id}")
            else:
                logger.debug(f"No updates to apply for document {document_id}")

        except Exception as e:
            logger.error(f"Failed to apply suggestions to Paperless: {e}")
            raise

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

    async def _polling_loop(self) -> None:
        """
        Real-time polling loop - continuously polls Paperless for new documents.

        Checks Paperless API for documents that haven't been processed yet and
        adds them to the queue.
        """
        logger.info("Real-time polling loop started")

        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(self.polling_interval)
                    continue

                logger.debug("Polling Paperless for new documents...")
                await self._poll_paperless_for_new_documents()

                # Wait for next poll interval
                await asyncio.sleep(self.polling_interval)

            except asyncio.CancelledError:
                logger.info("Polling loop cancelled")
                break

            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(self.polling_interval)

        logger.info("Real-time polling loop stopped")

    async def _poll_paperless_for_new_documents(self) -> None:
        """
        Poll Paperless-ngx API for new documents and add to queue.

        Fetches recent documents from Paperless and checks which ones haven't
        been processed yet in our database.
        """
        try:
            async with sessionmanager.session() as session:
                doc_repo = DocumentRepository(session)

                # Get recent documents from Paperless (last 24 hours)
                # Note: This is a simplified approach. For production, you might want
                # to track the last poll time and only fetch documents since then.
                response = await self.paperless_client.list_documents(
                    page=1,
                    page_size=100,
                    filters={
                        "ordering": "-created",  # Newest first
                    }
                )

                documents = response.get("results", [])
                logger.debug(f"Found {len(documents)} recent documents in Paperless")

                # For each document, check if it's been processed
                new_count = 0
                for doc in documents:
                    doc_id = doc.get("id")
                    if not doc_id:
                        continue

                    # TODO: Need to get user_id - this is a limitation of the current approach
                    # In a real system, you'd need a way to map Paperless documents to users
                    # For now, we'll skip this in polling mode and rely on manual/webhook triggers

                    # Example of how you'd check if processed:
                    # processed = await doc_repo.get_by_paperless_id(doc_id, user_id)
                    # if not processed:
                    #     await self.add_document(user_id, doc_id, priority=0)
                    #     new_count += 1

                if new_count > 0:
                    logger.info(f"Added {new_count} new documents to processing queue")

        except Exception as e:
            logger.error(f"Error polling Paperless for new documents: {e}", exc_info=True)

    async def _batch_loop(self) -> None:
        """
        Batch processing loop - processes documents based on configured rules.

        Processes documents in batches according to:
        - Document count threshold
        - Time interval threshold
        - Combined rules (both/either)
        """
        logger.info("Batch processing loop started")

        last_batch_time = datetime.utcnow()
        documents_since_batch = 0

        batch_rules = self.settings.processing.batch_rules
        time_threshold_seconds = batch_rules.time_threshold
        doc_threshold = batch_rules.document_threshold

        logger.info(
            f"Batch rules: {doc_threshold} documents OR "
            f"{time_threshold_seconds}s (rule: {batch_rules.rule_type})"
        )

        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(60)
                    continue

                # Check batch processing triggers
                time_elapsed = (datetime.utcnow() - last_batch_time).total_seconds()
                time_threshold_met = time_elapsed >= time_threshold_seconds

                # Count queued documents
                async with sessionmanager.session() as session:
                    queue_repo = QueueRepository(session)
                    stats = await queue_repo.get_queue_stats()
                    queued_count = stats.get("queued", 0)

                doc_threshold_met = queued_count >= doc_threshold

                # Determine if we should process batch
                should_process = False
                if batch_rules.rule_type == "both":
                    should_process = time_threshold_met and doc_threshold_met
                else:  # either
                    should_process = time_threshold_met or doc_threshold_met

                if should_process:
                    logger.info(
                        f"Batch processing triggered (queued: {queued_count}, "
                        f"elapsed: {time_elapsed:.1f}s)"
                    )
                    await self._execute_batch_processing()
                    last_batch_time = datetime.utcnow()
                    documents_since_batch = 0

                # Sleep for a minute before checking again
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.info("Batch loop cancelled")
                break

            except Exception as e:
                logger.error(f"Error in batch loop: {e}", exc_info=True)
                await asyncio.sleep(60)

        logger.info("Batch processing loop stopped")

    async def _execute_batch_processing(self) -> None:
        """
        Execute a batch processing run.

        Processes all currently queued documents.
        """
        logger.info("Executing batch processing")

        try:
            async with sessionmanager.session() as session:
                queue_repo = QueueRepository(session)
                stats = await queue_repo.get_queue_stats()

            queued_count = stats.get("queued", 0)
            logger.info(f"Processing batch of {queued_count} documents")

            # Workers will automatically process the queued items
            # Just log the batch execution
            processed = 0
            while processed < queued_count:
                success = await self.process_next()
                if success:
                    processed += 1
                else:
                    break  # Queue empty

            logger.info(f"Batch processing completed: {processed} documents processed")

        except Exception as e:
            logger.error(f"Error executing batch processing: {e}", exc_info=True)

    async def clear_completed(self, days_old: int = 7) -> int:
        """
        Clear old completed queue items.

        Args:
            days_old: Clear items older than N days (default: 7)

        Returns:
            Number of items cleared
        """
        logger.info(f"Clearing completed queue items older than {days_old} days")

        try:
            async with sessionmanager.session() as session:
                queue_repo = QueueRepository(session)
                count = await queue_repo.clear_completed(days_old=days_old)
                await session.commit()

            logger.info(f"Cleared {count} completed queue items")
            return count

        except Exception as e:
            logger.error(f"Error clearing completed items: {e}")
            return 0

    async def retry_failed(self, max_retries: int = 3) -> int:
        """
        Retry all failed queue items that haven't exceeded max retries.

        Args:
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Number of items re-queued
        """
        logger.info(f"Retrying failed items (max retries: {max_retries})")

        try:
            async with sessionmanager.session() as session:
                queue_repo = QueueRepository(session)

                # Get all failed items
                failed_items = await queue_repo.list(
                    filters={"status": QueueStatus.FAILED}
                )

                # Filter by retry count and retry
                retried = 0
                for item in failed_items:
                    if item.retry_count < max_retries:
                        await queue_repo.retry_item(item.id)
                        retried += 1
                        self.stats["total_retries"] += 1

                await session.commit()

            logger.info(f"Re-queued {retried} failed items for retry")
            return retried

        except Exception as e:
            logger.error(f"Error retrying failed items: {e}")
            return 0

    async def get_stats(self) -> Dict:
        """
        Get queue manager statistics.

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


# Global queue manager instance
_queue_manager: Optional[QueueManager] = None


def get_queue_manager() -> QueueManager:
    """
    Get global queue manager instance.

    Returns:
        QueueManager instance

    Raises:
        RuntimeError: If queue manager not initialized
    """
    if _queue_manager is None:
        raise RuntimeError(
            "Queue manager not initialized. Call init_queue_manager() first."
        )
    return _queue_manager


def init_queue_manager(
    processor: DocumentProcessor,
    paperless_client: PaperlessClient,
    max_workers: Optional[int] = None,
    polling_interval: Optional[int] = None,
) -> QueueManager:
    """
    Initialize global queue manager.

    Args:
        processor: Document processor instance
        paperless_client: Paperless API client
        max_workers: Maximum concurrent workers (None = use config)
        polling_interval: Polling interval in seconds (None = use config)

    Returns:
        Initialized QueueManager instance
    """
    global _queue_manager

    settings = get_settings()

    if max_workers is None:
        max_workers = settings.processing.concurrent_workers

    if polling_interval is None:
        polling_interval = settings.processing.polling_interval

    _queue_manager = QueueManager(
        processor=processor,
        paperless_client=paperless_client,
        max_workers=max_workers,
        polling_interval=polling_interval,
    )

    logger.info(
        f"Queue manager initialized (workers: {max_workers}, "
        f"polling: {polling_interval}s)"
    )

    return _queue_manager
