"""PostgreSQL database connector implementation."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import asyncpg
from asyncpg import Pool, Connection

from models import DatabaseType, TableSchema, ColumnSchema
from .base import BaseDatabaseConnector, ConnectionConfig

logger = logging.getLogger(__name__)


class PostgreSQLConnector(BaseDatabaseConnector):
    """PostgreSQL database connector with connection pooling."""

    def __init__(self, config: ConnectionConfig):
        if config.database_type != DatabaseType.POSTGRESQL:
            raise ValueError("Config must be for PostgreSQL database")
        super().__init__(config)
        self._pool: Optional[Pool] = None

    async def _create_pool(self) -> Pool:
        """Create PostgreSQL connection pool."""
        try:
            # Build connection parameters
            connection_kwargs = {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database,
                "user": self.config.username,
                "password": self.config.password,
                "min_size": self.config.min_connections,
                "max_size": self.config.max_connections,
                "command_timeout": self.config.command_timeout,
            }

            # Add SSL configuration if provided
            if self.config.ssl_mode:
                connection_kwargs["ssl"] = self.config.ssl_mode

            # Add any additional options
            connection_kwargs.update(self.config.options)

            pool = await asyncpg.create_pool(**connection_kwargs)
            logger.info(
                f"PostgreSQL pool created with {self.config.min_connections}-{self.config.max_connections} connections"
            )
            return pool

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise

    async def _close_pool(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL pool closed")

    @asynccontextmanager
    async def _get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get connection from PostgreSQL pool."""
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")

        async with self._pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"PostgreSQL connection error: {e}")
                raise

    async def _execute_query(
        self, connection: Connection, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on PostgreSQL connection."""
        try:
            if params:
                # Convert named parameters to positional for asyncpg
                param_values = list(params.values())
                # Replace named placeholders with $1, $2, etc.
                formatted_sql = sql
                for i, key in enumerate(params.keys(), 1):
                    formatted_sql = formatted_sql.replace(f":{key}", f"${i}")

                rows = await connection.fetch(formatted_sql, *param_values)
            else:
                rows = await connection.fetch(sql)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"PostgreSQL query execution failed: {e}")
            raise

    async def _explain_query(self, connection: Connection, sql: str) -> str:
        """Get PostgreSQL query execution plan."""
        try:
            explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"
            result = await connection.fetchval(explain_sql)

            # Extract the plan from JSON result
            if isinstance(result, list) and len(result) > 0:
                plan = result[0]
                return self._format_explain_output(plan)

            return str(result)

        except Exception as e:
            logger.error(f"Failed to get PostgreSQL execution plan: {e}")
            # Fallback to simple EXPLAIN
            try:
                explain_sql = f"EXPLAIN {sql}"
                rows = await connection.fetch(explain_sql)
                return "\n".join([row[0] for row in rows])
            except:
                raise e

    def _format_explain_output(self, plan: Dict[str, Any]) -> str:
        """Format PostgreSQL EXPLAIN output for readability."""
        if "Plan" not in plan:
            return str(plan)

        plan_info = plan["Plan"]
        output = []

        # Basic plan information
        output.append(f"Node Type: {plan_info.get('Node Type', 'Unknown')}")
        output.append(f"Total Cost: {plan_info.get('Total Cost', 'Unknown')}")
        output.append(f"Rows: {plan_info.get('Plan Rows', 'Unknown')}")

        if "Actual Total Time" in plan_info:
            output.append(f"Actual Time: {plan_info['Actual Total Time']:.2f} ms")

        # Add relation name if available
        if "Relation Name" in plan_info:
            output.append(f"Relation: {plan_info['Relation Name']}")

        return "\n".join(output)

    async def _get_table_metadata(
        self, connection: Connection, table_name: str
    ) -> TableSchema:
        """Get PostgreSQL table metadata."""
        try:
            # Get table information
            table_query = """
                SELECT
                    t.table_name,
                    t.table_type,
                    obj_description(c.oid) as table_comment
                FROM information_schema.tables t
                LEFT JOIN pg_class c ON c.relname = t.table_name
                WHERE t.table_name = $1
                AND t.table_schema = 'public'
            """

            table_info = await connection.fetchrow(table_query, table_name)
            if not table_info:
                raise ValueError(f"Table '{table_name}' not found")

            # Get column information
            columns_query = """
                SELECT
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    col_description(pgc.oid, c.ordinal_position) as column_comment,
                    CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
                    CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key
                FROM information_schema.columns c
                LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
                LEFT JOIN (
                    SELECT ku.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
                    WHERE tc.table_name = $1 AND tc.constraint_type = 'PRIMARY KEY'
                ) pk ON pk.column_name = c.column_name
                LEFT JOIN (
                    SELECT ku.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
                    WHERE tc.table_name = $1 AND tc.constraint_type = 'FOREIGN KEY'
                ) fk ON fk.column_name = c.column_name
                WHERE c.table_name = $1
                AND c.table_schema = 'public'
                ORDER BY c.ordinal_position
            """

            column_rows = await connection.fetch(columns_query, table_name)

            columns = []
            for row in column_rows:
                # Get sample values for low-cardinality columns
                sample_values = await self._get_sample_values(
                    connection, table_name, row["column_name"]
                )

                column = ColumnSchema(
                    name=row["column_name"],
                    data_type=row["data_type"],
                    description=row["column_comment"],
                    sample_values=sample_values,
                    is_nullable=row["is_nullable"] == "YES",
                    is_primary_key=row["is_primary_key"],
                    is_foreign_key=row["is_foreign_key"],
                )
                columns.append(column)

            # Get row count
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            row_count = await connection.fetchval(count_query)

            return TableSchema(
                name=table_name,
                database_id=self.config.database,  # Using database name as ID for now
                columns=columns,
                description=table_info["table_comment"],
                row_count=row_count,
            )

        except Exception as e:
            logger.error(
                f"Failed to get PostgreSQL table metadata for {table_name}: {e}"
            )
            raise

    async def _get_sample_values(
        self, connection: Connection, table_name: str, column_name: str, limit: int = 10
    ) -> List[Any]:
        """Get sample values for a column."""
        try:
            # Check if column has low cardinality (< 100 distinct values)
            distinct_query = f"""
                SELECT COUNT(DISTINCT "{column_name}") as distinct_count
                FROM "{table_name}"
            """
            distinct_count = await connection.fetchval(distinct_query)

            if distinct_count and distinct_count < 100:
                # Get sample values for low-cardinality columns
                sample_query = f"""
                    SELECT DISTINCT "{column_name}"
                    FROM "{table_name}"
                    WHERE "{column_name}" IS NOT NULL
                    ORDER BY "{column_name}"
                    LIMIT $1
                """
                rows = await connection.fetch(sample_query, limit)
                return [row[0] for row in rows]

            return []

        except Exception as e:
            logger.warning(
                f"Failed to get sample values for {table_name}.{column_name}: {e}"
            )
            return []

    async def _list_tables(self, connection: Connection) -> List[str]:
        """List all PostgreSQL tables."""
        try:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """

            rows = await connection.fetch(query)
            return [row["table_name"] for row in rows]

        except Exception as e:
            logger.error(f"Failed to list PostgreSQL tables: {e}")
            raise

    async def _health_check_query(self, connection: Connection) -> None:
        """Execute PostgreSQL health check query."""
        await connection.fetchval("SELECT 1")
