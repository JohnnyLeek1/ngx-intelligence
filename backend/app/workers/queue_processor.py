"""
Queue processor background worker for document processing.

This worker continuously polls the ProcessingQueue table for QUEUED documents,
processes them through the AI pipeline, and updates Paperless with the results.
"""

import asyncio
from typing import Optional

from app.config import get_settings
from app.core.logging import get_logger
from app.services.ai.ollama import OllamaProvider
from app.services.processing.pipeline import DocumentProcessor
from app.workers.queue_worker import EnhancedQueueWorker, init_queue_worker

logger = get_logger(__name__)


class QueueProcessor:
    """
    Background queue processor for document processing.

    Manages the lifecycle of the queue processing system, including:
    - Initializing AI providers and processing pipeline
    - Starting/stopping background workers
    - Graceful shutdown handling

    This is the main entry point for the background processing system.
    """

    def __init__(self):
        """Initialize queue processor."""
        self.settings = get_settings()
        self.queue_worker: Optional[EnhancedQueueWorker] = None
        self.ai_provider: Optional[OllamaProvider] = None
        self.processor: Optional[DocumentProcessor] = None
        self.is_running = False

    async def start(self) -> None:
        """
        Start the queue processor.

        Initializes all required services and starts background workers.
        """
        if self.is_running:
            logger.warning("Queue processor already running")
            return

        logger.info("Starting queue processor...")

        try:
            # Initialize AI provider using database configuration
            # This allows runtime config changes to take effect
            logger.info("Initializing AI provider (Ollama) from database config")

            # We need a database session to load config
            from app.database.session import async_session_maker
            from app.services.ai.ollama import get_ollama_provider_from_config

            async with async_session_maker() as db:
                self.ai_provider = await get_ollama_provider_from_config(db)

            # Verify AI provider is healthy
            ai_healthy = await self.ai_provider.health_check()
            if not ai_healthy:
                # Try to get the configured URL for logging
                base_url = self.ai_provider.base_url
                logger.warning(
                    f"AI provider health check failed at {base_url}. "
                    "Processing may fail until Ollama is available."
                )
            else:
                logger.info(f"AI provider healthy at {self.ai_provider.base_url}")

            # Initialize document processor with AI provider
            # Paperless client will be created per-user during processing
            logger.info("Initializing document processor with AI provider")
            self.processor = DocumentProcessor(
                ai_provider=self.ai_provider,
                paperless_client=None,  # Will be set per-document in the processing flow
            )

            # Initialize enhanced queue worker
            # This worker handles per-user Paperless clients automatically
            logger.info("Initializing enhanced queue worker")
            self.queue_worker = init_queue_worker(
                processor=self.processor,
                max_workers=self.settings.processing.concurrent_workers,
                polling_interval=self.settings.processing.polling_interval,
            )

            # Start queue worker (background workers)
            await self.queue_worker.start()

            self.is_running = True
            logger.info(
                f"Queue processor started successfully "
                f"(mode: {self.settings.processing.mode}, "
                f"workers: {self.settings.processing.concurrent_workers})"
            )

        except Exception as e:
            logger.error(f"Failed to start queue processor: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """
        Stop the queue processor gracefully.

        Waits for current processing to complete before shutting down.
        """
        if not self.is_running:
            logger.debug("Queue processor not running")
            return

        logger.info("Stopping queue processor...")

        try:
            # Stop queue worker
            if self.queue_worker:
                await self.queue_worker.stop(timeout=30)
                logger.info("Queue worker stopped")

            # Close AI provider
            if self.ai_provider:
                await self.ai_provider.close()
                logger.info("AI provider closed")

            self.is_running = False
            logger.info("Queue processor stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping queue processor: {e}", exc_info=True)

    async def pause(self) -> None:
        """Pause queue processing."""
        if self.queue_worker:
            await self.queue_worker.pause()
            logger.info("Queue processor paused")

    async def resume(self) -> None:
        """Resume queue processing."""
        if self.queue_worker:
            await self.queue_worker.resume()
            logger.info("Queue processor resumed")

    async def get_stats(self) -> dict:
        """
        Get queue processor statistics.

        Returns:
            Dictionary with processing statistics
        """
        if not self.queue_worker:
            return {
                "is_running": False,
                "error": "Queue worker not initialized"
            }

        stats = await self.queue_worker.get_stats()
        stats["queue_processor_running"] = self.is_running

        # Add AI provider health
        if self.ai_provider:
            stats["ai_provider_healthy"] = await self.ai_provider.health_check()

        return stats

    def is_healthy(self) -> bool:
        """
        Check if queue processor is healthy.

        Returns:
            True if running and healthy, False otherwise
        """
        return self.is_running and self.queue_worker is not None


# Global queue processor instance
_queue_processor: Optional[QueueProcessor] = None


def get_queue_processor() -> QueueProcessor:
    """
    Get global queue processor instance.

    Returns:
        QueueProcessor instance

    Raises:
        RuntimeError: If queue processor not initialized
    """
    if _queue_processor is None:
        raise RuntimeError(
            "Queue processor not initialized. It should be started in the app lifespan."
        )
    return _queue_processor


def init_queue_processor() -> QueueProcessor:
    """
    Initialize global queue processor.

    Returns:
        Initialized QueueProcessor instance
    """
    global _queue_processor

    if _queue_processor is None:
        _queue_processor = QueueProcessor()
        logger.info("Queue processor initialized")

    return _queue_processor
