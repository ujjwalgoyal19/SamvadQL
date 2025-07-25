import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import asyncpg
from asyncpg import Pool

from .config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections with connection pooling."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: Optional[Pool] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        async with self._lock:
            if self._pool is None:
                try:
                    self._pool = await asyncpg.create_pool(
                        host=self.config.host,
                        port=self.config.port,
                        database=self.config.database,
                        user=self.config.username,
                        password=self.config.password,
                        min_size=self.config.min_connections,
                        max_size=self.config.max_connections,
                        command_timeout=self.config.command_timeout,
                    )
                    logger.info(
                        f"Database pool initialized with {self.config.min_connections}-{self.config.max_connections} connections"
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize database pool: {e}")
                    raise

    async def close(self) -> None:
        """Close the connection pool."""
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None
                logger.info("Database pool closed")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a database connection from the pool."""
        if not self._pool:
            await self.initialize()
        if not self._pool:
            raise RuntimeError("Failed to initialize database pool")

        async with self._pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                raise

    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a database connection with transaction."""
        async with self.get_connection() as connection:
            async with connection.transaction():
                yield connection

    async def execute_query(
        self, query: str, *args, fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute a query and optionally fetch results."""
        async with self.get_connection() as connection:
            if fetch:
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
            else:
                await connection.execute(query, *args)
                return None

    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """Execute a query multiple times with different parameters."""
        async with self.get_connection() as connection:
            await connection.executemany(query, args_list)

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            async with self.get_connection() as connection:
                await connection.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
