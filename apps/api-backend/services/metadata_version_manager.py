"""Metadata version management service for SamvadQL."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import json

from models.table import TableSchema
from models.versioned_schema import VersionedTableSchema, SchemaChange, SchemaComparison
from repositories.versioned_schema import (
    VersionedSchemaRepository,
    SchemaChangeRepository,
)

logger = logging.getLogger(__name__)


class MetadataVersionManager:
    """Service for managing schema versions and detecting changes."""

    def __init__(
        self,
        schema_repo: Optional[VersionedSchemaRepository] = None,
        change_repo: Optional[SchemaChangeRepository] = None,
    ):
        self.schema_repo = schema_repo or VersionedSchemaRepository()
        self.change_repo = change_repo or SchemaChangeRepository()
        self._lock = asyncio.Lock()

    async def create_schema_version(
        self,
        schema: TableSchema,
        change_reason: str,
        changed_by: Optional[str] = None,
        version: Optional[str] = None,
    ) -> str:
        """Create a new schema version and return version ID."""
        async with self._lock:
            try:
                # Get current active version to determine parent
                current_version = await self.schema_repo.get_active_version(
                    schema.database_id, schema.name
                )

                # Generate version if not provided
                if not version:
                    version = await self._generate_version_id(
                        schema.database_id, schema.name
                    )

                # Create versioned schema
                versioned_schema = VersionedTableSchema.from_table_schema(
                    schema,
                    version=version,
                    parent_version=current_version.version if current_version else None,
                    change_reason=change_reason,
                    changed_by=changed_by or "system",
                )

                # Generate and set schema hash
                versioned_schema.schema_hash = versioned_schema.generate_schema_hash()

                # Check if schema actually changed
                if current_version:
                    current_hash = (
                        current_version.schema_hash
                        or current_version.generate_schema_hash()
                    )
                    if current_hash == versioned_schema.schema_hash:
                        logger.info(
                            f"Schema for table {schema.name} unchanged, skipping version creation"
                        )
                        return current_version.version

                # Create the new version
                created_schema = await self.schema_repo.create_version(
                    versioned_schema, deactivate_previous=True
                )

                # If there was a previous version, detect and record changes
                if current_version:
                    await self._detect_and_record_changes(
                        current_version, created_schema
                    )

                logger.info(
                    f"Created schema version {version} for table {schema.name} "
                    f"in database {schema.database_id}"
                )

                return version

            except Exception as e:
                logger.error(f"Failed to create schema version: {e}")
                raise

    async def get_schema_at_time(
        self, database_id: str, table_name: str, timestamp: datetime
    ) -> Optional[VersionedTableSchema]:
        """Retrieve schema as it existed at specific time."""
        try:
            return await self.schema_repo.get_schema_at_time(
                database_id, table_name, timestamp
            )

        except Exception as e:
            logger.error(
                f"Failed to get schema at time {timestamp} for table {table_name}: {e}"
            )
            return None

    async def compare_schema_versions(
        self, database_id: str, table_name: str, version1: str, version2: str
    ) -> SchemaComparison:
        """Compare two schema versions and return differences."""
        try:
            # Get both versions
            schema1 = await self.schema_repo.get_version(
                database_id, table_name, version1
            )
            schema2 = await self.schema_repo.get_version(
                database_id, table_name, version2
            )

            if not schema1:
                raise ValueError(f"Version {version1} not found")
            if not schema2:
                raise ValueError(f"Version {version2} not found")

            # Get recorded changes between versions
            changes = await self.change_repo.get_changes_between_versions(
                database_id, table_name, version1, version2
            )

            # If no recorded changes, compute them
            if not changes:
                changes = await self._compute_schema_differences(schema1, schema2)

            # Determine compatibility
            is_compatible, compatibility_notes = self._assess_compatibility(changes)

            return SchemaComparison(
                version1=version1,
                version2=version2,
                changes=changes,
                is_compatible=is_compatible,
                compatibility_notes=compatibility_notes,
                compared_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Failed to compare schema versions: {e}")
            raise

    async def get_version_history(
        self, database_id: str, table_name: str, limit: int = 50
    ) -> List[VersionedTableSchema]:
        """Get version history for a table."""
        try:
            return await self.schema_repo.get_version_history(
                database_id, table_name, limit
            )

        except Exception as e:
            logger.error(f"Failed to get version history for table {table_name}: {e}")
            return []

    async def get_active_schema(
        self, database_id: str, table_name: str
    ) -> Optional[VersionedTableSchema]:
        """Get the currently active schema version."""
        try:
            return await self.schema_repo.get_active_version(database_id, table_name)

        except Exception as e:
            logger.error(f"Failed to get active schema for table {table_name}: {e}")
            return None

    async def detect_schema_changes(
        self, database_id: str, current_schemas: List[TableSchema]
    ) -> Dict[str, str]:
        """Detect schema changes and create new versions automatically."""
        try:
            version_updates = {}

            for schema in current_schemas:
                # Get current active version
                current_version = await self.schema_repo.get_active_version(
                    database_id, schema.name
                )

                # Generate hash for current schema
                temp_versioned = VersionedTableSchema.from_table_schema(
                    schema, version="temp"
                )
                current_hash = temp_versioned.generate_schema_hash()

                # Check if schema changed
                if not current_version:
                    # First time seeing this table
                    version = await self.create_schema_version(
                        schema,
                        change_reason="Initial schema detection",
                        changed_by="system",
                    )
                    version_updates[schema.name] = version

                elif current_version.schema_hash != current_hash:
                    # Schema changed
                    version = await self.create_schema_version(
                        schema,
                        change_reason="Automatic schema change detection",
                        changed_by="system",
                    )
                    version_updates[schema.name] = version

            if version_updates:
                logger.info(
                    f"Detected schema changes for {len(version_updates)} tables "
                    f"in database {database_id}"
                )

            return version_updates

        except Exception as e:
            logger.error(f"Failed to detect schema changes: {e}")
            return {}

    async def cleanup_old_versions(
        self, database_id: str, keep_versions: int = 10
    ) -> int:
        """Clean up old schema versions."""
        try:
            return await self.schema_repo.cleanup_old_versions(
                database_id, keep_versions
            )

        except Exception as e:
            logger.error(f"Failed to cleanup old versions: {e}")
            return 0

    async def get_database_schema_summary(self, database_id: str) -> Dict[str, any]:
        """Get summary of all schema versions in a database."""
        try:
            active_schemas = await self.schema_repo.get_database_versions(
                database_id, active_only=True
            )

            all_schemas = await self.schema_repo.get_database_versions(
                database_id, active_only=False
            )

            # Group by table name
            table_stats = {}
            for schema in all_schemas:
                table_name = schema.name
                if table_name not in table_stats:
                    table_stats[table_name] = {
                        "total_versions": 0,
                        "active_version": None,
                        "first_version_date": None,
                        "last_version_date": None,
                    }

                stats = table_stats[table_name]
                stats["total_versions"] += 1

                if schema.is_active:
                    stats["active_version"] = schema.version

                if (
                    not stats["first_version_date"]
                    or schema.created_at < stats["first_version_date"]
                ):
                    stats["first_version_date"] = schema.created_at

                if (
                    not stats["last_version_date"]
                    or schema.created_at > stats["last_version_date"]
                ):
                    stats["last_version_date"] = schema.created_at

            return {
                "database_id": database_id,
                "total_tables": len(table_stats),
                "total_versions": len(all_schemas),
                "active_versions": len(active_schemas),
                "table_statistics": table_stats,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get database schema summary: {e}")
            return {"database_id": database_id, "error": str(e)}

    async def _generate_version_id(self, database_id: str, table_name: str) -> str:
        """Generate a unique version ID."""
        try:
            # Get latest version number
            history = await self.schema_repo.get_version_history(
                database_id, table_name, limit=1
            )

            if not history:
                return "v1.0.0"

            latest_version = history[0].version

            # Simple version increment (v1.0.0 -> v1.0.1)
            if latest_version.startswith("v") and "." in latest_version:
                parts = latest_version[1:].split(".")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    major, minor, patch = map(int, parts)
                    return f"v{major}.{minor}.{patch + 1}"

            # Fallback to timestamp-based version
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            return f"v{timestamp}"

        except Exception as e:
            logger.warning(f"Failed to generate version ID, using timestamp: {e}")
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            return f"v{timestamp}"

    async def _detect_and_record_changes(
        self, old_schema: VersionedTableSchema, new_schema: VersionedTableSchema
    ) -> None:
        """Detect and record changes between two schema versions."""
        try:
            changes = await self._compute_schema_differences(old_schema, new_schema)

            # Record each change
            for change in changes:
                change_record = {
                    "database_id": new_schema.database_id,
                    "table_name": new_schema.name,
                    "from_version": old_schema.version,
                    "to_version": new_schema.version,
                    "change_type": change.change_type,
                    "object_type": change.object_type,
                    "object_name": change.object_name,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "description": change.description,
                    "created_by": new_schema.changed_by,
                }

                await self.change_repo.create(change_record)

            logger.debug(
                f"Recorded {len(changes)} changes between versions "
                f"{old_schema.version} and {new_schema.version}"
            )

        except Exception as e:
            logger.warning(f"Failed to record schema changes: {e}")

    async def _compute_schema_differences(
        self, schema1: VersionedTableSchema, schema2: VersionedTableSchema
    ) -> List[SchemaChange]:
        """Compute differences between two schemas."""
        changes = []

        # Create column maps for easier comparison
        cols1 = {col.name: col for col in schema1.columns}
        cols2 = {col.name: col for col in schema2.columns}

        # Check for removed columns
        for col_name, col in cols1.items():
            if col_name not in cols2:
                changes.append(
                    SchemaChange(
                        change_type="removed",
                        object_type="column",
                        object_name=col_name,
                        old_value=col.model_dump(),
                        new_value=None,
                        description=f"Column '{col_name}' was removed",
                    )
                )

        # Check for added columns
        for col_name, col in cols2.items():
            if col_name not in cols1:
                changes.append(
                    SchemaChange(
                        change_type="added",
                        object_type="column",
                        object_name=col_name,
                        old_value=None,
                        new_value=col.model_dump(),
                        description=f"Column '{col_name}' was added",
                    )
                )

        # Check for modified columns
        for col_name in cols1.keys() & cols2.keys():
            old_col = cols1[col_name]
            new_col = cols2[col_name]

            if old_col.model_dump() != new_col.model_dump():
                changes.append(
                    SchemaChange(
                        change_type="modified",
                        object_type="column",
                        object_name=col_name,
                        old_value=old_col.model_dump(),
                        new_value=new_col.model_dump(),
                        description=f"Column '{col_name}' was modified",
                    )
                )

        # Check for table-level changes
        if schema1.description != schema2.description:
            changes.append(
                SchemaChange(
                    change_type="modified",
                    object_type="table",
                    object_name="description",
                    old_value={"description": schema1.description},
                    new_value={"description": schema2.description},
                    description="Table description was modified",
                )
            )

        return changes

    def _assess_compatibility(
        self, changes: List[SchemaChange]
    ) -> Tuple[bool, List[str]]:
        """Assess backward compatibility of changes."""
        is_compatible = True
        notes = []

        for change in changes:
            if change.change_type == "removed":
                is_compatible = False
                notes.append(
                    f"Removed {change.object_type} '{change.object_name}' breaks compatibility"
                )

            elif change.change_type == "modified" and change.object_type == "column":
                # Check for breaking changes in column modifications
                old_val = change.old_value or {}
                new_val = change.new_value or {}

                # Data type changes are potentially breaking
                if old_val.get("data_type") != new_val.get("data_type"):
                    is_compatible = False
                    notes.append(
                        f"Data type change in column '{change.object_name}' "
                        f"from {old_val.get('data_type')} to {new_val.get('data_type')} "
                        f"may break compatibility"
                    )

                # Nullable to non-nullable is breaking
                if old_val.get("is_nullable", True) and not new_val.get(
                    "is_nullable", True
                ):
                    is_compatible = False
                    notes.append(
                        f"Column '{change.object_name}' changed from nullable to non-nullable "
                        f"breaks compatibility"
                    )

        if is_compatible and changes:
            notes.append("All changes are backward compatible")
        elif not changes:
            notes.append("No changes detected")

        return is_compatible, notes
