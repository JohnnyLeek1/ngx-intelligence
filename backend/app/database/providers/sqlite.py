"""
SQLite database provider implementation.

Provides SQLite-specific database operations and optimizations.
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.core.logging import get_logger
from app.database.base import DatabaseProvider


logger = get_logger(__name__)


class SQLiteProvider(DatabaseProvider):
    """
    SQLite database provider.

    Implements database operations specific to SQLite with optimizations
    for async operations using aiosqlite.
    """

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """
        Initialize SQLite provider.

        Args:
            database_url: SQLite database URL (sqlite+aiosqlite:///path/to/db)
            echo: Whether to log SQL statements
        """
        self.database_url = database_url
        self.echo = echo
        self._engine: Optional[AsyncEngine] = None
        self._session: Optional[AsyncSession] = None

    async def connect(self) -> None:
        """Establish database connection and enable SQLite optimizations."""
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            connect_args={
                "check_same_thread": False,  # Allow async operations
            },
        )

        # Enable SQLite optimizations
        async with self._engine.begin() as conn:
            # Enable foreign keys
            await conn.execute("PRAGMA foreign_keys = ON")
            # Use WAL mode for better concurrency
            await conn.execute("PRAGMA journal_mode = WAL")
            # Increase cache size (in KB)
            await conn.execute("PRAGMA cache_size = -64000")
            # Use synchronous mode for better performance
            await conn.execute("PRAGMA synchronous = NORMAL")

        logger.info(f"SQLite provider connected: {self.database_url}")

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        logger.info("SQLite provider disconnected")

    async def begin_transaction(self) -> None:
        """Begin a database transaction."""
        if self._session is None:
            raise RuntimeError("No active session for transaction")
        await self._session.begin()

    async def commit(self) -> None:
        """Commit current transaction."""
        if self._session is None:
            raise RuntimeError("No active session to commit")
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback current transaction."""
        if self._session is None:
            raise RuntimeError("No active session to rollback")
        await self._session.rollback()

    async def execute_raw(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
        if self._engine is None:
            raise RuntimeError("Database not connected")

        async with self._engine.begin() as conn:
            if params:
                result = await conn.execute(query, params)
            else:
                result = await conn.execute(query)
            return result

    async def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if database is accessible
        """
        if self._engine is None:
            return False

        try:
            async with self._engine.begin() as conn:
                await conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            return False

    async def vacuum(self) -> None:
        """
        Run VACUUM to reclaim space and optimize database.

        This should be run periodically for SQLite databases.
        """
        if self._engine is None:
            raise RuntimeError("Database not connected")

        async with self._engine.begin() as conn:
            await conn.execute("VACUUM")
            logger.info("SQLite VACUUM completed")

    async def analyze(self) -> None:
        """
        Update query optimizer statistics.

        This helps SQLite choose better query plans.
        """
        if self._engine is None:
            raise RuntimeError("Database not connected")

        async with self._engine.begin() as conn:
            await conn.execute("ANALYZE")
            logger.info("SQLite ANALYZE completed")
