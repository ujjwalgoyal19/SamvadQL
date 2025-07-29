"""Purpose-driven logging system for SamvadQL backend.

This module provides a simple, static logging system with predefined purpose categories
to help developers debug and understand system behavior.

Public API:
    - log_api(): Log API-related events
    - log_database(): Log database operations
    - log_llm(): Log LLM interactions
    - log_error(): Log errors with context
    - log_general(): Log general events
    - setup_logging(): Initialize the logging system
    - LoggingConfig: Configuration class
"""

from .logger import (
    log_api,
    log_database,
    log_llm,
    log_error,
    log_general,
    setup_logging,
    log_operation,
)
from .config import LoggingConfig

__all__ = [
    "log_api",
    "log_database",
    "log_llm",
    "log_error",
    "log_general",
    "setup_logging",
    "log_operation",
    "LoggingConfig",
]
