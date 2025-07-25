"""Audit and feedback models for SamvadQL."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from .enums import DatabaseType


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
