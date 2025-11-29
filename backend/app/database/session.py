"""
Database session management and dependency injection.

Provides async database sessions and connection lifecycle management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.core.logging import get_logger
from app.database.models import Base


logger = get_logger(__name__)


class DatabaseSessionManager:
    """
    Manages database engine and session creation.

    Provides centralized database connection management with
    proper lifecycle handling.
    """

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

    def init(self, database_url: str, echo: bool = False) -> None:
        """
        Initialize database engine and session factory.

        Args:
            database_url: Database connection URL
            echo: Whether to log SQL statements
        """
        # SQLite doesn't support connection pooling parameters
        engine_args = {
            "echo": echo,
        }

        # Only add pooling parameters for databases that support them (PostgreSQL, MySQL)
        if not database_url.startswith("sqlite"):
            engine_args.update({
                "pool_pre_ping": True,  # Verify connections before using
                "pool_size": 5,
                "max_overflow": 10,
            })

        self._engine = create_async_engine(database_url, **engine_args)

        self._sessionmaker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info(f"Database engine initialized: {database_url.split('@')[-1]}")

    async def close(self) -> None:
        """Close database engine and cleanup resources."""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None
        logger.info("Database engine closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a new database session.

        Yields:
            AsyncSession instance

        Raises:
            Exception: If session manager not initialized
        """
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager not initialized")

        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_all(self) -> None:
        """Create all database tables."""
        if self._engine is None:
            raise Exception("DatabaseSessionManager not initialized")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")

    async def drop_all(self) -> None:
        """Drop all database tables. Use with caution!"""
        if self._engine is None:
            raise Exception("DatabaseSessionManager not initialized")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("Database tables dropped")

    async def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is accessible, False otherwise
        """
        if self._engine is None:
            return False

        try:
            async with self._sessionmaker() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global session manager instance
sessionmanager = DatabaseSessionManager()


def init_db() -> None:
    """Initialize database with settings from configuration."""
    settings = get_settings()
    sessionmanager.init(
        database_url=settings.database.url,
        echo=settings.database.echo,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Yields:
        AsyncSession instance for use in endpoint handlers

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with sessionmanager.session() as session:
        yield session


async def get_db_context():
    """
    Get database session context manager.

    Returns:
        Async context manager for database session

    Example:
        async with get_db_context() as db:
            result = await db.execute(...)
    """
    return sessionmanager.session()
