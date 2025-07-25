"""Table schema models for SamvadQL."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re
import uuid

from .column import ColumnSchema


class TableSchema(BaseModel):
    """Database table schema information with validation."""

    name: str = Field(..., min_length=1, max_length=255, description="Table name")
    database_id: str = Field(..., description="Database identifier")
    columns: List[ColumnSchema] = Field(..., min_length=1, description="Table columns")
    description: Optional[str] = Field(
        None, max_length=2000, description="Table description"
    )
    sample_queries: List[str] = Field(
        default_factory=list, description="Sample queries for this table"
    )
    tier: Optional[str] = Field(
        None, description="Table tier (e.g., 'gold', 'silver', 'bronze')"
    )
    tags: List[str] = Field(default_factory=list, description="Table tags")
    row_count: Optional[int] = Field(None, ge=0, description="Approximate row count")
    created_at: Optional[datetime] = Field(None, description="Table creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate table name format."""
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

    @field_validator("sample_queries")
    @classmethod
    def validate_sample_queries(cls, v):
        """Validate sample queries."""
        if v:
            if len(v) > 20:
                raise ValueError("Too many sample queries (max 20)")

            for query in v:
                if not query or query.isspace():
                    raise ValueError("Sample queries cannot be empty")

                if len(query) > 1000:
                    raise ValueError("Sample query too long (max 1000 characters)")

        return v

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

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate table tags."""
        if v:
            if len(v) > 20:
                raise ValueError("Too many tags (max 20)")

            for tag in v:
                if not tag or tag.isspace():
                    raise ValueError("Tags cannot be empty")

                if len(tag) > 50:
                    raise ValueError("Tag too long (max 50 characters)")

                if not re.match(r"^[a-zA-Z0-9_-]+$", tag):
                    raise ValueError(
                        "Tags can only contain alphanumeric characters, underscores, and hyphens"
                    )

        return v

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
                "tier": "gold",
                "tags": ["user-data", "core"],
                "row_count": 150000,
            }
        }
