"""Repository for metadata management."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from models import TableSchema
from .base import BaseRepository

logger = logging.getLogger(__name__)


class MetadataRepository(BaseRepository[Dict]):
    """Repository for managing metadata storage and retrieval."""

    def get_table_name(self) -> str:
        return "metadata_cache"

    def to_dict(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata entity to dictionary for database storage."""
        return {
            "id": entity.get("id", str(uuid4())),
            "database_id": entity["database_id"],
            "table_name": entity.get("table_name"),
            "metadata_type": entity[
                "metadata_type"
            ],  # 'table_list', 'table_metadata', 'sample_data'
            "metadata_content": json.dumps(entity["content"]),
            "database_type": entity.get("database_type"),
            "created_at": entity.get("created_at", datetime.utcnow()),
            "updated_at": entity.get("updated_at", datetime.utcnow()),
            "expires_at": entity.get("expires_at"),
        }

    def from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dictionary from database to metadata entity."""
        return {
            "id": data["id"],
            "database_id": data["database_id"],
            "table_name": data.get("table_name"),
            "metadata_type": data["metadata_type"],
            "content": (
                json.loads(data["metadata_content"]) if data["metadata_content"] else {}
            ),
            "database_type": data.get("database_type"),
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "expires_at": data.get("expires_at"),
        }

    async def get_table_list(self, database_id: str) -> Optional[List[str]]:
        """Get cached table list for a database."""
        try:
            results = await self.find_by(
                {"database_id": database_id, "metadata_type": "table_list"},
                limit=1,
                order_by="updated_at DESC",
            )

            if results:
                metadata = results[0]
                # Check if not expired
                if (
                    not metadata.get("expires_at")
                    or metadata["expires_at"] > datetime.utcnow()
                ):
                    return metadata["content"].get("tables", [])

            return None

        except Exception as e:
            logger.error(
                f"Failed to get cached table list for database {database_id}: {e}"
            )
            return None

    async def store_table_list(
        self,
        database_id: str,
        tables: List[str],
        database_type: str,
        ttl_seconds: int = 3600,
    ) -> None:
        """Store table list in cache."""
        try:
            expires_at = datetime.utcnow().replace(microsecond=0) + timedelta(
                seconds=ttl_seconds
            )

            entity = {
                "database_id": database_id,
                "metadata_type": "table_list",
                "content": {
                    "tables": tables,
                    "extracted_at": datetime.utcnow().isoformat(),
                },
                "database_type": database_type,
                "expires_at": expires_at,
            }

            # Delete existing table list for this database
            await self._delete_existing_metadata(database_id, "table_list")

            # Store new table list
            await self.create(entity)

            logger.debug(
                f"Stored table list for database {database_id} with {len(tables)} tables"
            )

        except Exception as e:
            logger.error(f"Failed to store table list for database {database_id}: {e}")
            raise

    async def get_table_metadata(
        self, database_id: str, table_name: str
    ) -> Optional[TableSchema]:
        """Get cached table metadata."""
        try:
            results = await self.find_by(
                {
                    "database_id": database_id,
                    "table_name": table_name,
                    "metadata_type": "table_metadata",
                },
                limit=1,
                order_by="updated_at DESC",
            )

            if results:
                metadata = results[0]
                # Check if not expired
                if (
                    not metadata.get("expires_at")
                    or metadata["expires_at"] > datetime.utcnow()
                ):
                    return TableSchema(**metadata["content"]["metadata"])

            return None

        except Exception as e:
            logger.error(f"Failed to get cached metadata for table {table_name}: {e}")
            return None

    async def store_table_metadata(
        self,
        database_id: str,
        table_schema: TableSchema,
        database_type: str,
        ttl_seconds: int = 7200,
    ) -> None:
        """Store table metadata in cache."""
        try:
            expires_at = datetime.utcnow().replace(microsecond=0) + timedelta(
                seconds=ttl_seconds
            )

            entity = {
                "database_id": database_id,
                "table_name": table_schema.name,
                "metadata_type": "table_metadata",
                "content": {
                    "metadata": table_schema.model_dump(),
                    "extracted_at": datetime.utcnow().isoformat(),
                },
                "database_type": database_type,
                "expires_at": expires_at,
            }

            # Delete existing metadata for this table
            await self._delete_existing_metadata(
                database_id, "table_metadata", table_schema.name
            )

            # Store new metadata
            await self.create(entity)

            logger.debug(
                f"Stored metadata for table {table_schema.name} in database {database_id}"
            )

        except Exception as e:
            logger.error(f"Failed to store metadata for table {table_schema.name}: {e}")
            raise

    async def get_sample_data(
        self, database_id: str, table_name: str, column_name: str
    ) -> Optional[List]:
        """Get cached sample data for a column."""
        try:
            results = await self.find_by(
                {
                    "database_id": database_id,
                    "table_name": table_name,
                    "metadata_type": "sample_data",
                },
                limit=1,
                order_by="updated_at DESC",
            )

            if results:
                metadata = results[0]
                # Check if not expired
                if (
                    not metadata.get("expires_at")
                    or metadata["expires_at"] > datetime.utcnow()
                ):
                    column_samples = metadata["content"].get("columns", {})
                    return column_samples.get(column_name, [])

            return None

        except Exception as e:
            logger.error(
                f"Failed to get cached sample data for {table_name}.{column_name}: {e}"
            )
            return None

    async def store_sample_data(
        self,
        database_id: str,
        table_name: str,
        column_samples: Dict[str, List],
        database_type: str,
        ttl_seconds: int = 14400,
    ) -> None:
        """Store sample data in cache."""
        try:
            expires_at = datetime.utcnow().replace(microsecond=0) + timedelta(
                seconds=ttl_seconds
            )

            entity = {
                "database_id": database_id,
                "table_name": table_name,
                "metadata_type": "sample_data",
                "content": {
                    "columns": column_samples,
                    "extracted_at": datetime.utcnow().isoformat(),
                },
                "database_type": database_type,
                "expires_at": expires_at,
            }

            # Delete existing sample data for this table
            await self._delete_existing_metadata(database_id, "sample_data", table_name)

            # Store new sample data
            await self.create(entity)

            logger.debug(
                f"Stored sample data for table {table_name} in database {database_id}"
            )

        except Exception as e:
            logger.error(f"Failed to store sample data for table {table_name}: {e}")
            raise

    async def _delete_existing_metadata(
        self, database_id: str, metadata_type: str, table_name: Optional[str] = None
    ) -> None:
        """Delete existing metadata entries."""
        try:
            filters = {"database_id": database_id, "metadata_type": metadata_type}

            if table_name:
                filters["table_name"] = table_name

            existing = await self.find_by(filters)

            for metadata in existing:
                await self.delete(metadata["id"])

        except Exception as e:
            logger.warning(f"Failed to delete existing metadata: {e}")

    async def cleanup_expired_metadata(self) -> int:
        """Clean up expired metadata entries."""
        try:
            current_time = datetime.utcnow()

            # Find expired entries
            expired_query = """
                SELECT id FROM metadata_cache
                WHERE expires_at IS NOT NULL AND expires_at < $1
            """

            expired_entries = await self.execute_raw_query(
                expired_query, [current_time]
            )

            # Delete expired entries
            deleted_count = 0
            for entry in expired_entries:
                await self.delete(entry["id"])
                deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired metadata entries")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired metadata: {e}")
            return 0

    async def get_database_stats(self, database_id: str) -> Dict[str, Any]:
        """Get statistics about cached metadata for a database."""
        try:
            stats_query = """
                SELECT
                    metadata_type,
                    COUNT(*) as count,
                    MAX(updated_at) as last_updated,
                    COUNT(CASE WHEN expires_at > $2 OR expires_at IS NULL THEN 1 END) as active_count
                FROM metadata_cache
                WHERE database_id = $1
                GROUP BY metadata_type
            """

            current_time = datetime.utcnow()
            results = await self.execute_raw_query(
                stats_query, [database_id, current_time]
            )

            stats = {
                "database_id": database_id,
                "total_entries": 0,
                "active_entries": 0,
                "by_type": {},
                "last_updated": None,
            }

            overall_last_updated = None

            for row in results:
                metadata_type = row["metadata_type"]
                count = row["count"]
                active_count = row["active_count"]
                last_updated = row["last_updated"]

                stats["total_entries"] += count
                stats["active_entries"] += active_count
                stats["by_type"][metadata_type] = {
                    "total": count,
                    "active": active_count,
                    "last_updated": last_updated.isoformat() if last_updated else None,
                }

                if last_updated and (
                    not overall_last_updated or last_updated > overall_last_updated
                ):
                    overall_last_updated = last_updated

            if overall_last_updated:
                stats["last_updated"] = overall_last_updated.isoformat()

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats for {database_id}: {e}")
            return {"database_id": database_id, "error": str(e)}
