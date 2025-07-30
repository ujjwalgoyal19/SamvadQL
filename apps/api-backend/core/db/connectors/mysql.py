"""MySQL database connector implementation."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiomysql
from aiomysql import Pool, Connection

from models import DatabaseType, TableSchema, ColumnSchema
from .base import BaseDatabaseConnector, ConnectionConfig

logger = logging.getLogger(__name__)


class MySQLConnector(BaseDatabaseConnector):
    """MySQL database connector with connection pooling."""

    def __init__(self, config: ConnectionConfig):
        if config.database_type != DatabaseType.MYSQL:
            raise ValueError("Config must be for MySQL database")
        super().__init__(config)
        self._pool: Optional[Pool] = None

    async def _create_pool(self) -> Pool:
        """Create MySQL connection pool."""
        try:
            # Build connection parameters
            connection_kwargs = {
                "host": self.config.host,
                "port": self.config.port,
                "db": self.config.database,
                "user": self.config.username,
                "password": self.config.password,
                "minsize": self.config.min_connections,
                "maxsize": self.config.max_connections,
                "charset": "utf8mb4",
                "autocommit": True,
            }

            # Add SSL configuration if provided
            if self.config.ssl_mode:
                connection_kwargs["ssl"] = {
                    "ssl_disabled": self.config.ssl_mode == "disable"
                }
                if self.config.ssl_cert:
                    connection_kwargs["ssl"]["cert"] = self.config.ssl_cert
                if self.config.ssl_key:
                    connection_kwargs["ssl"]["key"] = self.config.ssl_key
                if self.config.ssl_ca:
                    connection_kwargs["ssl"]["ca"] = self.config.ssl_ca

            # Add any additional options
            connection_kwargs.update(self.config.options)

            pool = await aiomysql.create_pool(**connection_kwargs)
            logger.info(
                f"MySQL pool created with {self.config.min_connections}-{self.config.max_connections} connections"
            )
            return pool

        except Exception as e:
            logger.error(f"Failed to create MySQL pool: {e}")
            raise

    async def _close_pool(self) -> None:
        """Close MySQL connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            logger.info("MySQL pool closed")

    @asynccontextmanager
    async def _get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get connection from MySQL pool."""
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")

        async with self._pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"MySQL connection error: {e}")
                raise

    async def _execute_query(
        self, connection: Connection, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on MySQL connection."""
        try:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    # Convert named parameters to format expected by aiomysql
                    formatted_sql = sql
                    param_values = []
                    for key, value in params.items():
                        formatted_sql = formatted_sql.replace(f":{key}", "%s")
                        param_values.append(value)

                    await cursor.execute(formatted_sql, param_values)
                else:
                    await cursor.execute(sql)

                result = await cursor.fetchall()
                return result or []

        except Exception as e:
            logger.error(f"MySQL query execution failed: {e}")
            raise

    async def _explain_query(self, connection: Connection, sql: str) -> str:
        """Get MySQL query execution plan."""
        try:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                # Try EXPLAIN FORMAT=JSON first (MySQL 5.6+)
                try:
                    explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
                    await cursor.execute(explain_sql)
                    result = await cursor.fetchone()

                    if result and "EXPLAIN" in result:
                        return self._format_explain_output(result["EXPLAIN"])

                except Exception:
                    # Fallback to regular EXPLAIN
                    pass

                # Regular EXPLAIN
                explain_sql = f"EXPLAIN {sql}"
                await cursor.execute(explain_sql)
                rows = await cursor.fetchall()

                if not rows:
                    return "No execution plan available"

                # Format the output
                output = []
                for row in rows:
                    parts = []
                    if row.get("select_type"):
                        parts.append(f"Type: {row['select_type']}")
                    if row.get("table"):
                        parts.append(f"Table: {row['table']}")
                    if row.get("type"):
                        parts.append(f"Access: {row['type']}")
                    if row.get("rows"):
                        parts.append(f"Rows: {row['rows']}")

                    output.append(" | ".join(parts))

                return "\n".join(output)

        except Exception as e:
            logger.error(f"Failed to get MySQL execution plan: {e}")
            raise

    def _format_explain_output(self, plan: str) -> str:
        """Format MySQL EXPLAIN JSON output for readability."""
        try:
            import json

            plan_data = json.loads(plan) if isinstance(plan, str) else plan

            if "query_block" in plan_data:
                query_block = plan_data["query_block"]
                output = []

                if "select_id" in query_block:
                    output.append(f"Select ID: {query_block['select_id']}")

                if "cost_info" in query_block:
                    cost = query_block["cost_info"]
                    if "query_cost" in cost:
                        output.append(f"Query Cost: {cost['query_cost']}")

                if "table" in query_block:
                    table_info = query_block["table"]
                    if "table_name" in table_info:
                        output.append(f"Table: {table_info['table_name']}")
                    if "access_type" in table_info:
                        output.append(f"Access Type: {table_info['access_type']}")

                return "\n".join(output)

            return str(plan_data)

        except Exception:
            return str(plan)

    async def _get_table_metadata(
        self, connection: Connection, table_name: str
    ) -> TableSchema:
        """Get MySQL table metadata."""
        try:
            # Get table information
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                table_query = """
                    SELECT
                        TABLE_NAME,
                        TABLE_TYPE,
                        TABLE_COMMENT,
                        TABLE_ROWS
                    FROM information_schema.TABLES
                    WHERE TABLE_NAME = %s
                    AND TABLE_SCHEMA = DATABASE()
                """

                await cursor.execute(table_query, (table_name,))
                table_info = await cursor.fetchone()

                if not table_info:
                    raise ValueError(f"Table '{table_name}' not found")

                # Get column information
                columns_query = """
                    SELECT
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.IS_NULLABLE,
                        c.COLUMN_DEFAULT,
                        c.COLUMN_COMMENT,
                        CASE WHEN c.COLUMN_KEY = 'PRI' THEN 1 ELSE 0 END as IS_PRIMARY_KEY,
                        CASE WHEN c.COLUMN_KEY = 'MUL' THEN 1 ELSE 0 END as IS_FOREIGN_KEY
                    FROM information_schema.COLUMNS c
                    WHERE c.TABLE_NAME = %s
                    AND c.TABLE_SCHEMA = DATABASE()
                    ORDER BY c.ORDINAL_POSITION
                """

                await cursor.execute(columns_query, (table_name,))
                column_rows = await cursor.fetchall()

                columns = []
                for row in column_rows:
                    # Get sample values for low-cardinality columns
                    sample_values = await self._get_sample_values(
                        connection, table_name, row["COLUMN_NAME"]
                    )

                    column = ColumnSchema(
                        name=row["COLUMN_NAME"],
                        data_type=row["DATA_TYPE"],
                        description=(
                            row["COLUMN_COMMENT"] if row["COLUMN_COMMENT"] else None
                        ),
                        sample_values=sample_values,
                        is_nullable=row["IS_NULLABLE"] == "YES",
                        is_primary_key=bool(row["IS_PRIMARY_KEY"]),
                        is_foreign_key=bool(row["IS_FOREIGN_KEY"]),
                    )
                    columns.append(column)

                return TableSchema(
                    name=table_name,
                    database_id=self.config.database,  # Using database name as ID for now
                    columns=columns,
                    description=(
                        table_info["TABLE_COMMENT"]
                        if table_info["TABLE_COMMENT"]
                        else None
                    ),
                    row_count=table_info["TABLE_ROWS"],
                )

        except Exception as e:
            logger.error(f"Failed to get MySQL table metadata for {table_name}: {e}")
            raise

    async def _get_sample_values(
        self, connection: Connection, table_name: str, column_name: str, limit: int = 10
    ) -> List[Any]:
        """Get sample values for a column."""
        try:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                # Check if column has low cardinality (< 100 distinct values)
                distinct_query = f"""
                    SELECT COUNT(DISTINCT `{column_name}`) as distinct_count
                    FROM `{table_name}`
                """
                await cursor.execute(distinct_query)
                result = await cursor.fetchone()
                distinct_count = result["distinct_count"] if result else 0

                if distinct_count and distinct_count < 100:
                    # Get sample values for low-cardinality columns
                    sample_query = f"""
                        SELECT DISTINCT `{column_name}`
                        FROM `{table_name}`
                        WHERE `{column_name}` IS NOT NULL
                        ORDER BY `{column_name}`
                        LIMIT %s
                    """
                    await cursor.execute(sample_query, (limit,))
                    rows = await cursor.fetchall()
                    return [row[column_name] for row in rows]

                return []

        except Exception as e:
            logger.warning(
                f"Failed to get sample values for {table_name}.{column_name}: {e}"
            )
            return []

    async def _list_tables(self, connection: Connection) -> List[str]:
        """List all MySQL tables."""
        try:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                query = """
                    SELECT TABLE_NAME
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """

                await cursor.execute(query)
                rows = await cursor.fetchall()
                return [row["TABLE_NAME"] for row in rows]

        except Exception as e:
            logger.error(f"Failed to list MySQL tables: {e}")
            raise

    async def _health_check_query(self, connection: Connection) -> None:
        """Execute MySQL health check query."""
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT 1")
