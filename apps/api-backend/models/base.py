"""Base data models for SamvadQL."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class DatabaseType(Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"


class ValidationStatus(Enum):
    """SQL validation status."""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    UNSAFE = "unsafe"


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


class QueryRequest(BaseModel):
    """Natural language query request with validation."""

    query: str = Field(
        ..., min_length=1, max_length=10000, description="Natural language query"
    )
    user_id: str = Field(
        ..., min_length=1, max_length=255, description="User identifier"
    )
    database_id: str = Field(..., description="Database identifier")
    selected_tables: Optional[List[str]] = Field(
        None, description="Pre-selected tables"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session identifier")
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Request identifier"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        """Validate query content."""
        if not v or v.isspace():
            raise ValueError("Query cannot be empty or whitespace only")

        # Check for potentially malicious content
        dangerous_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Query contains potentially unsafe content")

        return v.strip()

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        """Validate user ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "User ID can only contain alphanumeric characters, underscores, and hyphens"
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

    @field_validator("selected_tables")
    @classmethod
    def validate_selected_tables(cls, v):
        """Validate selected tables."""
        if v is not None:
            if len(v) > 50:  # Reasonable limit
                raise ValueError("Too many selected tables (max 50)")

            for table in v:
                if not re.match(
                    r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$", table
                ):
                    raise ValueError(f"Invalid table name format: {table}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all users who signed up last month",
                "user_id": "user123",
                "database_id": "550e8400-e29b-41d4-a716-446655440000",
                "selected_tables": ["users", "signups"],
                "context": {"timezone": "UTC"},
                "session_id": "session_abc123",
            }
        }


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


@dataclass
class QueryContext:
    """Context for query generation."""

    user_id: str
    session_id: str
    database_type: DatabaseType
    previous_queries: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserFeedback:
    """User feedback on generated queries."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    query_id: str = ""
    original_query: str = ""
    generated_sql: str = ""
    feedback_type: str = ""  # 'accept', 'reject', 'modify'
    comments: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLogEntry:
    """Audit log entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
