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


@router.delete("/completed")
async def clear_completed_and_failed(
    current_user: User = Depends(get_current_user),
    queue_repo: QueueRepository = Depends(get_queue_repository),
) -> dict:
    """
    Manually clear all completed and failed queue items.

    This is useful for resetting queue statistics and starting fresh.
    """
    try:
        result = await queue_repo.clear_completed_and_failed(user_id=current_user.id)

        if result["total"] == 0:
            return {
                "message": "No completed or failed items to clear",
                "cleared": result
            }

        logger.info(
            f"Cleared {result['total']} queue items for user {current_user.username} "
            f"({result['completed']} completed, {result['failed']} failed)"
        )

        return {
            "message": f"Successfully cleared {result['completed']} completed and {result['failed']} failed items",
            "cleared": result
        }

    except Exception as e:
        logger.error(f"Failed to clear queue items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear queue items: {str(e)}"
        )


@router.post("/process-now")
async def process_now(
    request: ProcessNowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Manually trigger processing of documents from Paperless.

    Fetches recent unprocessed documents from Paperless and queues them for AI processing.
    Automatically resets queue stats if the queue is empty.
    """
    from app.services.paperless import get_paperless_client

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
            await paperless.close()
            return {
                "message": "No documents found in Paperless",
                "queued": 0,
                "total_found": 0,
                "already_processed": 0,
                "already_queued": 0,
                "queue_was_reset": False
            }

        # Get repositories
        doc_repo = DocumentRepository(db)
        queue_repo = QueueRepository(db)

        # Filter out already processed documents
        pending_doc_ids = []
        already_processed = 0

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

            pending_doc_ids.append(paperless_id)

        await paperless.close()

        # If no pending documents found, don't reset the queue
        if not pending_doc_ids:
            logger.info(f"No pending documents to queue for user {current_user.username}")
            return {
                "message": "No pending documents found. All documents have already been processed.",
                "queued": 0,
                "total_found": len(documents),
                "already_processed": already_processed,
                "already_queued": 0,
                "queue_was_reset": False
            }

        # Add documents to queue with automatic reset logic
        result = await queue_repo.add_documents_to_queue_with_reset(
            user_id=current_user.id,
            paperless_document_ids=pending_doc_ids,
            priority=0
        )

        logger.info(
            f"Queued {result['added']} documents for processing (user: {current_user.username}). "
            f"Queue was reset: {result['queue_was_reset']}"
        )

        # Build response message
        if result["added"] == 0:
            message = "No new documents queued. All pending documents are already in the queue."
        elif result["queue_was_reset"]:
            message = (
                f"Queue was reset (cleared {result['cleared']['total']} old items). "
                f"Successfully queued {result['added']} new documents for processing."
            )
        else:
            message = f"Successfully queued {result['added']} documents for processing."

        return {
            "message": message,
            "queued": result["added"],
            "total_found": len(documents),
            "already_processed": already_processed,
            "already_queued": result["already_queued"],
            "queue_was_reset": result["queue_was_reset"],
            "cleared": result["cleared"] if result["queue_was_reset"] else None
        }

    except Exception as e:
        logger.error(f"Failed to queue documents for processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch or queue documents: {str(e)}"
        )
