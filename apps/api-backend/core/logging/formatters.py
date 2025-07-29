"""Custom log formatters for purpose-driven logging."""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging.

    This formatter outputs log records as structured JSON with consistent
    fields including timestamp, level, purpose, message, context, and caller info.
    """

    def __init__(self, include_context: bool = True, include_caller_info: bool = True):
        """Initialize the structured formatter.

        Args:
            include_context: Whether to include context information
            include_caller_info: Whether to include caller information
        """
        super().__init__()
        self.include_context = include_context
        self.include_caller_info = include_caller_info

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log entry
        """
        # Base log entry structure
        log_entry: Dict[str, Any] = {
            "timestamp": self._format_timestamp(record.created),
            "level": record.levelname,
            "purpose": self._extract_purpose(record),
            "message": record.getMessage(),
        }

        # Add context if enabled and available
        if self.include_context:
            context = self._extract_context(record)
            if context:
                log_entry["context"] = context

        # Add caller information if enabled
        if self.include_caller_info:
            caller_info = self._get_caller_info(record)
            if caller_info:
                log_entry["caller"] = caller_info

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stack_trace": self.formatException(record.exc_info),
            }

        return json.dumps(log_entry, default=str, ensure_ascii=False)

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp in ISO format.

        Args:
            timestamp: Unix timestamp

        Returns:
            ISO-formatted timestamp string
        """
        return datetime.fromtimestamp(timestamp).isoformat() + "Z"

    def _extract_purpose(self, record: logging.LogRecord) -> str:
        """Extract purpose from logger name or record.

        Args:
            record: The log record

        Returns:
            The log purpose (api, database, llm, error, general)
        """
        # Extract purpose from logger name (e.g., "samvadql.api" -> "api")
        if hasattr(record, "purpose"):
            return record.purpose

        logger_parts = record.name.split(".")
        if len(logger_parts) > 1 and logger_parts[0] == "samvadql":
            return logger_parts[1]

        return "general"

    def _extract_context(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract context information from log record.

        Args:
            record: The log record

        Returns:
            Dictionary of context information
        """
        context = {}

        # Extract custom context attributes
        context_attrs = [
            "request_id",
            "user_id",
            "session_id",
            "operation",
            "duration_ms",
            "endpoint",
            "method",
            "status_code",
            "query",
            "table",
            "error_type",
            "component",
            "retry_count",
        ]

        for attr in context_attrs:
            if hasattr(record, attr):
                context[attr] = getattr(record, attr)

        # Extract additional context from 'extra' if present
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            context.update(record.extra)

        return context

    def _get_caller_info(self, record: logging.LogRecord) -> Optional[Dict[str, str]]:
        """Get caller information from log record.

        Args:
            record: The log record

        Returns:
            Dictionary with caller information (module, function, line)
        """
        if not (record.pathname and record.funcName and record.lineno):
            return None

        # Extract module name from pathname
        module_parts = record.pathname.replace("\\", "/").split("/")
        if "backend" in module_parts:
            # Get relative path from backend directory
            backend_idx = module_parts.index("backend")
            module_path = "/".join(module_parts[backend_idx + 1 :])
            module_name = module_path.replace(".py", "").replace("/", ".")
        else:
            module_name = record.name

        return {
            "module": module_name,
            "function": record.funcName,
            "line": str(record.lineno),
        }


class SimpleFormatter(logging.Formatter):
    """Simple text formatter for development debugging.

    Provides a more readable format for console output during development.
    """

    def __init__(self):
        """Initialize the simple formatter."""
        format_string = "%(asctime)s [%(levelname)s] %(purpose)s: %(message)s"
        super().__init__(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as simple text.

        Args:
            record: The log record to format

        Returns:
            Formatted log string
        """
        # Add purpose to record if not present
        if not hasattr(record, "purpose"):
            record.purpose = self._extract_purpose(record)

        formatted = super().format(record)

        # Add context information if available
        context_parts = []
        context_attrs = ["request_id", "operation", "duration_ms"]

        for attr in context_attrs:
            if hasattr(record, attr):
                value = getattr(record, attr)
                context_parts.append(f"{attr}={value}")

        if context_parts:
            formatted += f" [{', '.join(context_parts)}]"

        return formatted

    def _extract_purpose(self, record: logging.LogRecord) -> str:
        """Extract purpose from logger name.

        Args:
            record: The log record

        Returns:
            The log purpose
        """
        logger_parts = record.name.split(".")
        if len(logger_parts) > 1 and logger_parts[0] == "samvadql":
            return logger_parts[1]
        return "general"
