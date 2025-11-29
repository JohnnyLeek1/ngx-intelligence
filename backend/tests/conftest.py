"""
Pytest configuration and fixtures for testing.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.database.models import Base, User, UserRole
from app.database.session import get_db
from app.main import create_app


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Yields:
        AsyncSession instance for testing
    """
    # Create test engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database override.

    Args:
        db_session: Test database session

    Yields:
        AsyncClient for testing API endpoints
    """
    # Create app
    app = create_app()

    # Override database dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create client
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings() -> Settings:
    """
    Get test settings.

    Returns:
        Settings instance for testing
    """
    return Settings(
        app={"name": "test", "debug": True, "log_level": "DEBUG", "secret_key": "test-secret-key"},
        database={"provider": "sqlite", "name": ":memory:"},
    )


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """
    Create a test user.

    Args:
        db_session: Test database session

    Returns:
        Created test user
    """
    from app.core.security import hash_password
    from app.repositories import UserRepository

    user_repo = UserRepository(db_session)
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.USER,
        paperless_url="http://paperless.local",
        paperless_username="testuser",
        paperless_token="test-token-123",
    )
    created_user = await user_repo.create(user)
    return created_user


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """
    Create a test admin user.

    Args:
        db_session: Test database session

    Returns:
        Created admin user
    """
    from app.core.security import hash_password
    from app.repositories import UserRepository

    user_repo = UserRepository(db_session)
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("AdminPassword123!"),
        role=UserRole.ADMIN,
        paperless_url="http://paperless.local",
        paperless_username="admin",
        paperless_token="admin-token-123",
    )
    created_admin = await user_repo.create(admin)
    return created_admin


@pytest.fixture
def access_token(test_user):
    """
    Create access token for test user.

    Args:
        test_user: Test user fixture

    Returns:
        JWT access token
    """
    from app.core.security import create_access_token

    return create_access_token(subject=str(test_user.id))


@pytest.fixture
def auth_headers(access_token):
    """
    Create authentication headers.

    Args:
        access_token: Access token fixture

    Returns:
        Dict with authorization header
    """
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_paperless_client():
    """
    Mock Paperless API client.

    Returns:
        Mock client with common methods
    """
    from unittest.mock import AsyncMock, MagicMock

    mock_client = MagicMock()
    mock_client.health_check = AsyncMock(return_value=True)
    mock_client.get_documents = AsyncMock(return_value=[])
    mock_client.get_document = AsyncMock(return_value={"id": 1, "title": "Test"})
    mock_client.update_document = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    return mock_client


@pytest.fixture
def mock_ollama_provider():
    """
    Mock Ollama AI provider.

    Returns:
        Mock provider with common methods
    """
    from unittest.mock import AsyncMock, MagicMock

    mock_provider = MagicMock()
    mock_provider.generate_text = AsyncMock(return_value="Generated text")
    mock_provider.generate_json = AsyncMock(
        return_value={
            "document_type": "Invoice",
            "confidence": 0.95,
            "tags": ["invoice", "business"],
        }
    )
    mock_provider.list_models = AsyncMock(return_value=["llama3.2", "mixtral"])

    return mock_provider
