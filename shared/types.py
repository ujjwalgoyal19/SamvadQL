"""
Shared type definitions between backend and frontend.
This file serves as a reference for maintaining consistency.
"""

from typing import Dict, Any

# Type mappings between Python and TypeScript
TYPE_MAPPINGS: Dict[str, str] = {
    # Python -> TypeScript
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "List": "Array",
    "Dict": "Record",
    "Optional": "| undefined",
    "Union": "|",
    "datetime": "string",  # ISO string format
    "uuid.UUID": "string",
    "Enum": "enum",
}

# Shared constants
DATABASE_TYPES = ["postgresql", "mysql", "snowflake", "bigquery"]

VALIDATION_STATUSES = ["valid", "invalid", "warning", "unsafe"]

FEEDBACK_TYPES = ["accept", "reject", "modify"]

# API endpoint paths
API_ENDPOINTS = {
    "QUERY": "/api/v1/query",
    "VALIDATE": "/api/v1/validate",
    "TABLES": "/api/v1/tables",
    "FEEDBACK": "/api/v1/feedback",
    "HEALTH": "/health",
}

# WebSocket event types
WEBSOCKET_EVENTS = {
    "QUERY_STREAM": "query_stream",
    "QUERY_COMPLETE": "query_complete",
    "QUERY_ERROR": "query_error",
    "TABLE_RECOMMENDATIONS": "table_recommendations",
}
