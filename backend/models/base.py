"""Base data models for SamvadQL."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import uuid


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


@dataclass
class ColumnSchema:
    """Database column schema information."""

    name: str
    data_type: str
    description: Optional[str] = None
    sample_values: List[Any] = field(default_factory=list)
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False


@dataclass
class TableSchema:
    """Database table schema information."""

    name: str
    database_id: str
    columns: List[ColumnSchema]
    description: Optional[str] = None
    sample_queries: List[str] = field(default_factory=list)
    tier: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    row_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class QueryRequest:
    """Natural language query request."""

    query: str
    user_id: str
    database_id: str
    selected_tables: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ValidationResult:
    """SQL validation result."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    is_destructive: bool = False
    estimated_cost: Optional[float] = None
    execution_plan: Optional[str] = None


@dataclass
class OptimizationSuggestion:
    """Query optimization suggestion."""

    type: str
    description: str
    impact: str  # "high", "medium", "low"
    suggested_sql: Optional[str] = None


@dataclass
class QueryResponse:
    """Generated SQL query response."""

    sql: str
    explanation: str
    confidence_score: float
    selected_tables: List[str]
    validation_status: ValidationStatus
    optimization_suggestions: List[OptimizationSuggestion] = field(default_factory=list)
    execution_time_estimate: Optional[float] = None
    request_id: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)


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
