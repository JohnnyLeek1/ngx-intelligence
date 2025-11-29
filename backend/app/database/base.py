"""
Abstract database interfaces and base repository pattern.

Provides provider-agnostic database operations following the repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar
from uuid import UUID


# Generic type for entity models
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository defining CRUD operations.

    This interface must be implemented by all repository classes
    to ensure consistent data access patterns across the application.
    """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID populated
        """
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Retrieve an entity by ID.

        Args:
            entity_id: Entity UUID

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_ids(self, entity_ids: List[UUID]) -> List[T]:
        """
        Retrieve multiple entities by IDs.

        Args:
            entity_ids: List of entity UUIDs

        Returns:
            List of found entities
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: Entity with updated values

        Returns:
            Updated entity
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: Entity UUID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """
        List entities with optional filtering and pagination.

        Args:
            filters: Dictionary of field filters
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field to order by (prefix with - for descending)

        Returns:
            List of entities matching criteria
        """
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Dictionary of field filters

        Returns:
            Count of matching entities
        """
        pass

    @abstractmethod
    async def exists(self, filters: Dict[str, Any]) -> bool:
        """
        Check if an entity exists matching filters.

        Args:
            filters: Dictionary of field filters

        Returns:
            True if at least one matching entity exists
        """
        pass


class DatabaseProvider(ABC):
    """
    Abstract database provider interface.

    Defines connection management and transaction operations
    that must be implemented by specific database providers.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish database connection.

        Raises:
            Exception: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close database connection.
        """
        pass

    @abstractmethod
    async def begin_transaction(self) -> None:
        """
        Begin a database transaction.
        """
        pass

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit current transaction.
        """
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback current transaction.
        """
        pass

    @abstractmethod
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if database is accessible
        """
        pass


class UnitOfWork(Protocol):
    """
    Unit of Work pattern for coordinating repository operations.

    Ensures that all operations within a transaction are atomic.
    """

    async def __aenter__(self) -> "UnitOfWork":
        """Enter async context manager."""
        ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        ...

    async def commit(self) -> None:
        """Commit all changes made within this unit of work."""
        ...

    async def rollback(self) -> None:
        """Rollback all changes made within this unit of work."""
        ...
