"""
Integration tests for API endpoints.

Tests authentication, document management, and queue management endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.database.models import User, UserRole, ProcessedDocument, ProcessingStatus
from app.core.security import hash_password, create_access_token
from app.repositories import UserRepository


@pytest.mark.asyncio
class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        with patch("app.api.v1.endpoints.auth.get_paperless_client") as mock_client_factory:
            # Mock Paperless client
            mock_client = AsyncMock()
            mock_client.health_check = AsyncMock(return_value=True)
            mock_client.close = AsyncMock()
            mock_client_factory.return_value = mock_client

            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "newuser",
                    "password": "SecurePass123!",
                    "email": "newuser@example.com",
                    "paperless_url": "http://paperless.local",
                    "paperless_username": "newuser",
                    "paperless_token": "test-token-123",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["username"] == "newuser"
            assert data["email"] == "newuser@example.com"
            assert "password" not in data
            assert "paperless_token" not in data

    async def test_register_duplicate_username(self, client: AsyncClient, db_session):
        """Test registration with duplicate username."""
        # Create existing user
        user_repo = UserRepository(db_session)
        existing_user = User(
            username="existinguser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="existing",
            paperless_token="token",
        )
        await user_repo.create(existing_user)

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "existinguser",
                "password": "SecurePass123!",
                "email": "new@example.com",
                "paperless_url": "http://paperless.local",
                "paperless_username": "newuser",
                "paperless_token": "test-token",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_register_invalid_password(self, client: AsyncClient):
        """Test registration with invalid password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "weak",  # Too weak
                "email": "test@example.com",
                "paperless_url": "http://paperless.local",
                "paperless_username": "testuser",
                "paperless_token": "test-token",
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_login_success(self, client: AsyncClient, db_session):
        """Test successful login."""
        # Create user
        user_repo = UserRepository(db_session)
        user = User(
            username="loginuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="loginuser",
            paperless_token="token",
        )
        await user_repo.create(user)

        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "loginuser", "password": "Password123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient, db_session):
        """Test login with invalid credentials."""
        # Create user
        user_repo = UserRepository(db_session)
        user = User(
            username="testuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="testuser",
            paperless_token="token",
        )
        await user_repo.create(user)

        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "WrongPassword!"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "Password123!"},
        )

        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, db_session):
        """Test token refresh."""
        # Create user
        user_repo = UserRepository(db_session)
        user = User(
            username="refreshuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="refreshuser",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        # Create refresh token
        from app.core.security import create_refresh_token

        refresh_token = create_refresh_token(subject=str(created_user.id))

        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid-token"}
        )

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, db_session):
        """Test getting current user info."""
        # Create user
        user_repo = UserRepository(db_session)
        user = User(
            username="currentuser",
            email="current@example.com",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="currentuser",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        # Create access token
        token = create_access_token(subject=str(created_user.id))

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["email"] == "current@example.com"

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


@pytest.mark.asyncio
class TestDocumentEndpoints:
    """Test document management API endpoints."""

    async def test_list_documents_authenticated(self, client: AsyncClient, db_session):
        """Test listing documents with authentication."""
        # Create user
        user_repo = UserRepository(db_session)
        user = User(
            username="docuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="docuser",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        # Create some documents
        from app.repositories.document import DocumentRepository

        doc_repo = DocumentRepository(db_session)
        for i in range(3):
            doc = ProcessedDocument(
                user_id=created_user.id,
                paperless_document_id=100 + i,
                status=ProcessingStatus.SUCCESS,
            )
            await doc_repo.create(doc)

        # Get documents
        token = create_access_token(subject=str(created_user.id))
        response = await client.get(
            "/api/v1/documents", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 3

    async def test_list_documents_unauthorized(self, client: AsyncClient):
        """Test listing documents without authentication."""
        response = await client.get("/api/v1/documents")

        assert response.status_code == 401

    async def test_get_document_by_id(self, client: AsyncClient, db_session):
        """Test getting a specific document."""
        # Create user and document
        user_repo = UserRepository(db_session)
        user = User(
            username="docuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="docuser",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        from app.repositories.document import DocumentRepository

        doc_repo = DocumentRepository(db_session)
        doc = ProcessedDocument(
            user_id=created_user.id,
            paperless_document_id=123,
            status=ProcessingStatus.SUCCESS,
            confidence_score=0.95,
        )
        created_doc = await doc_repo.create(doc)

        # Get document
        token = create_access_token(subject=str(created_user.id))
        response = await client.get(
            f"/api/v1/documents/{created_doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["paperless_document_id"] == 123
        assert data["confidence_score"] == 0.95

    async def test_get_document_not_found(self, client: AsyncClient, db_session):
        """Test getting nonexistent document."""
        user_repo = UserRepository(db_session)
        user = User(
            username="docuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="docuser",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        from uuid import uuid4

        token = create_access_token(subject=str(created_user.id))
        response = await client.get(
            f"/api/v1/documents/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestQueueEndpoints:
    """Test queue management API endpoints."""

    async def test_get_queue_status(self, client: AsyncClient, db_session):
        """Test getting queue status."""
        # Create user
        user_repo = UserRepository(db_session)
        user = User(
            username="queueuser",
            password_hash=hash_password("Password123!"),
            paperless_url="http://paperless.local",
            paperless_username="queueuser",
            paperless_token="token",
        )
        created_user = await user_repo.create(user)

        # Create queue items
        from app.repositories.queue import QueueRepository
        from app.database.models import ProcessingQueue, QueueStatus

        queue_repo = QueueRepository(db_session)
        for i in range(2):
            item = ProcessingQueue(
                user_id=created_user.id,
                paperless_document_id=200 + i,
                status=QueueStatus.QUEUED,
            )
            await queue_repo.create(item)

        # Get queue status
        token = create_access_token(subject=str(created_user.id))
        response = await client.get(
            "/api/v1/queue", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 0

    async def test_queue_unauthorized(self, client: AsyncClient):
        """Test queue access without authentication."""
        response = await client.get("/api/v1/queue")

        assert response.status_code == 401
