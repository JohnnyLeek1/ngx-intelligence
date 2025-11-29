"""
Integration tests for database operations.

Tests database session management, transactions, and concurrent access.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, ProcessedDocument, ProcessingStatus, UserRole
from app.core.security import hash_password


@pytest.mark.asyncio
class TestDatabaseSession:
    """Test database session management."""

    async def test_session_commit(self, db_session: AsyncSession):
        """Test that changes are committed to database."""
        user = User(
            username="commituser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )

        db_session.add(user)
        await db_session.commit()

        # Verify user was persisted
        result = await db_session.execute(select(User).where(User.username == "commituser"))
        retrieved_user = result.scalar_one_or_none()

        assert retrieved_user is not None
        assert retrieved_user.username == "commituser"

    async def test_session_rollback(self, db_session: AsyncSession):
        """Test that rollback discards changes."""
        user = User(
            username="rollbackuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )

        db_session.add(user)
        await db_session.flush()  # Make user available in session

        # Rollback before commit
        await db_session.rollback()

        # Verify user was not persisted
        result = await db_session.execute(select(User).where(User.username == "rollbackuser"))
        retrieved_user = result.scalar_one_or_none()

        assert retrieved_user is None

    async def test_transaction_isolation(self, db_session: AsyncSession):
        """Test transaction isolation."""
        user = User(
            username="isolationuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )

        db_session.add(user)
        await db_session.commit()

        # Update user
        user.email = "updated@example.com"
        await db_session.commit()

        # Verify update
        result = await db_session.execute(select(User).where(User.username == "isolationuser"))
        retrieved_user = result.scalar_one_or_none()

        assert retrieved_user.email == "updated@example.com"


@pytest.mark.asyncio
class TestDatabaseRelationships:
    """Test database model relationships."""

    async def test_user_documents_relationship(self, db_session: AsyncSession):
        """Test User -> ProcessedDocument relationship."""
        # Create user
        user = User(
            username="docowner",
            password_hash=hash_password("Password123!"),
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        db_session.add(user)
        await db_session.flush()

        # Create documents for user
        for i in range(3):
            doc = ProcessedDocument(
                user_id=user.id,
                paperless_document_id=100 + i,
                status=ProcessingStatus.SUCCESS,
            )
            db_session.add(doc)

        await db_session.commit()

        # Refresh user to load relationships
        await db_session.refresh(user, ["processed_documents"])

        assert len(user.processed_documents) == 3

    async def test_cascade_delete(self, db_session: AsyncSession):
        """Test cascade delete of related records."""
        # Create user with document
        user = User(
            username="cascadeuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        db_session.add(user)
        await db_session.flush()

        doc = ProcessedDocument(
            user_id=user.id,
            paperless_document_id=999,
            status=ProcessingStatus.SUCCESS,
        )
        db_session.add(doc)
        await db_session.commit()

        # Delete user (should cascade to documents)
        await db_session.delete(user)
        await db_session.commit()

        # Verify document was also deleted
        result = await db_session.execute(
            select(ProcessedDocument).where(ProcessedDocument.paperless_document_id == 999)
        )
        deleted_doc = result.scalar_one_or_none()

        assert deleted_doc is None


@pytest.mark.asyncio
class TestDatabaseConstraints:
    """Test database constraints and validation."""

    async def test_unique_username_constraint(self, db_session: AsyncSession):
        """Test that duplicate usernames are rejected."""
        user1 = User(
            username="uniqueuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://test.local",
            paperless_username="user1",
            paperless_token="token1",
        )
        db_session.add(user1)
        await db_session.commit()

        # Try to create another user with same username
        user2 = User(
            username="uniqueuser",  # Duplicate
            password_hash=hash_password("Password123!"),
            paperless_url="http://test.local",
            paperless_username="user2",
            paperless_token="token2",
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()

    async def test_enum_validation(self, db_session: AsyncSession):
        """Test enum field validation."""
        user = User(
            username="enumuser",
            password_hash=hash_password("Password123!"),
            role=UserRole.ADMIN,  # Valid enum value
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        db_session.add(user)
        await db_session.commit()

        result = await db_session.execute(select(User).where(User.username == "enumuser"))
        retrieved_user = result.scalar_one_or_none()

        assert retrieved_user.role == UserRole.ADMIN
