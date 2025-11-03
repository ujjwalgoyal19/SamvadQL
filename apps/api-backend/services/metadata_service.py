"""Metadata extraction service for SamvadQL."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import uuid4

import redis.asyncio as redis
from pydantic import BaseModel

from core.config import settings
from core.db.connectors.factory import DatabaseConnectorFactory
from core.db.connectors.base import BaseDatabaseConnector
from models import DatabaseType, TableSchema, ColumnSchema
from services.metadata_version_manager import MetadataVersionManager

logger = logging.getLogger(__name__)


class MetadataCacheConfig(BaseModel):
    """Configuration for metadata caching."""

    # Cache TTL settings (in seconds)
    table_list_ttl: int = 3600  # 1 hour
    table_metadata_ttl: int = 7200  # 2 hours
    sample_data_ttl: int = 14400  # 4 hours

    # Cache key prefixes
    table_list_prefix: str = "metadata:tables"
    table_metadata_prefix: str = "metadata:table"
    sample_data_prefix: str = "metadata:samples"

    # Sample data collection settings
    max_sample_values: int = 20
    low_cardinality_threshold: int = 100
    sample_collection_timeout: int = 30


class MetadataExtractionService:
    """Service for extracting and caching database metadata."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.config = MetadataCacheConfig()
        self._connectors: Dict[str, BaseDatabaseConnector] = {}
        self._lock = asyncio.Lock()
        self.version_manager = MetadataVersionManager()

    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
        return self.redis_client

    async def _get_connector(
        self, database_id: str, database_type: DatabaseType, connection_config: Dict
    ) -> BaseDatabaseConnector:
        """Get or create database connector."""
        async with self._lock:
            if database_id not in self._connectors:
                connector = DatabaseConnectorFactory.create_connector(
                    database_type, connection_config
                )
                await connector.connect()
                self._connectors[database_id] = connector

            return self._connectors[database_id]

    def _generate_cache_key(
        self, prefix: str, database_id: str, table_name: Optional[str] = None
    ) -> str:
        """Generate cache key."""
        if table_name:
            return f"{prefix}:{database_id}:{table_name}"
        return f"{prefix}:{database_id}"

    async def _cache_set(self, key: str, value: Dict, ttl: int) -> None:
        """Set value in cache with TTL."""
        try:
            redis_client = await self._get_redis_client()
            await redis_client.setex(key, ttl, json.dumps(value, default=str))
            logger.debug(f"Cached data with key: {key}")
        except Exception as e:
            logger.warning(f"Failed to cache data with key {key}: {e}")

    async def _cache_get(self, key: str) -> Optional[Dict]:
        """Get value from cache."""
        try:
            redis_client = await self._get_redis_client()
            cached_data = await redis_client.get(key)
            if cached_data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached_data)
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached data with key {key}: {e}")
            return None

    async def _cache_delete(self, pattern: str) -> None:
        """Delete cache entries matching pattern."""
        try:
            redis_client = await self._get_redis_client()
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.debug(f"Deleted {len(keys)} cache entries matching: {pattern}")
        except Exception as e:
            logger.warning(
                f"Failed to delete cache entries with pattern {pattern}: {e}"
            )

    async def list_tables(
        self,
        database_id: str,
        database_type: DatabaseType,
        connection_config: Dict,
        use_cache: bool = True,
    ) -> List[str]:
        """List all tables in the database."""
        cache_key = self._generate_cache_key(self.config.table_list_prefix, database_id)

        # Try cache first
        if use_cache:
            cached_tables = await self._cache_get(cache_key)
            if cached_tables:
                return cached_tables.get("tables", [])

        # Fetch from database
        try:
            connector = await self._get_connector(
                database_id, database_type, connection_config
            )
            tables = await connector.list_tables()

            # Cache the result
            if use_cache:
                await self._cache_set(
                    cache_key,
                    {
                        "tables": tables,
                        "extracted_at": datetime.utcnow().isoformat(),
                        "database_type": database_type.value,
                    },
                    self.config.table_list_ttl,
                )

            logger.info(f"Extracted {len(tables)} tables from database {database_id}")
            return tables

        except Exception as e:
            logger.error(f"Failed to list tables for database {database_id}: {e}")
            raise

    async def get_table_metadata(
        self,
        database_id: str,
        database_type: DatabaseType,
        connection_config: Dict,
        table_name: str,
        use_cache: bool = True,
        include_samples: bool = True,
    ) -> TableSchema:
        """Get metadata for a specific table."""
        cache_key = self._generate_cache_key(
            self.config.table_metadata_prefix, database_id, table_name
        )

        # Try cache first
        if use_cache:
            cached_metadata = await self._cache_get(cache_key)
            if cached_metadata:
                # Convert back to TableSchema
                return TableSchema(**cached_metadata["metadata"])

        # Fetch from database
        try:
            connector = await self._get_connector(
                database_id, database_type, connection_config
            )
            table_schema = await connector.get_table_metadata(table_name)

            # Enhance with sample data if requested
            if include_samples:
                table_schema = await self._enhance_with_sample_data(
                    connector, table_schema
                )

            # Cache the result
            if use_cache:
                await self._cache_set(
                    cache_key,
                    {
                        "metadata": table_schema.model_dump(),
                        "extracted_at": datetime.utcnow().isoformat(),
                        "database_type": database_type.value,
                        "includes_samples": include_samples,
                    },
                    self.config.table_metadata_ttl,
                )

            logger.info(
                f"Extracted metadata for table {table_name} from database {database_id}"
            )
            return table_schema

        except Exception as e:
            logger.error(
                f"Failed to get metadata for table {table_name} in database {database_id}: {e}"
            )
            raise

    async def _enhance_with_sample_data(
        self, connector: BaseDatabaseConnector, table_schema: TableSchema
    ) -> TableSchema:
        """Enhance table schema with sample data for low-cardinality columns."""
        try:
            enhanced_columns = []

            for column in table_schema.columns:
                enhanced_column = column.model_copy()

                # Skip if already has sample values
                if enhanced_column.sample_values:
                    enhanced_columns.append(enhanced_column)
                    continue

                # Get sample values for this column
                sample_values = await self._collect_sample_data(
                    connector, table_schema.name, column.name, column.data_type
                )

                if sample_values:
                    enhanced_column.sample_values = sample_values

                enhanced_columns.append(enhanced_column)

            # Create new table schema with enhanced columns
            enhanced_schema = table_schema.model_copy()
            enhanced_schema.columns = enhanced_columns

            return enhanced_schema

        except Exception as e:
            logger.warning(
                f"Failed to enhance table {table_schema.name} with sample data: {e}"
            )
            return table_schema

    async def _collect_sample_data(
        self,
        connector: BaseDatabaseConnector,
        table_name: str,
        column_name: str,
        data_type: str,
    ) -> List:
        """Collect sample data for a specific column."""
        try:
            # Skip certain data types that are not suitable for sampling
            skip_types = {"text", "blob", "binary", "json", "jsonb", "xml"}
            if data_type.lower() in skip_types:
                return []

            # Check cardinality first
            cardinality_query = f"""
                SELECT COUNT(DISTINCT "{column_name}") as distinct_count,
                       COUNT(*) as total_count
                FROM "{table_name}"
                WHERE "{column_name}" IS NOT NULL
            """

            cardinality_result = await connector.execute_query(cardinality_query)
            if not cardinality_result:
                return []

            distinct_count = cardinality_result[0].get("distinct_count", 0)
            total_count = cardinality_result[0].get("total_count", 0)

            # Only collect samples for low-cardinality columns
            if distinct_count > self.config.low_cardinality_threshold:
                return []

            # Collect sample values
            sample_query = f"""
                SELECT DISTINCT "{column_name}" as sample_value
                FROM "{table_name}"
                WHERE "{column_name}" IS NOT NULL
                ORDER BY "{column_name}"
                LIMIT {self.config.max_sample_values}
            """

            # Execute with timeout
            sample_result = await asyncio.wait_for(
                connector.execute_query(sample_query),
                timeout=self.config.sample_collection_timeout,
            )

            samples = [row["sample_value"] for row in sample_result]

            logger.debug(
                f"Collected {len(samples)} sample values for {table_name}.{column_name} "
                f"(cardinality: {distinct_count}/{total_count})"
            )

            return samples

        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout collecting sample data for {table_name}.{column_name}"
            )
            return []
        except Exception as e:
            logger.warning(
                f"Failed to collect sample data for {table_name}.{column_name}: {e}"
            )
            return []

    async def refresh_metadata(
        self,
        database_id: str,
        database_type: DatabaseType,
        connection_config: Dict,
        table_names: Optional[List[str]] = None,
        detect_schema_changes: bool = True,
    ) -> Dict:
        """Refresh metadata for specified tables or all tables."""
        try:
            # Clear existing cache
            if table_names:
                # Clear specific tables
                for table_name in table_names:
                    cache_key = self._generate_cache_key(
                        self.config.table_metadata_prefix, database_id, table_name
                    )
                    await self._cache_delete(cache_key)
            else:
                # Clear all metadata for this database
                pattern = f"{self.config.table_metadata_prefix}:{database_id}:*"
                await self._cache_delete(pattern)

                # Also clear table list
                cache_key = self._generate_cache_key(
                    self.config.table_list_prefix, database_id
                )
                await self._cache_delete(cache_key)

            # Get fresh table list
            tables = await self.list_tables(
                database_id, database_type, connection_config, use_cache=False
            )

            # Filter tables if specified
            if table_names:
                tables = [t for t in tables if t in table_names]

            # Refresh metadata for each table
            refreshed_tables = []
            failed_tables = []
            table_schemas = []

            for table_name in tables:
                try:
                    schema = await self.get_table_metadata(
                        database_id,
                        database_type,
                        connection_config,
                        table_name,
                        use_cache=False,
                        include_samples=True,
                    )
                    refreshed_tables.append(table_name)
                    table_schemas.append(schema)
                except Exception as e:
                    logger.error(
                        f"Failed to refresh metadata for table {table_name}: {e}"
                    )
                    failed_tables.append(table_name)

            # Detect schema changes if requested
            schema_changes = {}
            if detect_schema_changes and table_schemas:
                try:
                    schema_changes = await self.version_manager.detect_schema_changes(
                        database_id, table_schemas
                    )
                except Exception as e:
                    logger.warning(f"Failed to detect schema changes: {e}")

            result = {
                "database_id": database_id,
                "refreshed_at": datetime.utcnow().isoformat(),
                "total_tables": len(tables),
                "refreshed_tables": refreshed_tables,
                "failed_tables": failed_tables,
                "success_rate": len(refreshed_tables) / len(tables) if tables else 0,
                "schema_changes": schema_changes,
            }

            logger.info(
                f"Metadata refresh completed for database {database_id}: "
                f"{len(refreshed_tables)}/{len(tables)} tables successful"
                + (
                    f", {len(schema_changes)} schema changes detected"
                    if schema_changes
                    else ""
                )
            )

            return result

        except Exception as e:
            logger.error(f"Failed to refresh metadata for database {database_id}: {e}")
            raise

    async def get_database_summary(
        self, database_id: str, database_type: DatabaseType, connection_config: Dict
    ) -> Dict:
        """Get summary information about the database."""
        try:
            tables = await self.list_tables(
                database_id, database_type, connection_config
            )

            summary = {
                "database_id": database_id,
                "database_type": database_type.value,
                "total_tables": len(tables),
                "tables": tables,
                "generated_at": datetime.utcnow().isoformat(),
            }

            # Get sample of table metadata for summary
            sample_tables = tables[:5]  # First 5 tables
            table_summaries = []

            for table_name in sample_tables:
                try:
                    metadata = await self.get_table_metadata(
                        database_id, database_type, connection_config, table_name
                    )
                    table_summaries.append(
                        {
                            "name": metadata.name,
                            "column_count": len(metadata.columns),
                            "row_count": metadata.row_count,
                            "description": metadata.description,
                            "tier": metadata.tier,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to get summary for table {table_name}: {e}")

            summary["sample_tables"] = table_summaries

            # Add schema versioning summary
            try:
                schema_summary = await self.version_manager.get_database_schema_summary(
                    database_id
                )
                summary["schema_versioning"] = schema_summary
            except Exception as e:
                logger.warning(f"Failed to get schema versioning summary: {e}")

            return summary

        except Exception as e:
            logger.error(f"Failed to get database summary for {database_id}: {e}")
            raise

    async def get_table_version_history(
        self, database_id: str, table_name: str, limit: int = 50
    ) -> List[Dict]:
        """Get version history for a specific table."""
        try:
            versions = await self.version_manager.get_version_history(
                database_id, table_name, limit
            )

            return [
                {
                    "version": v.version,
                    "created_at": v.created_at.isoformat(),
                    "is_active": v.is_active,
                    "parent_version": v.parent_version,
                    "change_reason": v.change_reason,
                    "changed_by": v.changed_by,
                    "schema_hash": v.schema_hash,
                    "column_count": len(v.columns),
                }
                for v in versions
            ]

        except Exception as e:
            logger.error(f"Failed to get version history for table {table_name}: {e}")
            return []

    async def compare_table_versions(
        self, database_id: str, table_name: str, version1: str, version2: str
    ) -> Dict:
        """Compare two versions of a table schema."""
        try:
            comparison = await self.version_manager.compare_schema_versions(
                database_id, table_name, version1, version2
            )

            return {
                "version1": comparison.version1,
                "version2": comparison.version2,
                "is_compatible": comparison.is_compatible,
                "compatibility_notes": comparison.compatibility_notes,
                "changes": [
                    {
                        "change_type": change.change_type,
                        "object_type": change.object_type,
                        "object_name": change.object_name,
                        "description": change.description,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                    }
                    for change in comparison.changes
                ],
                "compared_at": comparison.compared_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to compare table versions: {e}")
            raise

    async def get_table_at_time(
        self, database_id: str, table_name: str, timestamp: datetime
    ) -> Optional[Dict]:
        """Get table schema as it existed at a specific time."""
        try:
            versioned_schema = await self.version_manager.get_schema_at_time(
                database_id, table_name, timestamp
            )

            if not versioned_schema:
                return None

            return {
                "name": versioned_schema.name,
                "database_id": versioned_schema.database_id,
                "version": versioned_schema.version,
                "created_at": versioned_schema.created_at.isoformat(),
                "columns": [col.model_dump() for col in versioned_schema.columns],
                "description": versioned_schema.description,
                "tier": versioned_schema.tier,
                "tags": versioned_schema.tags,
                "row_count": versioned_schema.row_count,
            }

        except Exception as e:
            logger.error(f"Failed to get table at time {timestamp}: {e}")
            return None

    async def close(self) -> None:
        """Close all connections and cleanup resources."""
        try:
            # Close all database connectors
            for connector in self._connectors.values():
                await connector.disconnect()

            self._connectors.clear()

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()

            logger.info("Metadata extraction service closed")

        except Exception as e:
            logger.error(f"Error closing metadata extraction service: {e}")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
