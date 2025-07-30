"""Repository for versioned schema management."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from models.versioned_schema import VersionedTableSchema, SchemaChange, SchemaComparison
from .base import BaseRepository

logger = logging.getLogger(__name__)


class VersionedSchemaRepository(BaseRepository[VersionedTableSchema]):
    """Repository for managing versioned table schemas."""

    def get_table_name(self) -> str:
        return "versioned_table_schemas"

    def to_dict(self, entity: VersionedTableSchema) -> Dict[str, Any]:
        """Convert versioned schema entity to dictionary for database storage."""
        # Generate schema hash if not present
        schema_hash = entity.schema_hash or entity.generate_schema_hash()

        return {
            "id": str(uuid4()),
            "database_id": entity.database_id,
            "table_name": entity.name,
            "version": entity.version,
            "parent_version": entity.parent_version,
            "is_active": entity.is_active,
            "schema_content": json.dumps(
                {
                    "name": entity.name,
                    "database_id": entity.database_id,
                    "columns": [col.model_dump() for col in entity.columns],
                    "description": entity.description,
                    "sample_queries": entity.sample_queries,
                    "tier": entity.tier,
                    "tags": entity.tags,
                    "row_count": entity.row_count,
                }
            ),
            "schema_hash": schema_hash,
            "description": entity.description,
            "tier": entity.tier,
            "tags": entity.tags,
            "row_count": entity.row_count,
            "change_reason": entity.change_reason,
            "changed_by": entity.changed_by,
            "created_at": entity.created_at,
        }

    def from_dict(self, data: Dict[str, Any]) -> VersionedTableSchema:
        """Convert dictionary from database to versioned schema entity."""
        schema_content = (
            json.loads(data["schema_content"]) if data["schema_content"] else {}
        )

        # Import here to avoid circular imports
        from models.column import ColumnSchema

        columns = [ColumnSchema(**col) for col in schema_content.get("columns", [])]

        return VersionedTableSchema(
            name=data["table_name"],
            database_id=data["database_id"],
            columns=columns,
            description=data.get("description"),
            version=data["version"],
            created_at=data["created_at"],
            parent_version=data.get("parent_version"),
            is_active=data.get("is_active", True),
            sample_queries=schema_content.get("sample_queries", []),
            tier=data.get("tier"),
            tags=data.get("tags", []),
            row_count=data.get("row_count"),
            change_reason=data.get("change_reason"),
            changed_by=data.get("changed_by"),
            schema_hash=data.get("schema_hash"),
        )

    async def create_version(
        self, schema: VersionedTableSchema, deactivate_previous: bool = True
    ) -> VersionedTableSchema:
        """Create a new schema version."""
        try:
            # Deactivate previous active version if requested
            if deactivate_previous:
                await self._deactivate_previous_versions(
                    schema.database_id, schema.name
                )

            # Create the new version
            created_schema = await self.create(schema)

            logger.info(
                f"Created schema version {schema.version} for table {schema.name} "
                f"in database {schema.database_id}"
            )

            return created_schema

        except Exception as e:
            logger.error(f"Failed to create schema version: {e}")
            raise

    async def get_active_version(
        self, database_id: str, table_name: str
    ) -> Optional[VersionedTableSchema]:
        """Get the currently active version of a table schema."""
        try:
            results = await self.find_by(
                {
                    "database_id": database_id,
                    "table_name": table_name,
                    "is_active": True,
                },
                limit=1,
                order_by="created_at DESC",
            )

            return results[0] if results else None

        except Exception as e:
            logger.error(f"Failed to get active version for table {table_name}: {e}")
            return None

    async def get_version(
        self, database_id: str, table_name: str, version: str
    ) -> Optional[VersionedTableSchema]:
        """Get a specific version of a table schema."""
        try:
            results = await self.find_by(
                {
                    "database_id": database_id,
                    "table_name": table_name,
                    "version": version,
                },
                limit=1,
            )

            return results[0] if results else None

        except Exception as e:
            logger.error(f"Failed to get version {version} for table {table_name}: {e}")
            return None

    async def get_version_history(
        self, database_id: str, table_name: str, limit: int = 50
    ) -> List[VersionedTableSchema]:
        """Get version history for a table."""
        try:
            return await self.find_by(
                {"database_id": database_id, "table_name": table_name},
                limit=limit,
                order_by="created_at DESC",
            )

        except Exception as e:
            logger.error(f"Failed to get version history for table {table_name}: {e}")
            return []

    async def get_schema_at_time(
        self, database_id: str, table_name: str, timestamp: datetime
    ) -> Optional[VersionedTableSchema]:
        """Get the schema as it existed at a specific time."""
        try:
            query = """
                SELECT * FROM versioned_table_schemas
                WHERE database_id = $1 AND table_name = $2 AND created_at <= $3
                ORDER BY created_at DESC
                LIMIT 1
            """

            results = await self.execute_raw_query(
                query, [database_id, table_name, timestamp]
            )

            if results:
                return self.from_dict(results[0])

            return None

        except Exception as e:
            logger.error(
                f"Failed to get schema at time {timestamp} for table {table_name}: {e}"
            )
            return None

    async def find_by_hash(self, schema_hash: str) -> List[VersionedTableSchema]:
        """Find schemas with matching hash."""
        try:
            return await self.find_by({"schema_hash": schema_hash})

        except Exception as e:
            logger.error(f"Failed to find schemas by hash {schema_hash}: {e}")
            return []

    async def get_database_versions(
        self, database_id: str, active_only: bool = False
    ) -> List[VersionedTableSchema]:
        """Get all schema versions for a database."""
        try:
            filters = {"database_id": database_id}
            if active_only:
                filters["is_active"] = True

            return await self.find_by(filters, order_by="table_name, created_at DESC")

        except Exception as e:
            logger.error(f"Failed to get database versions for {database_id}: {e}")
            return []

    async def _deactivate_previous_versions(
        self, database_id: str, table_name: str
    ) -> None:
        """Deactivate all previous versions of a table."""
        try:
            query = """
                UPDATE versioned_table_schemas
                SET is_active = FALSE
                WHERE database_id = $1 AND table_name = $2 AND is_active = TRUE
            """

            await self.execute_raw_query(query, [database_id, table_name])

            logger.debug(
                f"Deactivated previous versions for table {table_name} "
                f"in database {database_id}"
            )

        except Exception as e:
            logger.warning(f"Failed to deactivate previous versions: {e}")

    async def cleanup_old_versions(
        self, database_id: str, keep_versions: int = 10
    ) -> int:
        """Clean up old schema versions, keeping only the most recent ones."""
        try:
            # Get tables with more than keep_versions versions
            query = """
                WITH version_counts AS (
                    SELECT database_id, table_name, COUNT(*) as version_count
                    FROM versioned_table_schemas
                    WHERE database_id = $1
                    GROUP BY database_id, table_name
                    HAVING COUNT(*) > $2
                ),
                versions_to_delete AS (
                    SELECT v.id
                    FROM versioned_table_schemas v
                    JOIN version_counts vc ON v.database_id = vc.database_id
                                           AND v.table_name = vc.table_name
                    WHERE v.is_active = FALSE
                    AND v.id NOT IN (
                        SELECT id FROM versioned_table_schemas v2
                        WHERE v2.database_id = v.database_id
                        AND v2.table_name = v.table_name
                        ORDER BY v2.created_at DESC
                        LIMIT $2
                    )
                )
                DELETE FROM versioned_table_schemas
                WHERE id IN (SELECT id FROM versions_to_delete)
                RETURNING id
            """

            deleted_results = await self.execute_raw_query(
                query, [database_id, keep_versions]
            )

            deleted_count = len(deleted_results)

            if deleted_count > 0:
                logger.info(
                    f"Cleaned up {deleted_count} old schema versions "
                    f"for database {database_id}"
                )

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old versions: {e}")
            return 0


class SchemaChangeRepository(BaseRepository[Dict]):
    """Repository for managing schema change records."""

    def get_table_name(self) -> str:
        return "schema_changes"

    def to_dict(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema change entity to dictionary for database storage."""
        return {
            "id": entity.get("id", str(uuid4())),
            "database_id": entity["database_id"],
            "table_name": entity["table_name"],
            "from_version": entity.get("from_version"),
            "to_version": entity["to_version"],
            "change_type": entity["change_type"],
            "object_type": entity["object_type"],
            "object_name": entity["object_name"],
            "old_value": (
                json.dumps(entity.get("old_value")) if entity.get("old_value") else None
            ),
            "new_value": (
                json.dumps(entity.get("new_value")) if entity.get("new_value") else None
            ),
            "description": entity["description"],
            "detected_at": entity.get("detected_at", datetime.utcnow()),
            "created_by": entity.get("created_by"),
        }

    def from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dictionary from database to schema change entity."""
        return {
            "id": data["id"],
            "database_id": data["database_id"],
            "table_name": data["table_name"],
            "from_version": data.get("from_version"),
            "to_version": data["to_version"],
            "change_type": data["change_type"],
            "object_type": data["object_type"],
            "object_name": data["object_name"],
            "old_value": (
                json.loads(data["old_value"]) if data.get("old_value") else None
            ),
            "new_value": (
                json.loads(data["new_value"]) if data.get("new_value") else None
            ),
            "description": data["description"],
            "detected_at": data["detected_at"],
            "created_by": data.get("created_by"),
        }

    async def get_changes_between_versions(
        self, database_id: str, table_name: str, from_version: str, to_version: str
    ) -> List[SchemaChange]:
        """Get changes between two specific versions."""
        try:
            results = await self.find_by(
                {
                    "database_id": database_id,
                    "table_name": table_name,
                    "from_version": from_version,
                    "to_version": to_version,
                },
                order_by="detected_at",
            )

            changes = []
            for result in results:
                changes.append(
                    SchemaChange(
                        change_type=result["change_type"],
                        object_type=result["object_type"],
                        object_name=result["object_name"],
                        old_value=result.get("old_value"),
                        new_value=result.get("new_value"),
                        description=result["description"],
                    )
                )

            return changes

        except Exception as e:
            logger.error(
                f"Failed to get changes between versions {from_version} and {to_version}: {e}"
            )
            return []

    async def get_table_change_history(
        self, database_id: str, table_name: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get change history for a table."""
        try:
            return await self.find_by(
                {"database_id": database_id, "table_name": table_name},
                limit=limit,
                order_by="detected_at DESC",
            )

        except Exception as e:
            logger.error(f"Failed to get change history for table {table_name}: {e}")
            return []
