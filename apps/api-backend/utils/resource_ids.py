"""
Resource ID utilities for consistent resource identification across the ABAC system.

This module provides helper functions to format and parse resource IDs in a standardized way.
Resource IDs are used to uniquely identify resources in the permission system.

Format Conventions:
- Database: "database_id" (e.g., "prod_db", "analytics_db")
- Table: "database_id:table_name" (e.g., "prod_db:users", "analytics_db:orders")
- Column: "database_id:table_name:column_name" (e.g., "prod_db:users:email")
- Query: "query_id" (e.g., "q_12345")
- API: "api_endpoint" (e.g., "/api/v1/query")
"""

from typing import Tuple, Optional


def format_table_resource_id(database_id: str, table_name: str) -> str:
    """
    Format a table resource ID in the standard convention.

    Args:
        database_id: The database identifier
        table_name: The table name

    Returns:
        Formatted resource ID: "database_id:table_name"

    Example:
        >>> format_table_resource_id("prod_db", "users")
        "prod_db:users"
    """
    if not database_id or not table_name:
        raise ValueError("Both database_id and table_name must be non-empty")

    # Ensure no colons in individual components to avoid ambiguity
    if ":" in database_id:
        raise ValueError(f"database_id cannot contain ':' character: {database_id}")
    if ":" in table_name:
        raise ValueError(f"table_name cannot contain ':' character: {table_name}")

    return f"{database_id}:{table_name}"


def parse_table_resource_id(resource_id: str) -> Tuple[str, str]:
    """
    Parse a table resource ID into its components.

    Args:
        resource_id: The resource ID in format "database_id:table_name"

    Returns:
        Tuple of (database_id, table_name)

    Raises:
        ValueError: If the resource_id format is invalid

    Example:
        >>> parse_table_resource_id("prod_db:users")
        ("prod_db", "users")
    """
    if not resource_id:
        raise ValueError("resource_id cannot be empty")

    parts = resource_id.split(":", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid table resource_id format: '{resource_id}'. "
            "Expected format: 'database_id:table_name'"
        )

    database_id, table_name = parts

    if not database_id or not table_name:
        raise ValueError(
            f"Invalid table resource_id: '{resource_id}'. "
            "Both database_id and table_name must be non-empty"
        )

    return database_id, table_name


def format_column_resource_id(database_id: str, table_name: str, column_name: str) -> str:
    """
    Format a column resource ID in the standard convention.

    Args:
        database_id: The database identifier
        table_name: The table name
        column_name: The column name

    Returns:
        Formatted resource ID: "database_id:table_name:column_name"

    Example:
        >>> format_column_resource_id("prod_db", "users", "email")
        "prod_db:users:email"
    """
    if not database_id or not table_name or not column_name:
        raise ValueError("database_id, table_name, and column_name must all be non-empty")

    # Ensure no colons in individual components
    for name, value in [("database_id", database_id), ("table_name", table_name), ("column_name", column_name)]:
        if ":" in value:
            raise ValueError(f"{name} cannot contain ':' character: {value}")

    return f"{database_id}:{table_name}:{column_name}"


def parse_column_resource_id(resource_id: str) -> Tuple[str, str, str]:
    """
    Parse a column resource ID into its components.

    Args:
        resource_id: The resource ID in format "database_id:table_name:column_name"

    Returns:
        Tuple of (database_id, table_name, column_name)

    Raises:
        ValueError: If the resource_id format is invalid

    Example:
        >>> parse_column_resource_id("prod_db:users:email")
        ("prod_db", "users", "email")
    """
    if not resource_id:
        raise ValueError("resource_id cannot be empty")

    parts = resource_id.split(":", 2)
    if len(parts) != 3:
        raise ValueError(
            f"Invalid column resource_id format: '{resource_id}'. "
            "Expected format: 'database_id:table_name:column_name'"
        )

    database_id, table_name, column_name = parts

    if not database_id or not table_name or not column_name:
        raise ValueError(
            f"Invalid column resource_id: '{resource_id}'. "
            "All components (database_id, table_name, column_name) must be non-empty"
        )

    return database_id, table_name, column_name


def validate_resource_id(resource_id: str, resource_type: str) -> bool:
    """
    Validate a resource ID for a given resource type.

    Args:
        resource_id: The resource ID to validate
        resource_type: The resource type ("database", "table", "column", "query", "api")

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_resource_id("prod_db:users", "table")
        True
        >>> validate_resource_id("prod_db", "table")
        False
    """
    try:
        if resource_type == "table":
            parse_table_resource_id(resource_id)
            return True
        elif resource_type == "column":
            parse_column_resource_id(resource_id)
            return True
        elif resource_type == "database":
            return bool(resource_id and ":" not in resource_id)
        elif resource_type in ("query", "api"):
            return bool(resource_id)
        else:
            return False
    except ValueError:
        return False
