"""
Document API endpoints.

Handles document listing, reprocessing, and statistics.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.models import User
from app.dependencies import get_current_user, get_document_repository
from app.repositories import DocumentRepository
from app.schemas import (
    DocumentReprocessRequest,
    DocumentStatsResponse,
    ProcessedDocumentResponse,
)


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=List[ProcessedDocumentResponse])
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    doc_repo: DocumentRepository = Depends(get_document_repository),
) -> List[ProcessedDocumentResponse]:
    """List processed documents for current user."""
    documents = await doc_repo.get_user_documents(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return documents


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    doc_repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentStatsResponse:
    """Get processing statistics for current user."""
    stats = await doc_repo.get_processing_stats(current_user.id)
    return DocumentStatsResponse(**stats)


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Reprocess a single document (stub)."""
    # TODO: Implement reprocessing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Reprocessing not yet implemented",
    )
