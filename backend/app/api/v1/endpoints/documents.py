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
    DocumentFilterRequest,
    DocumentReprocessRequest,
    DocumentStatsResponse,
    ProcessedDocumentResponse,
)


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/filter")
async def filter_documents(
    filters: DocumentFilterRequest,
    current_user: User = Depends(get_current_user),
    doc_repo: DocumentRepository = Depends(get_document_repository),
) -> dict:
    """
    Filter processed documents for current user.

    Supports filtering by:
    - status: Document processing status
    - start_date/end_date: Date range filter
    - min_confidence: Minimum confidence score
    - search: Search by document title (case-insensitive partial match)
    - limit/offset: Pagination
    """
    documents = await doc_repo.filter_documents(
        user_id=current_user.id,
        status=filters.status,
        start_date=filters.start_date,
        end_date=filters.end_date,
        min_confidence=filters.min_confidence,
        search=filters.search,
        limit=filters.limit,
        offset=filters.offset,
    )

    # Get total count without pagination
    total_documents = await doc_repo.filter_documents(
        user_id=current_user.id,
        status=filters.status,
        start_date=filters.start_date,
        end_date=filters.end_date,
        min_confidence=filters.min_confidence,
        search=filters.search,
        limit=None,
        offset=None,
    )

    # Convert SQLAlchemy models to Pydantic schemas
    documents_response = [ProcessedDocumentResponse.model_validate(doc) for doc in documents]

    return {
        "documents": documents_response,
        "total": len(total_documents)
    }


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
