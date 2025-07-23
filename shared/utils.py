"""
Shared utility functions.
"""

import re
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return uuid.uuid4().hex[:12]


def sanitize_sql(sql: str) -> str:  # type: ignore
    # WARNING: Do not attempt to sanitize SQL with regex.
    # Use parameterized queries or a proper SQL parser library to prevent SQL injection.
    raise NotImplementedError(
        "sanitize_sql is not implemented. Use parameterized queries instead."
    )


def extract_table_names(sql: str) -> List[str]:
    """Extract table names from SQL query."""
    # Simple regex to find table names after FROM and JOIN
    # Regex explanation:
    # \b(?:FROM|JOIN)\s+    : Matches 'FROM' or 'JOIN' as whole words, followed by whitespace
    # ([a-zA-Z_][a-zA-Z0-9_]* : Matches a table or schema name starting with a letter or underscore
    # (?:\.[a-zA-Z_][a-zA-Z0-9_]*)?) : Optionally matches '.tablename' for schema-qualified names
    pattern = r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)"
    matches = re.findall(pattern, sql, re.IGNORECASE)

    # Clean up schema prefixes
    tables = []
    for match in matches:
        if "." in match:
            tables.append(match.split(".")[-1])
        else:
            tables.append(match)

    return list(set(tables))  # Remove duplicates


def is_destructive_query(sql: str) -> bool:
    """Check if SQL query contains destructive operations."""
    destructive_keywords = [
        "DELETE",
        "DROP",
        "TRUNCATE",
        "ALTER",
        "UPDATE",
        "INSERT",
        "CREATE",
        "REPLACE",
    ]

    sql_upper = sql.upper()
    return any(keyword in sql_upper for keyword in destructive_keywords)


def format_error_message(
    error: Exception, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format error message for API responses."""
    return {
        "message": str(error),
        "type": type(error).__name__,
        "context": context or {},
    }


def validate_database_id(database_id: str) -> bool:
    """Validate database ID format."""
    # Simple validation - alphanumeric with hyphens and underscores
    pattern = r"^[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, database_id))


def truncate_text(text: str, max_length: int = 1000) -> str:  # type: ignore
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


BASE_CONFIDENCE_SCORE = 0.5


def calculate_confidence_score(
    validation_result: bool,
    table_match_score: float,
    llm_confidence: Optional[float] = None,
) -> float:
    """Calculate overall confidence score for query generation."""
    base_score = BASE_CONFIDENCE_SCORE

    # Validation adds/subtracts 30%
    if validation_result:
        base_score += 0.3
    else:
        base_score -= 0.3

    # Table match score contributes 40%
    base_score += table_match_score * 0.4

    # LLM confidence contributes 30% if available
    if llm_confidence is not None:
        base_score += llm_confidence * 0.3

    # Ensure score is between 0 and 1
    return max(0.0, min(1.0, base_score))
