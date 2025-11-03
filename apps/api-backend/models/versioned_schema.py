"""Versioned schema models for SamvadQL."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid

from .table import TableSchema
from .column import ColumnSchema


class SchemaChange(BaseModel):
    """Represents a change in schema between versions."""

    change_type: str = Field(
        ..., description="Type of change: added, removed, modified"
    )
    object_type: str = Field(..., description="Type of object: table, column")
    object_name: str = Field(..., description="Name of the changed object")
    old_value: Optional[Dict[str, Any]] = Field(None, description="Previous value")
    new_value: Optional[Dict[str, Any]] = Field(None, description="New value")
    description: str = Field(
        ..., description="Human-readable description of the change"
    )

    @field_validator("change_type")
    @classmethod
    def validate_change_type(cls, v):
        """Validate change type."""
        valid_types = ["added", "removed", "modified"]
        if v not in valid_types:
            raise ValueError(f"Change type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("object_type")
    @classmethod
    def validate_object_type(cls, v):
        """Validate object type."""
        valid_types = ["table", "column"]
        if v not in valid_types:
            raise ValueError(f"Object type must be one of: {', '.join(valid_types)}")
        return v


class SchemaComparison(BaseModel):
    """Result of comparing two schema versions."""

    version1: str = Field(..., description="First version ID")
    version2: str = Field(..., description="Second version ID")
    changes: List[SchemaChange] = Field(
        default_factory=list, description="List of changes"
    )
    is_compatible: bool = Field(
        ..., description="Whether versions are backward compatible"
    )
    compatibility_notes: List[str] = Field(
        default_factory=list, description="Compatibility notes"
    )
    compared_at: datetime = Field(
        default_factory=datetime.utcnow, description="Comparison timestamp"
    )


class VersionedTableSchema(BaseModel):
    """Database table schema with versioning information."""

    # Core schema information
    name: str = Field(..., min_length=1, max_length=255, description="Table name")
    database_id: str = Field(..., description="Database identifier")
    columns: List[ColumnSchema] = Field(..., min_length=1, description="Table columns")
    description: Optional[str] = Field(
        None, max_length=2000, description="Table description"
    )

    # Versioning information
    version: str = Field(..., description="Version identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Version creation timestamp"
    )
    parent_version: Optional[str] = Field(None, description="Parent version ID")
    is_active: bool = Field(
        True, description="Whether this version is currently active"
    )

    # Metadata
    sample_queries: List[str] = Field(
        default_factory=list, description="Sample queries for this table"
    )
    tier: Optional[str] = Field(
        None, description="Table tier (e.g., 'gold', 'silver', 'bronze')"
    )
    tags: List[str] = Field(default_factory=list, description="Table tags")
    row_count: Optional[int] = Field(None, ge=0, description="Approximate row count")

    # Change tracking
    change_reason: Optional[str] = Field(None, description="Reason for this version")
    changed_by: Optional[str] = Field(
        None, description="User/system that created this version"
    )
    schema_hash: Optional[str] = Field(
        None, description="Hash of schema structure for quick comparison"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate table name format."""
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Table name must start with letter or underscore and contain only alphanumeric characters and underscores"
            )
        return v

    @field_validator("database_id")
    @classmethod
    def validate_database_id(cls, v):
        """Validate database ID format."""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Database ID must be a valid UUID")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """Validate version format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Version cannot be empty")
        return v.strip()

    @field_validator("parent_version")
    @classmethod
    def validate_parent_version(cls, v):
        """Validate parent version format."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Parent version cannot be empty string")
        return v.strip() if v else None

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v):
        """Validate table tier."""
        if v is not None:
            valid_tiers = ["gold", "silver", "bronze", "deprecated"]
            if v.lower() not in valid_tiers:
                raise ValueError(
                    f"Invalid tier. Must be one of: {', '.join(valid_tiers)}"
                )
            return v.lower()
        return v

    def to_table_schema(self) -> TableSchema:
        """Convert to regular TableSchema."""
        return TableSchema(
            name=self.name,
            database_id=self.database_id,
            columns=self.columns,
            description=self.description,
            sample_queries=self.sample_queries,
            tier=self.tier,
            tags=self.tags,
            row_count=self.row_count,
            created_at=self.created_at,
            updated_at=self.created_at,
        )

    @classmethod
    def from_table_schema(
        cls,
        table_schema: TableSchema,
        version: str,
        parent_version: Optional[str] = None,
        change_reason: Optional[str] = None,
        changed_by: Optional[str] = None,
    ) -> "VersionedTableSchema":
        """Create versioned schema from regular TableSchema."""
        return cls(
            name=table_schema.name,
            database_id=table_schema.database_id,
            columns=table_schema.columns,
            description=table_schema.description,
            version=version,
            parent_version=parent_version,
            sample_queries=table_schema.sample_queries,
            tier=table_schema.tier,
            tags=table_schema.tags,
            row_count=table_schema.row_count,
            change_reason=change_reason,
            changed_by=changed_by,
        )

    def generate_schema_hash(self) -> str:
        """Generate hash of schema structure for quick comparison."""
        import hashlib
        import json

        # Create a normalized representation of the schema structure
        schema_structure = {
            "name": self.name,
            "columns": [
                {
                    "name": col.name,
                    "data_type": col.data_type,
                    "is_nullable": col.is_nullable,
                    "is_primary_key": col.is_primary_key,
                    "is_foreign_key": col.is_foreign_key,
                }
                for col in sorted(self.columns, key=lambda x: x.name)
            ],
        }

        # Create hash
        schema_json = json.dumps(schema_structure, sort_keys=True)
        return hashlib.sha256(schema_json.encode()).hexdigest()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "users",
                "database_id": "550e8400-e29b-41d4-a716-446655440000",
                "columns": [
                    {
                        "name": "id",
                        "data_type": "integer",
                        "description": "Primary key",
                        "is_primary_key": True,
                        "is_nullable": False,
                    }
                ],
                "description": "User account information",
                "version": "v1.0.0",
                "parent_version": None,
                "is_active": True,
                "tier": "gold",
                "tags": ["user-data", "core"],
                "row_count": 150000,
                "change_reason": "Initial schema version",
                "changed_by": "system",
            }
        }
