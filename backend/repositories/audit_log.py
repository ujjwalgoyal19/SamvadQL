"""Audit log repository implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

from models import AuditLogEntry
from repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLogEntry]):
    """Repository for audit log operations."""

    def get_table_name(self) -> str:
        return "audit_log"

    def to_dict(self, entity: AuditLogEntry) -> Dict[str, Any]:
        """Convert AuditLogEntry to dictionary."""
        return {
            "id": entity.id,
            "user_id": entity.user_id,
            "action": entity.action,
            "resource_type": entity.resource_type,
            "resource_id": entity.resource_id,
            "details": entity.details,
            "ip_address": entity.ip_address,
            "user_agent": entity.user_agent,
            "created_at": entity.created_at,
        }

    def from_dict(self, data: Dict[str, Any]) -> AuditLogEntry:
        """Convert dictionary to AuditLogEntry."""
        return AuditLogEntry(
            id=str(data["id"]),
            user_id=data["user_id"],
            action=data["action"],
            resource_type=data["resource_type"],
            resource_id=data.get("resource_id"),
            details=data.get("details", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            created_at=data["created_at"],
        )

    async def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log an audit action."""
        entry = AuditLogEntry(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(entry)

    async def get_by_user_id(
        self,
        user_id: str,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """Get audit logs by user ID with optional date filtering."""
        db_manager = await self.get_db_manager()

        where_conditions = ["user_id = $1"]
        params = [user_id]

        if start_date:
            where_conditions.append(f"created_at >= ${len(params) + 1}")
            params.append(start_date.isoformat())

        if end_date:
            where_conditions.append(f"created_at <= ${len(params) + 1}")
            params.append(end_date.isoformat())

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(where_conditions)}
            ORDER BY created_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                return [self.from_dict(dict(row)) for row in rows]
        except Exception as e:
            raise Exception(f"Error getting audit logs by user ID: {e}")

    async def get_by_resource(
        self, resource_type: str, resource_id: str, limit: Optional[int] = None
    ) -> List[AuditLogEntry]:
        """Get audit logs by resource."""
        return await self.find_by(
            filters={"resource_type": resource_type, "resource_id": resource_id},
            limit=limit,
            order_by="created_at DESC",
        )

    async def get_by_action(
        self,
        action: str,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """Get audit logs by action type."""
        db_manager = await self.get_db_manager()

        where_conditions = ["action = $1"]
        params = [action]

        if start_date:
            where_conditions.append(f"created_at >= ${len(params) + 1}")
            params.append(start_date.isoformat())

        if end_date:
            where_conditions.append(f"created_at <= ${len(params) + 1}")
            params.append(end_date.isoformat())

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(where_conditions)}
            ORDER BY created_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                return [self.from_dict(dict(row)) for row in rows]
        except Exception as e:
            raise Exception(f"Error getting audit logs by action: {e}")

    async def get_activity_summary(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get activity summary statistics."""
        db_manager = await self.get_db_manager()

        where_clause = ""
        params = []

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append(f"created_at >= ${len(params) + 1}")
                params.append(start_date.isoformat())
            if end_date:
                conditions.append(f"created_at <= ${len(params) + 1}")
                params.append(end_date.isoformat())
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                action,
                resource_type,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as unique_users
            FROM {self.table_name}
            {where_clause}
            GROUP BY action, resource_type
            ORDER BY count DESC
        """

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                return [
                    {
                        "action": row["action"],
                        "resource_type": row["resource_type"],
                        "count": row["count"],
                        "unique_users": row["unique_users"],
                    }
                    for row in rows
                ]
        except Exception as e:
            raise Exception(f"Error getting activity summary: {e}")

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old audit logs beyond retention period."""
        db_manager = await self.get_db_manager()

        query = f"""
            DELETE FROM {self.table_name}
            WHERE created_at < NOW() - INTERVAL '{days_to_keep} days'
        """

        try:
            async with db_manager.get_connection() as connection:
                result = await connection.execute(query)
                # Extract number from result like "DELETE 123"
                return int(result.split()[-1]) if result.startswith("DELETE") else 0
        except Exception as e:
            raise Exception(f"Error cleaning up old logs: {e}")
