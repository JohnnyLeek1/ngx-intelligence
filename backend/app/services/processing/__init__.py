"""
Document processing services for ngx-intelligence.

Provides AI-powered document metadata extraction and queue management.
"""

from app.services.processing.pipeline import DocumentProcessor, ProcessingError
from app.services.processing.queue import (
    QueueManager,
    get_queue_manager,
    init_queue_manager,
)

__all__ = [
    "DocumentProcessor",
    "ProcessingError",
    "QueueManager",
    "get_queue_manager",
    "init_queue_manager",
]
