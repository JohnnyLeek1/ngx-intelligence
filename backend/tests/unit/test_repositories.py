"""
Unit tests for repository layer.

Tests CRUD operations, filtering, pagination, and custom repository methods.
"""

import pytest
from uuid import uuid4

from app.database.models import User, ProcessedDocument, ProcessingQueue, UserRole, QueueStatus, ProcessingStatus
from app.repositories import UserRepository, DocumentRepository, QueueRepository


@pytest.mark.asyncio
class TestUserRepository:
    """Test UserRepository operations."""

    async def test_create_user(self, db_session):
        """Test creating a new user."""
        repo = UserRepository(db_session)

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.USER,
            paperless_url="http://paperless.local",
            paperless_username="testuser",
            paperless_token="token123",
        )

        created_user = await repo.create(user)

        assert created_user.id is not None
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"
        assert created_user.is_active is True

    async def test_get_user_by_id(self, db_session):
        """Test retrieving user by ID."""
        repo = UserRepository(db_session)

        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await repo.create(user)

        retrieved_user = await repo.get_by_id(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == "testuser"

    async def test_get_user_by_username(self, db_session):
        """Test retrieving user by username."""
        repo = UserRepository(db_session)

        user = User(
            username="uniqueuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        await repo.create(user)

        retrieved_user = await repo.get_by_username("uniqueuser")

        assert retrieved_user is not None
        assert retrieved_user.username == "uniqueuser"

    async def test_get_user_by_email(self, db_session):
        """Test retrieving user by email."""
        repo = UserRepository(db_session)

        user = User(
            username="testuser",
            email="unique@example.com",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        await repo.create(user)

        retrieved_user = await repo.get_by_email("unique@example.com")

        assert retrieved_user is not None
        assert retrieved_user.email == "unique@example.com"

    async def test_username_exists(self, db_session):
        """Test checking if username exists."""
        repo = UserRepository(db_session)

        user = User(
            username="existinguser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        await repo.create(user)

        assert await repo.username_exists("existinguser") is True
        assert await repo.username_exists("nonexistent") is False

    async def test_email_exists(self, db_session):
        """Test checking if email exists."""
        repo = UserRepository(db_session)

        user = User(
            username="testuser",
            email="existing@example.com",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        await repo.create(user)

        assert await repo.email_exists("existing@example.com") is True
        assert await repo.email_exists("nonexistent@example.com") is False

    async def test_get_active_users(self, db_session):
        """Test retrieving only active users."""
        repo = UserRepository(db_session)

        # Create active user
        active_user = User(
            username="active",
            password_hash="hashed",
            is_active=True,
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        await repo.create(active_user)

        # Create inactive user
        inactive_user = User(
            username="inactive",
            password_hash="hashed",
            is_active=False,
            paperless_url="http://test.local",
            paperless_username="user2",
            paperless_token="token2",
        )
        await repo.create(inactive_user)

        active_users = await repo.get_active_users()

        assert len(active_users) == 1
        assert active_users[0].username == "active"

    async def test_get_admins(self, db_session):
        """Test retrieving admin users."""
        repo = UserRepository(db_session)

        # Create admin user
        admin = User(
            username="admin",
            password_hash="hashed",
            role=UserRole.ADMIN,
            paperless_url="http://test.local",
            paperless_username="admin",
            paperless_token="token",
        )
        await repo.create(admin)

        # Create regular user
        user = User(
            username="user",
            password_hash="hashed",
            role=UserRole.USER,
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token2",
        )
        await repo.create(user)

        admins = await repo.get_admins()

        assert len(admins) == 1
        assert admins[0].username == "admin"
        assert admins[0].role == UserRole.ADMIN

    async def test_update_user(self, db_session):
        """Test updating user."""
        repo = UserRepository(db_session)

        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await repo.create(user)

        created_user.email = "updated@example.com"
        updated_user = await repo.update(created_user)

        assert updated_user.email == "updated@example.com"

    async def test_delete_user(self, db_session):
        """Test deleting user."""
        repo = UserRepository(db_session)

        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await repo.create(user)

        await repo.delete(created_user.id)

        deleted_user = await repo.get_by_id(created_user.id)
        assert deleted_user is None


@pytest.mark.asyncio
class TestDocumentRepository:
    """Test DocumentRepository operations."""

    async def test_create_document(self, db_session):
        """Test creating processed document."""
        from app.repositories.document import DocumentRepository

        # First create a user
        user_repo = UserRepository(db_session)
        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        # Create document
        doc_repo = DocumentRepository(db_session)
        document = ProcessedDocument(
            user_id=created_user.id,
            paperless_document_id=123,
            status=ProcessingStatus.SUCCESS,
            confidence_score=0.95,
        )

        created_doc = await doc_repo.create(document)

        assert created_doc.id is not None
        assert created_doc.paperless_document_id == 123
        assert created_doc.status == ProcessingStatus.SUCCESS

    async def test_get_by_paperless_id(self, db_session):
        """Test retrieving document by Paperless ID."""
        from app.repositories.document import DocumentRepository

        user_repo = UserRepository(db_session)
        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        doc_repo = DocumentRepository(db_session)
        document = ProcessedDocument(
            user_id=created_user.id,
            paperless_document_id=456,
            status=ProcessingStatus.SUCCESS,
        )
        await doc_repo.create(document)

        retrieved_doc = await doc_repo.get_by_paperless_id(
            created_user.id, 456
        )

        assert retrieved_doc is not None
        assert retrieved_doc.paperless_document_id == 456

    async def test_list_with_pagination(self, db_session):
        """Test listing documents with pagination."""
        from app.repositories.document import DocumentRepository

        user_repo = UserRepository(db_session)
        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        doc_repo = DocumentRepository(db_session)

        # Create multiple documents
        for i in range(5):
            document = ProcessedDocument(
                user_id=created_user.id,
                paperless_document_id=100 + i,
                status=ProcessingStatus.SUCCESS,
            )
            await doc_repo.create(document)

        # Test pagination
        docs = await doc_repo.list_by_user(created_user.id, skip=0, limit=3)

        assert len(docs) == 3


@pytest.mark.asyncio
class TestQueueRepository:
    """Test QueueRepository operations."""

    async def test_create_queue_item(self, db_session):
        """Test creating queue item."""
        from app.repositories.queue import QueueRepository

        user_repo = UserRepository(db_session)
        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        queue_repo = QueueRepository(db_session)
        queue_item = ProcessingQueue(
            user_id=created_user.id,
            paperless_document_id=789,
            status=QueueStatus.QUEUED,
            priority=1,
        )

        created_item = await queue_repo.create(queue_item)

        assert created_item.id is not None
        assert created_item.paperless_document_id == 789
        assert created_item.status == QueueStatus.QUEUED

    async def test_get_next_item(self, db_session):
        """Test retrieving next queue item by priority."""
        from app.repositories.queue import QueueRepository

        user_repo = UserRepository(db_session)
        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        queue_repo = QueueRepository(db_session)

        # Create items with different priorities
        low_priority = ProcessingQueue(
            user_id=created_user.id,
            paperless_document_id=1,
            status=QueueStatus.QUEUED,
            priority=1,
        )
        await queue_repo.create(low_priority)

        high_priority = ProcessingQueue(
            user_id=created_user.id,
            paperless_document_id=2,
            status=QueueStatus.QUEUED,
            priority=10,
        )
        await queue_repo.create(high_priority)

        # Should get high priority item first
        next_item = await queue_repo.get_next(created_user.id)

        assert next_item is not None
        assert next_item.paperless_document_id == 2
        assert next_item.priority == 10

    async def test_count_queued(self, db_session):
        """Test counting queued items."""
        from app.repositories.queue import QueueRepository

        user_repo = UserRepository(db_session)
        user = User(
            username="testuser",
            password_hash="hashed",
            paperless_url="http://test.local",
            paperless_username="user",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        queue_repo = QueueRepository(db_session)

        # Create queued items
        for i in range(3):
            item = ProcessingQueue(
                user_id=created_user.id,
                paperless_document_id=100 + i,
                status=QueueStatus.QUEUED,
            )
            await queue_repo.create(item)

        # Create processing item
        processing_item = ProcessingQueue(
            user_id=created_user.id,
            paperless_document_id=200,
            status=QueueStatus.PROCESSING,
        )
        await queue_repo.create(processing_item)

        count = await queue_repo.count_queued(created_user.id)

        assert count == 3
