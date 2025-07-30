"""Snowflake database connector implementation."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

import snowflake.connector
from snowflake.connector import DictCursor

from models import DatabaseType, TableSchema, ColumnSchema
from .base import BaseDatabaseConnector, ConnectionConfig

logger = logging.getLogger(__name__)


class SnowflakeConnector(BaseDatabaseConnector):
    """Snowflake database connector with connection pooling."""

    def __init__(self, config: ConnectionConfig):
        if config.database_type != DatabaseType.SNOWFLAKE:
            raise ValueError("Config must be for Snowflake database")
        super().__init__(config)
        self._pool: Optional[List[snowflake.connector.SnowflakeConnection]] = None
        self._available_connections: Optional[asyncio.Queue] = None
        self._executor = ThreadPoolExecutor(max_workers=config.max_connections)

    async def _create_pool(self) -> List[snowflake.connector.SnowflakeConnection]:
        """Create Snowflake connection pool."""
        try:
            # Build connection parameters
            connection_kwargs = {
                "account": self.config.options.get("account", self.config.host),
                "user": self.config.username,
                "password": self.config.password,
                "database": self.config.database,
                "warehouse": self.config.options.get("warehouse"),
                "schema": self.config.options.get("schema", "PUBLIC"),
                "role": self.config.options.get("role"),
            }

            # Remove None values
            connection_kwargs = {
                k: v for k, v in connection_kwargs.items() if v is not None
            }

            # Create connection pool
            pool = []
            self._available_connections = asyncio.Queue(
                maxsize=self.config.max_connections
            )

            for i in range(self.config.min_connections):
                conn = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    lambda: snowflake.connector.connect(**connection_kwargs),
                )
                pool.append(conn)
                await self._available_connections.put(conn)

            logger.info(
                f"Snowflake pool created with {self.config.min_connections} initial connections"
            )
            return pool

        except Exception as e:
            logger.error(f"Failed to create Snowflake pool: {e}")
            raise

    async def _close_pool(self) -> None:
        """Close Snowflake connection pool."""
        if self._pool:
            for conn in self._pool:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        self._executor, conn.close
                    )
                except Exception as e:
                    logger.warning(f"Error closing Snowflake connection: {e}")

            self._pool = None
            self._available_connections = None
            logger.info("Snowflake pool closed")

    @asynccontextmanager
    async def _get_connection(
        self,
    ) -> AsyncGenerator[snowflake.connector.SnowflakeConnection, None]:
        """Get connection from Snowflake pool."""
        if not self._available_connections:
            raise RuntimeError("Connection pool not initialized")

        # Get connection from pool
        connection = await self._available_connections.get()

        try:
            # Check if connection is still valid
            await asyncio.get_event_loop().run_in_executor(
                self._executor, lambda: connection.cursor().execute("SELECT 1")
            )
            yield connection
        except Exception as e:
            logger.error(f"Snowflake connection error: {e}")
            # Try to create a new connection to replace the broken one
            try:
                connection = await self._create_new_connection()
            except Exception:
                logger.error("Failed to create replacement connection")
            raise e
        finally:
            # Return connection to pool
            await self._available_connections.put(connection)

    async def _create_new_connection(self) -> snowflake.connector.SnowflakeConnection:
        """Create a new Snowflake connection."""
        connection_kwargs = {
            "account": self.config.options.get("account", self.config.host),
            "user": self.config.username,
            "password": self.config.password,
            "database": self.config.database,
            "warehouse": self.config.options.get("warehouse"),
            "schema": self.config.options.get("schema", "PUBLIC"),
            "role": self.config.options.get("role"),
        }

        # Remove None values
        connection_kwargs = {
            k: v for k, v in connection_kwargs.items() if v is not None
        }

        return await asyncio.get_event_loop().run_in_executor(
            self._executor, lambda: snowflake.connector.connect(**connection_kwargs)
        )

    async def _execute_query(
        self,
        connection: snowflake.connector.SnowflakeConnection,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute query on Snowflake connection."""
        try:

            def _execute():
                cursor = connection.cursor(DictCursor)
                try:
                    if params:
                        # Snowflake uses %(name)s format for named parameters
                        formatted_sql = sql
                        for key in params.keys():
                            formatted_sql = formatted_sql.replace(
                                f":{key}", f"%({key})s"
                            )

                        cursor.execute(formatted_sql, params)
                    else:
                        cursor.execute(sql)

                    return cursor.fetchall()
                finally:
                    cursor.close()

            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, _execute
            )

            return result or []

        except Exception as e:
            logger.error(f"Snowflake query execution failed: {e}")
            raise

    async def _explain_query(
        self, connection: snowflake.connector.SnowflakeConnection, sql: str
    ) -> str:
        """Get Snowflake query execution plan."""
        try:

            def _explain():
                cursor = connection.cursor(DictCursor)
                try:
                    explain_sql = f"EXPLAIN {sql}"
                    cursor.execute(explain_sql)
                    rows = cursor.fetchall()

                    if not rows:
                        return "No execution plan available"

                    # Format the output
                    output = []
                    for row in rows:
                        if isinstance(row, dict):
                            # Extract relevant information from the explain plan
                            step = row.get("step", "")
                            operation = row.get("operation", "")
                            objects = row.get("objects", "")

                            parts = []
                            if step:
                                parts.append(f"Step: {step}")
                            if operation:
                                parts.append(f"Operation: {operation}")
                            if objects:
                                parts.append(f"Objects: {objects}")

                            if parts:
                                output.append(" | ".join(parts))
                            else:
                                output.append(str(row))
                        else:
                            output.append(str(row))

                    return "\n".join(output)
                finally:
                    cursor.close()

            return await asyncio.get_event_loop().run_in_executor(
                self._executor, _explain
            )

        except Exception as e:
            logger.error(f"Failed to get Snowflake execution plan: {e}")
            raise

    async def _get_table_metadata(
        self, connection: snowflake.connector.SnowflakeConnection, table_name: str
    ) -> TableSchema:
        """Get Snowflake table metadata."""
        try:

            def _get_metadata():
                cursor = connection.cursor(DictCursor)
                try:
                    # Get table information
                    table_query = """
                        SELECT
                            TABLE_NAME,
                            TABLE_TYPE,
                            COMMENT as TABLE_COMMENT,
                            ROW_COUNT
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE UPPER(TABLE_NAME) = UPPER(%s)
                        AND TABLE_SCHEMA = CURRENT_SCHEMA()
                    """

                    cursor.execute(table_query, (table_name,))
                    table_info = cursor.fetchone()

                    if not table_info:
                        raise ValueError(f"Table '{table_name}' not found")

                    # Get column information
                    columns_query = """
                        SELECT
                            COLUMN_NAME,
                            DATA_TYPE,
                            IS_NULLABLE,
                            COLUMN_DEFAULT,
                            COMMENT as COLUMN_COMMENT
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE UPPER(TABLE_NAME) = UPPER(%s)
                        AND TABLE_SCHEMA = CURRENT_SCHEMA()
                        ORDER BY ORDINAL_POSITION
                    """

                    cursor.execute(columns_query, (table_name,))
                    column_rows = cursor.fetchall()

                    # Get primary key information
                    pk_query = """
                        SELECT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                        WHERE UPPER(tc.TABLE_NAME) = UPPER(%s)
                        AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                        AND tc.TABLE_SCHEMA = CURRENT_SCHEMA()
                    """

                    cursor.execute(pk_query, (table_name,))
                    pk_columns = {row["COLUMN_NAME"] for row in cursor.fetchall()}

                    return table_info, column_rows, pk_columns
                finally:
                    cursor.close()

            (
                table_info,
                column_rows,
                pk_columns,
            ) = await asyncio.get_event_loop().run_in_executor(
                self._executor, _get_metadata
            )

            columns = []
            for row in column_rows:
                # Get sample values for low-cardinality columns
                sample_values = await self._get_sample_values(
                    connection, table_name, row["COLUMN_NAME"]
                )

                column = ColumnSchema(
                    name=row["COLUMN_NAME"],
                    data_type=row["DATA_TYPE"].lower(),
                    description=(
                        row["COLUMN_COMMENT"] if row["COLUMN_COMMENT"] else None
                    ),
                    sample_values=sample_values,
                    is_nullable=row["IS_NULLABLE"] == "YES",
                    is_primary_key=row["COLUMN_NAME"] in pk_columns,
                    is_foreign_key=False,  # Would need additional query for FK detection
                )
                columns.append(column)

            return TableSchema(
                name=table_name,
                database_id=self.config.database,  # Using database name as ID for now
                columns=columns,
                description=(
                    table_info["TABLE_COMMENT"] if table_info["TABLE_COMMENT"] else None
                ),
                row_count=table_info["ROW_COUNT"],
            )

        except Exception as e:
            logger.error(
                f"Failed to get Snowflake table metadata for {table_name}: {e}"
            )
            raise

    async def _get_sample_values(
        self,
        connection: snowflake.connector.SnowflakeConnection,
        table_name: str,
        column_name: str,
        limit: int = 10,
    ) -> List[Any]:
        """Get sample values for a column."""
        try:

            def _get_samples():
                cursor = connection.cursor(DictCursor)
                try:
                    # Check if column has low cardinality (< 100 distinct values)
                    distinct_query = f"""
                        SELECT COUNT(DISTINCT "{column_name}") as DISTINCT_COUNT
                        FROM "{table_name}"
                    """
                    cursor.execute(distinct_query)
                    result = cursor.fetchone()
                    distinct_count = result["DISTINCT_COUNT"] if result else 0

                    if distinct_count and distinct_count < 100:
                        # Get sample values for low-cardinality columns
                        sample_query = f"""
                            SELECT DISTINCT "{column_name}"
                            FROM "{table_name}"
                            WHERE "{column_name}" IS NOT NULL
                            ORDER BY "{column_name}"
                            LIMIT {limit}
                        """
                        cursor.execute(sample_query)
                        rows = cursor.fetchall()
                        return [row[column_name] for row in rows]

                    return []
                finally:
                    cursor.close()

            return await asyncio.get_event_loop().run_in_executor(
                self._executor, _get_samples
            )

        except Exception as e:
            logger.warning(
                f"Failed to get sample values for {table_name}.{column_name}: {e}"
            )
            return []

    async def _list_tables(
        self, connection: snowflake.connector.SnowflakeConnection
    ) -> List[str]:
        """List all Snowflake tables."""
        try:

            def _list():
                cursor = connection.cursor(DictCursor)
                try:
                    query = """
                        SELECT TABLE_NAME
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
                        AND TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_NAME
                    """

                    cursor.execute(query)
                    rows = cursor.fetchall()
                    return [row["TABLE_NAME"] for row in rows]
                finally:
                    cursor.close()

            return await asyncio.get_event_loop().run_in_executor(self._executor, _list)

        except Exception as e:
            logger.error(f"Failed to list Snowflake tables: {e}")
            raise

    async def _health_check_query(
        self, connection: snowflake.connector.SnowflakeConnection
    ) -> None:
        """Execute Snowflake health check query."""

        def _health_check():
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT 1")
            finally:
                cursor.close()

        await asyncio.get_event_loop().run_in_executor(self._executor, _health_check)
