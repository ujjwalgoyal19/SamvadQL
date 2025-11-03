"""Abstract base class for database connectors."""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from models import DatabaseType, TableSchema, ColumnSchema

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of database health check."""

    is_healthy: bool
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class ConnectionConfig(BaseModel):
    """Database connection configuration."""

    database_type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str

    # Connection pool settings
    min_connections: int = Field(default=5, ge=1, le=50)
    max_connections: int = Field(default=20, ge=1, le=100)
    connection_timeout: int = Field(default=30, ge=5, le=300)
    command_timeout: int = Field(default=60, ge=10, le=600)

    # Additional connection parameters
    ssl_mode: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None

    # Database-specific options
    options: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_url(cls, url: str, database_type: DatabaseType) -> "ConnectionConfig":
        """Create configuration from database URL."""
        parsed = urlparse(url)

        return cls(
            database_type=database_type,
            host=parsed.hostname or "localhost",
            port=parsed.port or cls._get_default_port(database_type),
            database=parsed.path.lstrip("/") if parsed.path else "",
            username=parsed.username or "",
            password=parsed.password or "",
        )

    @staticmethod
    def _get_default_port(database_type: DatabaseType) -> int:
        """Get default port for database type."""
        defaults = {
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MYSQL: 3306,
            DatabaseType.SNOWFLAKE: 443,
            DatabaseType.BIGQUERY: 443,
        }
        return defaults.get(database_type, 5432)


class BaseDatabaseConnector(ABC):
    """Abstract base class for database connectors."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._pool = None
        self._lock = asyncio.Lock()
        self._is_connected = False

    @property
    def database_type(self) -> DatabaseType:
        """Get database type."""
        return self.config.database_type

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._is_connected

    @abstractmethod
    async def _create_pool(self) -> Any:
        """Create database connection pool. Implementation specific."""
        pass

    @abstractmethod
    async def _close_pool(self) -> None:
        """Close database connection pool. Implementation specific."""
        pass

    @abstractmethod
    async def _get_connection(self) -> AsyncGenerator[Any, None]:
        """Get connection from pool. Implementation specific."""
        pass

    @abstractmethod
    async def _execute_query(
        self, connection: Any, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on connection. Implementation specific."""
        pass

    @abstractmethod
    async def _explain_query(self, connection: Any, sql: str) -> str:
        """Get query execution plan. Implementation specific."""
        pass

    @abstractmethod
    async def _get_table_metadata(
        self, connection: Any, table_name: str
    ) -> TableSchema:
        """Get table metadata. Implementation specific."""
        pass

    @abstractmethod
    async def _list_tables(self, connection: Any) -> List[str]:
        """List all tables. Implementation specific."""
        pass

    @abstractmethod
    async def _health_check_query(self, connection: Any) -> None:
        """Execute health check query. Implementation specific."""
        pass

    async def connect(self) -> None:
        """Establish database connection pool."""
        async with self._lock:
            if self._is_connected:
                return

            try:
                logger.info(
                    f"Connecting to {self.database_type.value} database at {self.config.host}:{self.config.port}"
                )
                self._pool = await self._create_pool()
                self._is_connected = True
                logger.info(
                    f"Successfully connected to {self.database_type.value} database"
                )

                # Perform initial health check
                health_result = await self.health_check()
                if not health_result.is_healthy:
                    raise ConnectionError(
                        f"Initial health check failed: {health_result.error_message}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to connect to {self.database_type.value} database: {e}"
                )
                self._is_connected = False
                if self._pool:
                    await self._close_pool()
                    self._pool = None
                raise

    async def disconnect(self) -> None:
        """Close database connection pool."""
        async with self._lock:
            if not self._is_connected:
                return

            try:
                logger.info(f"Disconnecting from {self.database_type.value} database")
                if self._pool:
                    await self._close_pool()
                    self._pool = None
                self._is_connected = False
                logger.info(
                    f"Successfully disconnected from {self.database_type.value} database"
                )
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
                raise

    async def execute_query(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        if not self._is_connected:
            await self.connect()

        async with self._get_connection() as connection:
            try:
                logger.debug(f"Executing query: {sql[:100]}...")
                start_time = asyncio.get_event_loop().time()

                result = await self._execute_query(connection, sql, params)

                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                logger.debug(
                    f"Query executed in {execution_time:.2f}ms, returned {len(result)} rows"
                )

                return result

            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise

    async def explain_query(self, sql: str) -> str:
        """Get query execution plan."""
        if not self._is_connected:
            await self.connect()

        async with self._get_connection() as connection:
            try:
                logger.debug(f"Getting execution plan for query: {sql[:100]}...")
                return await self._explain_query(connection, sql)
            except Exception as e:
                logger.error(f"Failed to get execution plan: {e}")
                raise

    async def get_table_metadata(self, table_name: str) -> TableSchema:
        """Get metadata for a specific table."""
        if not self._is_connected:
            await self.connect()

        async with self._get_connection() as connection:
            try:
                logger.debug(f"Getting metadata for table: {table_name}")
                return await self._get_table_metadata(connection, table_name)
            except Exception as e:
                logger.error(f"Failed to get table metadata for {table_name}: {e}")
                raise

    async def list_tables(self) -> List[str]:
        """List all table names."""
        if not self._is_connected:
            await self.connect()

        async with self._get_connection() as connection:
            try:
                logger.debug("Listing all tables")
                tables = await self._list_tables(connection)
                logger.debug(f"Found {len(tables)} tables")
                return tables
            except Exception as e:
                logger.error(f"Failed to list tables: {e}")
                raise

    async def health_check(self) -> HealthCheckResult:
        """Perform database health check."""
        start_time = asyncio.get_event_loop().time()

        try:
            if not self._is_connected:
                return HealthCheckResult(
                    is_healthy=False,
                    response_time_ms=0,
                    error_message="Not connected to database",
                )

            async with self._get_connection() as connection:
                await self._health_check_query(connection)

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            return HealthCheckResult(is_healthy=True, response_time_ms=response_time)

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"Health check failed: {e}")

            return HealthCheckResult(
                is_healthy=False, response_time_ms=response_time, error_message=str(e)
            )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
