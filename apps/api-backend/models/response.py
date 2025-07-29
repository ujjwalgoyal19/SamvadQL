"""Response models for SamvadQL."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
import re
import uuid

from .enums import ValidationStatus
from .table import TableSchema


class ValidationResult(BaseModel):
    """SQL validation result with validation."""

    is_valid: bool = Field(..., description="Whether the SQL is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    is_destructive: bool = Field(
        False, description="Whether the SQL contains destructive operations"
    )
    estimated_cost: Optional[float] = Field(
        None, ge=0, description="Estimated execution cost"
    )
    execution_plan: Optional[str] = Field(None, description="Query execution plan")

    @field_validator("errors", "warnings")
    @classmethod
    def validate_messages(cls, v):
        """Validate error and warning messages."""
        if v:
            for msg in v:
                if not isinstance(msg, str) or not msg.strip():
                    raise ValueError(
                        "Error and warning messages must be non-empty strings"
                    )
        return v

    @field_validator("estimated_cost")
    @classmethod
    def validate_cost(cls, v):
        """Validate estimated cost."""
        if v is not None and v < 0:
            raise ValueError("Estimated cost cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_consistency(self):
        """Validate consistency between fields."""
        if not self.is_valid and not self.errors:
            raise ValueError("Invalid SQL must have at least one error message")

        if self.is_valid and self.errors:
            raise ValueError("Valid SQL cannot have error messages")

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Query may be slow due to missing index"],
                "is_destructive": False,
                "estimated_cost": 125.5,
                "execution_plan": "Seq Scan on users...",
            }
        }


@dataclass
class OptimizationSuggestion:
    """Query optimization suggestion."""

    type: str
    description: str
    impact: str  # "high", "medium", "low"
    suggested_sql: Optional[str] = None


class QueryResponse(BaseModel):
    """Generated SQL query response with validation."""

    sql: str = Field(..., min_length=1, description="Generated SQL query")
    explanation: str = Field(
        ..., min_length=1, description="Human-readable explanation"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    selected_tables: List[str] = Field(..., description="Tables used in the query")
    validation_status: ValidationStatus = Field(..., description="Validation status")
    optimization_suggestions: List[OptimizationSuggestion] = Field(
        default_factory=list, description="Optimization suggestions"
    )
    execution_time_estimate: Optional[float] = Field(
        None, ge=0, description="Estimated execution time in seconds"
    )
    request_id: Optional[str] = Field(None, description="Original request ID")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )

    @field_validator("sql")
    @classmethod
    def validate_sql(cls, v):
        """Validate SQL content."""
        if not v or v.isspace():
            raise ValueError("SQL cannot be empty or whitespace only")

        # Basic SQL validation - check for common SQL keywords
        sql_upper = v.upper().strip()
        valid_starts = [
            "SELECT",
            "WITH",
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
        ]

        if not any(sql_upper.startswith(keyword) for keyword in valid_starts):
            raise ValueError("SQL must start with a valid SQL keyword")

        return v.strip()

    @field_validator("explanation")
    @classmethod
    def validate_explanation(cls, v):
        """Validate explanation content."""
        if not v or v.isspace():
            raise ValueError("Explanation cannot be empty or whitespace only")

        if len(v) > 5000:
            raise ValueError("Explanation is too long (max 5000 characters)")

        return v.strip()

    @field_validator("selected_tables")
    @classmethod
    def validate_selected_tables(cls, v):
        """Validate selected tables."""
        if not v:
            raise ValueError("At least one table must be selected")

        for table in v:
            if not re.match(
                r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table
            ):
                raise ValueError(f"Invalid table name format: {table}")

        return v

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, v):
        """Validate request ID format."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Request ID must be a valid UUID")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT * FROM users WHERE created_at >= '2024-01-01'",
                "explanation": "This query retrieves all users who were created on or after January 1st, 2024",
                "confidence_score": 0.95,
                "selected_tables": ["users"],
                "validation_status": "valid",
                "optimization_suggestions": [],
                "execution_time_estimate": 0.25,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }


@dataclass
class TableRecommendation:
    """Table recommendation from vector search."""

    table_schema: TableSchema
    relevance_score: float
    match_reason: str
    summary: Optional[str] = None
