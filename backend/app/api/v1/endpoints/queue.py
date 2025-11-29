"""
Queue API endpoints.

Handles queue status, management, and statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database.models import User
from app.dependencies import get_current_user, get_queue_repository, get_user_paperless_client
from app.repositories import QueueRepository, DocumentRepository
from app.schemas import QueueStatsResponse
from app.database.session import get_db
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/queue", tags=["Queue"])


class ProcessNowRequest(BaseModel):
    """Request to manually process documents."""
    limit: int = 10  # Number of documents to fetch and process


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    current_user: User = Depends(get_current_user),
    queue_repo: QueueRepository = Depends(get_queue_repository),
) -> QueueStatsResponse:
    """Get queue statistics for current user."""
    stats = await queue_repo.get_queue_stats(user_id=current_user.id)
    return QueueStatsResponse(**stats)


@router.post("/pause")
async def pause_queue(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Pause queue processing (stub)."""
    # TODO: Implement queue pausing
    return {"message": "Queue pause not yet implemented"}


@router.post("/resume")
async def resume_queue(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Resume queue processing (stub)."""
    # TODO: Implement queue resuming
    return {"message": "Queue resume not yet implemented"}


@router.post("/process-now")
async def process_now(
    request: ProcessNowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Manually trigger processing of documents from Paperless.

    Fetches recent unprocessed documents from Paperless and queues them for AI processing.
    """
    from app.services.paperless import get_paperless_client
    from app.database.models import ProcessingQueue, QueueStatus, ProcessedDocument
    from sqlalchemy import select
    from datetime import datetime, timezone

    try:
        # Get Paperless client for user
        paperless = await get_paperless_client(
            base_url=current_user.paperless_url,
            auth_token=current_user.paperless_token,
        )

        # Fetch recent documents from Paperless
        logger.info(f"Fetching up to {request.limit} documents from Paperless for user {current_user.username}")
        response = await paperless.list_documents(page=1, page_size=request.limit)

        documents = response.get("results", [])
        if not documents:
            return {
                "message": "No documents found in Paperless",
                "queued": 0,
                "total_found": 0
            }

        # Check which documents are already processed
        doc_repo = DocumentRepository(db)
        queue_repo = QueueRepository(db)

        queued_count = 0
        already_processed = 0
        already_queued = 0

        for doc in documents:
            paperless_id = doc.get("id")

            # Check if already processed
            existing_doc = await doc_repo.get_by_paperless_id(
                paperless_id=paperless_id,
                user_id=current_user.id
            )

            if existing_doc:
                already_processed += 1
                continue

            # Check if already in queue
            stmt = select(ProcessingQueue).where(
                ProcessingQueue.user_id == current_user.id,
                ProcessingQueue.paperless_document_id == paperless_id,
                ProcessingQueue.status.in_([QueueStatus.QUEUED, QueueStatus.PROCESSING])
            )
            result = await db.execute(stmt)
            existing_queue = result.scalar_one_or_none()

            if existing_queue:
                already_queued += 1
                continue

            # Add to processing queue
            queue_item = ProcessingQueue(
                user_id=current_user.id,
                paperless_document_id=paperless_id,
                status=QueueStatus.QUEUED,
                priority=0,
                retry_count=0,
            )
            db.add(queue_item)
            queued_count += 1

        await db.commit()
        await paperless.close()

        logger.info(f"Queued {queued_count} documents for processing (user: {current_user.username})")

        return {
            "message": f"Successfully queued {queued_count} documents for processing",
            "queued": queued_count,
            "total_found": len(documents),
            "already_processed": already_processed,
            "already_queued": already_queued,
        }

    except Exception as e:
        logger.error(f"Failed to queue documents for processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch or queue documents: {str(e)}"
        )
