"""
Base repository implementation using SQLAlchemy.

Provides concrete implementation of BaseRepository interface.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import BaseRepository
from app.database.models import Base


T = TypeVar("T", bound=Base)


class SQLAlchemyRepository(BaseRepository[T], Generic[T]):
    """
    SQLAlchemy-based repository implementation.

    Provides CRUD operations for any SQLAlchemy model.
    """

    def __init__(self, model: Type[T], session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session

    async def create(self, entity: T) -> T:
        """Create a new entity."""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Retrieve an entity by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, entity_ids: List[UUID]) -> List[T]:
        """Retrieve multiple entities by IDs."""
        result = await self.session.execute(
            select(self.model).where(self.model.id.in_(entity_ids))
        )
        return list(result.scalars().all())

    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID."""
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return False

        await self.session.delete(entity)
        await self.session.commit()
        return True

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """List entities with optional filtering and pagination."""
        query = select(self.model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if isinstance(value, list):
                        query = query.where(column.in_(value))
                    else:
                        query = query.where(column == value)

        # Apply ordering
        if order_by:
            desc = order_by.startswith("-")
            field = order_by.lstrip("-")
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                query = query.order_by(column.desc() if desc else column.asc())

        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        query = select(func.count()).select_from(self.model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if isinstance(value, list):
                        query = query.where(column.in_(value))
                    else:
                        query = query.where(column == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if an entity exists matching filters."""
        count = await self.count(filters)
        return count > 0
