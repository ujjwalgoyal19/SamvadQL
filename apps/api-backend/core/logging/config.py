"""Logging configuration for purpose-driven logging system."""

from enum import Enum
from typing import Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class LogPurpose(Enum):
    """Predefined log purposes."""

    API = "api"
    DATABASE = "database"
    LLM = "llm"
    ERROR = "error"
    GENERAL = "general"


class LogFormat(Enum):
    """Available log formats."""

    STRUCTURED = "structured"
    SIMPLE = "simple"


class LoggingConfig(BaseSettings):
    """Configuration for purpose-driven logging system.

    This class manages logging configuration with support for:
    - Per-purpose log levels
    - Environment variable integration
    - Output format configuration
    - Context inclusion settings
    """

    # Log levels per purpose
    api_level: str = Field(default="INFO", validation_alias="LOG_API_LEVEL")
    database_level: str = Field(default="DEBUG", validation_alias="LOG_DATABASE_LEVEL")
    llm_level: str = Field(default="INFO", validation_alias="LOG_LLM_LEVEL")
    error_level: str = Field(default="ERROR", validation_alias="LOG_ERROR_LEVEL")
    general_level: str = Field(default="INFO", validation_alias="LOG_GENERAL_LEVEL")

    # Global log configuration
    log_format: str = Field(default="structured", validation_alias="LOG_FORMAT")
    include_context: bool = Field(default=True, validation_alias="LOG_INCLUDE_CONTEXT")
    include_caller_info: bool = Field(
        default=True, validation_alias="LOG_INCLUDE_CALLER_INFO"
    )

    # Environment-based defaults
    debug: bool = Field(default=False, validation_alias="DEBUG")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Apply environment-based defaults after initialization
        self._apply_environment_defaults()

    def _apply_environment_defaults(self) -> None:
        """Apply environment-based default log levels."""
        if self.debug:
            # Development mode - more verbose logging
            self.api_level = getattr(self, "api_level", None) or "DEBUG"
            self.database_level = getattr(self, "database_level", None) or "DEBUG"
            self.llm_level = getattr(self, "llm_level", None) or "DEBUG"
            self.error_level = getattr(self, "error_level", None) or "DEBUG"
            self.general_level = getattr(self, "general_level", None) or "DEBUG"
        else:
            # Production mode - less verbose logging
            self.api_level = getattr(self, "api_level", None) or "INFO"
            self.database_level = getattr(self, "database_level", None) or "INFO"
            self.llm_level = getattr(self, "llm_level", None) or "INFO"
            self.error_level = getattr(self, "error_level", None) or "ERROR"
            self.general_level = getattr(self, "general_level", None) or "INFO"

    def get_level_for_purpose(self, purpose: LogPurpose) -> str:
        """Get the configured log level for a specific purpose."""
        level_mapping = {
            LogPurpose.API: self.api_level,
            LogPurpose.DATABASE: self.database_level,
            LogPurpose.LLM: self.llm_level,
            LogPurpose.ERROR: self.error_level,
            LogPurpose.GENERAL: self.general_level,
        }
        return level_mapping.get(purpose, "INFO")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for easy access."""
        return {
            "levels": {
                "api": self.api_level,
                "database": self.database_level,
                "llm": self.llm_level,
                "error": self.error_level,
                "general": self.general_level,
            },
            "format": self.log_format,
            "include_context": self.include_context,
            "include_caller_info": self.include_caller_info,
            "debug": self.debug,
        }

    class Config:
        case_sensitive = False
        extra = "ignore"
        env_prefix = ""  # Allow both prefixed and non-prefixed env vars
