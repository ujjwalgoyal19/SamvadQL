"""Main logging implementation for purpose-driven logging system."""

import time
import logging
import threading
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
from .config import LoggingConfig, LogPurpose, LogFormat
from .formatters import StructuredFormatter, SimpleFormatter


# Thread-local storage for context
_context_storage = threading.local()

# Global configuration
_config: Optional[LoggingConfig] = None
_loggers: Dict[str, logging.Logger] = {}


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Initialize purpose-driven logging system.

    Args:
        config: Logging configuration. If None, uses default configuration.
    """
    global _config, _loggers

    if config is None:
        config = LoggingConfig()

    _config = config
    _loggers.clear()

    # Create loggers for each purpose
    for purpose in LogPurpose:
        logger_name = f"samvadql.{purpose.value}"
        logger = logging.getLogger(logger_name)

        # Clear existing handlers
        logger.handlers.clear()

        # Set log level
        level = config.get_level_for_purpose(purpose)
        logger.setLevel(getattr(logging, level.upper()))

        # Create and configure handler
        handler = logging.StreamHandler()

        # Choose formatter based on configuration
        if config.log_format == LogFormat.STRUCTURED.value:
            formatter = StructuredFormatter(
                include_context=config.include_context,
                include_caller_info=config.include_caller_info,
            )
        else:
            formatter = SimpleFormatter()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Prevent propagation to root logger
        logger.propagate = False

        _loggers[purpose.value] = logger


def set_log_context(**context: Any) -> None:
    """Set context for current thread.

    Args:
        **context: Context key-value pairs to set
    """
    if not hasattr(_context_storage, "context"):
        _context_storage.context = {}

    _context_storage.context.update(context)


def get_log_context() -> Dict[str, Any]:
    """Get current thread context.

    Returns:
        Dictionary of current context
    """
    return getattr(_context_storage, "context", {})


def clear_log_context() -> None:
    """Clear current thread context."""
    if hasattr(_context_storage, "context"):
        _context_storage.context.clear()


def _log_with_purpose(
    purpose: LogPurpose, message: str, level: str = "INFO", **context: Any
) -> None:
    """Internal function to log with a specific purpose.

    Args:
        purpose: The log purpose
        message: Log message
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        **context: Additional context to include
    """
    # Ensure logging is initialized
    if not _loggers:
        setup_logging()

    logger = _loggers.get(purpose.value)
    if not logger:
        return

    # Merge thread context with provided context
    full_context = get_log_context().copy()
    full_context.update(context)

    # Create log record with context
    extra = {"purpose": purpose.value}
    extra.update(full_context)

    # Log at the specified level
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra)


def log_api(message: str, **context: Any) -> None:
    """Log API-related events.

    Args:
        message: Log message
        **context: Additional context (request_id, endpoint, method, status_code, etc.)
    """
    _log_with_purpose(LogPurpose.API, message, "INFO", **context)


def log_database(message: str, **context: Any) -> None:
    """Log database operations.

    Args:
        message: Log message
        **context: Additional context (query, table, duration_ms, etc.)
    """
    _log_with_purpose(LogPurpose.DATABASE, message, "DEBUG", **context)


def log_llm(message: str, **context: Any) -> None:
    """Log LLM interactions.

    Args:
        message: Log message
        **context: Additional context (model, tokens, duration_ms, etc.)
    """
    _log_with_purpose(LogPurpose.LLM, message, "INFO", **context)


def log_error(message: str, **context: Any) -> None:
    """Log errors with context.

    Args:
        message: Error message
        **context: Additional context (error_type, component, exception, etc.)
    """
    _log_with_purpose(LogPurpose.ERROR, message, "ERROR", **context)


def log_general(message: str, **context: Any) -> None:
    """Log general events.

    Args:
        message: Log message
        **context: Additional context
    """
    _log_with_purpose(LogPurpose.GENERAL, message, "INFO", **context)


@contextmanager
def log_operation(
    purpose: str, operation: str, **context: Any
) -> Generator[Dict[str, Any], None, None]:
    """Context manager for operation logging.

    Automatically logs operation start and completion with timing.

    Args:
        purpose: Log purpose (api, database, llm, error, general)
        operation: Operation name
        **context: Additional context

    Yields:
        Context dictionary that can be updated during operation

    Example:
        with log_operation("database", "user_query", user_id=123) as ctx:
            # Perform database operation
            ctx["rows_affected"] = 5
    """

    # Validate purpose
    try:
        log_purpose = LogPurpose(purpose)
    except ValueError:
        log_purpose = LogPurpose.GENERAL

    # Set up operation context
    operation_context = context.copy()
    operation_context["operation"] = operation

    # Log operation start
    _log_with_purpose(
        log_purpose, f"Starting {operation}", "DEBUG", **operation_context
    )

    start_time = time.time()

    try:
        yield operation_context

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        operation_context["duration_ms"] = round(duration_ms, 2)

        # Log successful completion
        _log_with_purpose(
            log_purpose, f"Completed {operation}", "INFO", **operation_context
        )

    except Exception as e:
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        operation_context["duration_ms"] = round(duration_ms, 2)
        operation_context["error_type"] = type(e).__name__
        operation_context["exception"] = str(e)

        # Log error
        _log_with_purpose(
            LogPurpose.ERROR, f"Failed {operation}", "ERROR", **operation_context
        )

        # Re-raise the exception
        raise
