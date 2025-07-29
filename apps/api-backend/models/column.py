"""Column schema models for SamvadQL."""

from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class ColumnSchema(BaseModel):
    """Database column schema information with validation."""

    name: str = Field(..., min_length=1, max_length=255, description="Column name")
    data_type: str = Field(..., min_length=1, description="Column data type")
    description: Optional[str] = Field(
        None, max_length=1000, description="Column description"
    )
    sample_values: List[Any] = Field(default_factory=list, description="Sample values")
    is_nullable: bool = Field(True, description="Whether column allows NULL values")
    is_primary_key: bool = Field(False, description="Whether column is primary key")
    is_foreign_key: bool = Field(False, description="Whether column is foreign key")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate column name format."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Column name must start with letter or underscore and contain only alphanumeric characters and underscores"
            )
        return v

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v):
        """Validate data type format."""
        # Common SQL data types
        valid_types = [
            "integer",
            "int",
            "bigint",
            "smallint",
            "tinyint",
            "varchar",
            "char",
            "text",
            "string",
            "decimal",
            "numeric",
            "float",
            "double",
            "real",
            "boolean",
            "bool",
            "date",
            "time",
            "timestamp",
            "datetime",
            "json",
            "jsonb",
            "xml",
            "uuid",
            "binary",
            "blob",
        ]

        # Allow parameterized types like varchar(255)
        base_type = v.lower().split("(")[0]
        if base_type not in valid_types:
            # Log a warning for unknown types to support different databases
            import warnings

            warnings.warn(
                f"Unknown data type '{v}'. Proceeding for compatibility, but please verify."
            )

        return v.lower()

    @field_validator("sample_values")
    @classmethod
    def validate_sample_values(cls, v):
        """Validate sample values."""
        if v and len(v) > 20:
            raise ValueError("Too many sample values (max 20)")
        return v

    @model_validator(mode="after")
    def validate_key_constraints(self):
        """Validate key constraints."""
        if self.is_primary_key and self.is_nullable:
            raise ValueError("Primary key columns cannot be nullable")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "name": "user_id",
                "data_type": "integer",
                "description": "Unique identifier for user",
                "sample_values": [1, 2, 3, 4, 5],
                "is_nullable": False,
                "is_primary_key": True,
                "is_foreign_key": False,
            }
        }
