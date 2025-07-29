"""Request models for SamvadQL."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import re
import uuid


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
