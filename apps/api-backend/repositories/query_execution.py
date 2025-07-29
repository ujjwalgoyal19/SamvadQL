"""Query execution log repository implementation."""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass, field
import uuid

from repositories.base import BaseRepository


@dataclass
class QueryExecutionLog:
    """Query execution log entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str = ""
    user_id: str = ""
    original_query: str = ""
    generated_sql: str = ""
    schema_versions: Dict[str, str] = field(default_factory=dict)
    execution_timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_result: Optional[str] = None
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class QueryExecutionRepository(BaseRepository[QueryExecutionLog]):
    """Repository for query execution log operations."""

    def get_table_name(self) -> str:
        return "query_execution_log"

    def to_dict(self, entity: QueryExecutionLog) -> Dict[str, Any]:
        """Convert QueryExecutionLog to dictionary."""
        return {
            "id": entity.id,
            "query_id": entity.query_id,
            "user_id": entity.user_id,
            "original_query": entity.original_query,
            "generated_sql": entity.generated_sql,
            "schema_versions": entity.schema_versions,
            "execution_timestamp": entity.execution_timestamp,
            "execution_result": entity.execution_result,
            "error_message": entity.error_message,
            "performance_metrics": entity.performance_metrics,
        }

    def from_dict(self, data: Dict[str, Any]) -> QueryExecutionLog:
        """Convert dictionary to QueryExecutionLog."""
        return QueryExecutionLog(
            id=str(data["id"]),
            query_id=str(data["query_id"]),
            user_id=data["user_id"],
            original_query=data["original_query"],
            generated_sql=data["generated_sql"],
            schema_versions=data.get("schema_versions", {}),
            execution_timestamp=data["execution_timestamp"],
            execution_result=data.get("execution_result"),
            error_message=data.get("error_message"),
            performance_metrics=data.get("performance_metrics", {}),
        )

    async def log_query_execution(
        self,
        query_id: str,
        user_id: str,
        original_query: str,
        generated_sql: str,
        schema_versions: Dict[str, str],
        execution_result: Optional[str] = None,
        error_message: Optional[str] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
    ) -> QueryExecutionLog:
        """Log a query execution."""
        entry = QueryExecutionLog(
            query_id=query_id,
            user_id=user_id,
            original_query=original_query,
            generated_sql=generated_sql,
            schema_versions=schema_versions,
            execution_result=execution_result,
            error_message=error_message,
            performance_metrics=performance_metrics or {},
        )
        return await self.create(entry)

    async def get_by_user_id(
        self,
        user_id: str,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[QueryExecutionLog]:
        """Get query execution logs by user ID."""
        db_manager = await self.get_db_manager()

        where_conditions = ["user_id = $1"]

        params: List[Union[str, datetime]] = [user_id]

        if start_date:
            where_conditions.append(f"execution_timestamp >= ${len(params) + 1}")
            params.append(start_date)

        if end_date:
            where_conditions.append(f"execution_timestamp <= ${len(params) + 1}")
            params.append(end_date)

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(where_conditions)}
            ORDER BY execution_timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                return [self.from_dict(dict(row)) for row in rows]
        except Exception as e:
            raise Exception(f"Error getting query logs by user ID: {e}")

    async def get_by_query_id(self, query_id: str) -> List[QueryExecutionLog]:
        """Get query execution logs by query ID."""
        return await self.find_by(
            filters={"query_id": query_id}, order_by="execution_timestamp DESC"
        )

    async def get_failed_queries(
        self,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[QueryExecutionLog]:
        """Get failed query executions."""
        db_manager = await self.get_db_manager()

        where_conditions = ["error_message IS NOT NULL"]
        params = []

        if start_date:
            where_conditions.append(f"execution_timestamp >= ${len(params) + 1}")
            params.append(start_date)

        if end_date:
            where_conditions.append(f"execution_timestamp <= ${len(params) + 1}")
            params.append(end_date)

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(where_conditions)}
            ORDER BY execution_timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                return [self.from_dict(dict(row)) for row in rows]
        except Exception as e:
            raise Exception(f"Error getting failed queries: {e}")

    async def get_performance_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get query performance statistics."""
        db_manager = await self.get_db_manager()

        where_clause = ""
        params = []

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append(f"execution_timestamp >= ${len(params) + 1}")
                params.append(start_date)
            if end_date:
                conditions.append(f"execution_timestamp <= ${len(params) + 1}")
                params.append(end_date)
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                COUNT(*) as total_queries,
                COUNT(CASE WHEN error_message IS NULL THEN 1 END) as successful_queries,
                COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as failed_queries,
                AVG(CASE WHEN performance_metrics->>'execution_time_ms' IS NOT NULL
                    THEN (performance_metrics->>'execution_time_ms')::float END) as avg_execution_time_ms,
                COUNT(DISTINCT user_id) as unique_users
            FROM {self.table_name}
            {where_clause}
        """

        try:
            async with db_manager.get_connection() as connection:
                row = await connection.fetchrow(query, *params)
                if not row:
                    return {}
                return {
                    "total_queries": row["total_queries"],
                    "successful_queries": row["successful_queries"],
                    "failed_queries": row["failed_queries"],
                    "success_rate": (
                        (row["successful_queries"] / row["total_queries"] * 100)
                        if row["total_queries"] > 0
                        else 0
                    ),
                    "avg_execution_time_ms": (
                        float(row["avg_execution_time_ms"])
                        if row["avg_execution_time_ms"]
                        else None
                    ),
                    "unique_users": row["unique_users"],
                }
        except Exception as e:
            raise Exception(f"Error getting performance stats: {e}")

    async def get_schema_usage_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get schema version usage statistics."""
        db_manager = await self.get_db_manager()

        where_clause = ""
        params = []

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append(f"execution_timestamp >= ${len(params) + 1}")
                params.append(start_date)
            if end_date:
                conditions.append(f"execution_timestamp <= ${len(params) + 1}")
                params.append(end_date)
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                jsonb_object_keys(schema_versions) as table_name,
                schema_versions->>jsonb_object_keys(schema_versions) as schema_version,
                COUNT(*) as usage_count
            FROM {self.table_name}
            {where_clause}
            GROUP BY table_name, schema_version
            ORDER BY usage_count DESC
        """

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                return [
                    {
                        "table_name": row["table_name"],
                        "schema_version": row["schema_version"],
                        "usage_count": row["usage_count"],
                    }
                    for row in rows
                ]
        except Exception as e:
            raise Exception(f"Error getting schema usage stats: {e}")
