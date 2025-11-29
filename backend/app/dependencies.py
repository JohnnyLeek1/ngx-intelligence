"""
FastAPI dependencies for dependency injection.

Provides reusable dependencies for authentication, database access, and services.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import verify_token
from app.database.models import User
from app.database.session import get_db
from app.repositories import (
    ApprovalRepository,
    DocumentRepository,
    QueueRepository,
    UserRepository,
)
from app.services.ai.base import BaseLLMProvider
from app.services.ai.ollama import get_ollama_provider
from app.services.paperless import PaperlessClient, get_paperless_client


# Security
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Get current user ID from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User UUID

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    user_id_str = verify_token(token, token_type="access")

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current user from database.

    Args:
        user_id: User UUID from token
        db: Database session

    Returns:
        User instance

    Raises:
        HTTPException: If user not found or inactive
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify admin role.

    Args:
        current_user: Current user from token

    Returns:
        User instance

    Raises:
        HTTPException: If user is not an admin
    """
    from app.database.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return current_user


# Repositories
async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


async def get_document_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    """Get document repository instance."""
    return DocumentRepository(db)


async def get_queue_repository(
    db: AsyncSession = Depends(get_db),
) -> QueueRepository:
    """Get queue repository instance."""
    return QueueRepository(db)


async def get_approval_repository(
    db: AsyncSession = Depends(get_db),
) -> ApprovalRepository:
    """Get approval repository instance."""
    return ApprovalRepository(db)


# Services
async def get_ai_provider() -> BaseLLMProvider:
    """
    Get AI provider instance based on configuration.

    Returns:
        AI provider instance
    """
    settings = get_settings()

    if settings.ai.provider == "ollama":
        return await get_ollama_provider(
            base_url=settings.ai.ollama.base_url,
            model=settings.ai.ollama.model,
            timeout=settings.ai.ollama.timeout,
            max_retries=settings.ai.ollama.max_retries,
        )
    else:
        raise ValueError(f"Unsupported AI provider: {settings.ai.provider}")


async def get_user_paperless_client(
    current_user: User = Depends(get_current_user),
) -> PaperlessClient:
    """
    Get Paperless client for current user.

    Args:
        current_user: Current user

    Returns:
        PaperlessClient instance configured for user
    """
    return await get_paperless_client(
        base_url=current_user.paperless_url,
        auth_token=current_user.paperless_token,
    )
