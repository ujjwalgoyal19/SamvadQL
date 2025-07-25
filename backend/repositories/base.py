"""Base repository classes with CRUD operations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import UUID
from datetime import datetime

from core.db.pool import DatabaseConnectionManager
from core.db.manager import get_database_manager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository class with common CRUD operations."""

    def __init__(self, db_manager: Optional[DatabaseConnectionManager] = None):
        self._db_manager = db_manager
        self.table_name = self.get_table_name()

    @abstractmethod
    def get_table_name(self) -> str:
        """Return the table name for this repository."""
        pass

    @abstractmethod
    def to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary for database storage."""
        pass

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> T:
        """Convert dictionary from database to entity."""
        pass

    async def get_db_manager(self) -> DatabaseConnectionManager:
        """Get database manager instance."""
        if self._db_manager is None:
            self._db_manager = await get_database_manager()
        return self._db_manager

    async def create(self, entity: T) -> T:
        """Create a new entity in the database."""
        db_manager = await self.get_db_manager()
        data = self.to_dict(entity)

        # Build INSERT query
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(data.values())

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """

        try:
            async with db_manager.get_connection() as connection:
                row = await connection.fetchrow(query, *values)
                if row is None:
                    raise Exception("Failed to create entity: no row returned")
                row_dict = {str(k): v for k, v in dict(row).items()}
                return self.from_dict(row_dict)
        except Exception as e:
            logger.error(f"Error creating entity in {self.table_name}: {e}")
            raise

    async def get_by_id(self, entity_id: Union[str, UUID]) -> Optional[T]:
        """Get entity by ID."""
        db_manager = await self.get_db_manager()

        query = f"SELECT * FROM {self.table_name} WHERE id = $1"

        try:
            async with db_manager.get_connection() as connection:
                row = await connection.fetchrow(query, str(entity_id))
                return self.from_dict(dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error getting entity by ID from {self.table_name}: {e}")
            raise

    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """Get all entities with optional pagination and ordering."""
        db_manager = await self.get_db_manager()

        query = f"SELECT * FROM {self.table_name}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        if offset:
            query += f" OFFSET {offset}"

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query)
                return [self.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all entities from {self.table_name}: {e}")
            raise

    async def update(
        self, entity_id: Union[str, UUID], updates: Dict[str, Any]
    ) -> Optional[T]:
        """Update entity by ID."""
        db_manager = await self.get_db_manager()

        if not updates:
            return await self.get_by_id(entity_id)

        # Add updated_at timestamp only if the column exists in the table
        updates = updates.copy()
        db_manager = await self.get_db_manager()
        async with db_manager.get_connection() as connection:
            columns_query = f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{self.table_name}'
            """
            columns = [
                row["column_name"] for row in await connection.fetch(columns_query)
            ]
        if "updated_at" in columns:
            updates["updated_at"] = datetime.utcnow()

        # Build UPDATE query
        set_clauses = [f"{key} = ${i+2}" for i, key in enumerate(updates.keys())]
        values = [str(entity_id)] + list(updates.values())

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE id = $1
            RETURNING *
        """

        try:
            async with db_manager.get_connection() as connection:
                row = await connection.fetchrow(query, *values)
                return self.from_dict(dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error updating entity in {self.table_name}: {e}")
            raise

    async def delete(self, entity_id: Union[str, UUID]) -> bool:
        """Delete entity by ID."""
        db_manager = await self.get_db_manager()

        query = f"DELETE FROM {self.table_name} WHERE id = $1"

        try:
            async with db_manager.get_connection() as connection:
                result = await connection.execute(query, str(entity_id))
                return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Error deleting entity from {self.table_name}: {e}")
            raise

    async def exists(self, entity_id: Union[str, UUID]) -> bool:
        """Check if entity exists by ID."""
        db_manager = await self.get_db_manager()

        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE id = $1)"

        try:
            async with db_manager.get_connection() as connection:
                result = await connection.fetchval(query, str(entity_id))
                return bool(result) if result is not None else False
        except Exception as e:
            logger.error(f"Error checking entity existence in {self.table_name}: {e}")
            raise

    async def count(
        self, where_clause: Optional[str] = None, params: Optional[List[Any]] = None
    ) -> int:
        """Count entities with optional WHERE clause."""
        db_manager = await self.get_db_manager()

        query = f"SELECT COUNT(*) FROM {self.table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            async with db_manager.get_connection() as connection:
                result = await connection.fetchval(query, *(params or []))
                return result if result is not None else 0
        except Exception as e:
            logger.error(f"Error counting entities in {self.table_name}: {e}")
            raise

    async def find_by(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """Find entities by filters."""
        db_manager = await self.get_db_manager()

        if not filters:
            return await self.get_all(limit=limit, order_by=order_by)

        # Build WHERE clause
        where_clauses = [f"{key} = ${i+1}" for i, key in enumerate(filters.keys())]
        values = list(filters.values())

        query = f"SELECT * FROM {self.table_name} WHERE {' AND '.join(where_clauses)}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *values)
                return [self.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error finding entities in {self.table_name}: {e}")
            raise

    async def execute_raw_query(
        self, query: str, params: Optional[List[Any]] = None, fetch_one: bool = False
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """Execute raw SQL query."""
        db_manager = await self.get_db_manager()

        try:
            async with db_manager.get_connection() as connection:
                if fetch_one:
                    row = await connection.fetchrow(query, *(params or []))
                    return dict(row) if row else None
                else:
                    rows = await connection.fetch(query, *(params or []))
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error executing raw query: {e}")
            raise
