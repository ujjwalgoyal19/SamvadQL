"""Configuration management for SamvadQL backend."""

from pathlib import Path
from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (three levels up from this file to reach repository root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    api_title: str = "SamvadQL API"
    api_version: str = "1.0.0"
    api_description: str = "Text-to-SQL conversational interface"
    debug: bool = False

    # Database Configuration
    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    redis_url: str = Field(
        default="redis://localhost:6379", validation_alias="REDIS_URL"
    )

    # LLM Configuration
    openai_api_key: Optional[str] = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None, validation_alias="ANTHROPIC_API_KEY"
    )
    llm_provider: str = Field(
        default="openai", validation_alias="LLM_PROVIDER"
    )  # openai, anthropic, azure, etc.
    llm_model: str = Field(default="gpt-4", validation_alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.1, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, validation_alias="LLM_MAX_TOKENS")

    # Vector Database Configuration (Pinecone)
    pinecone_api_key: str = Field(default="", validation_alias="PINECONE_API_KEY")
    pinecone_environment: str = Field(
        default="us-east-1-aws", validation_alias="PINECONE_ENVIRONMENT"
    )
    pinecone_index_name: str = Field(
        default="samvadql-vectors", validation_alias="PINECONE_INDEX_NAME"
    )

    # Embedding Configuration
    embedding_model_name: str = Field(
        default="text-embedding-3-small", validation_alias="EMBEDDING_MODEL_NAME"
    )  # OpenAI model for embeddings
    embedding_dimension: int = Field(
        default=1536, validation_alias="EMBEDDING_DIMENSION"
    )  # Dimension for OpenAI embeddings

    # Security
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        validation_alias="SECRET_KEY",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    allowed_origins: Union[List[str], str] = Field(
        default=["http://localhost:3000"], validation_alias="ALLOWED_ORIGINS"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
            # Already JSON format, let pydantic handle it
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Performance
    max_concurrent_requests: int = Field(
        default=100, validation_alias="MAX_CONCURRENT_REQUESTS"
    )
    query_timeout_seconds: int = Field(
        default=30, validation_alias="QUERY_TIMEOUT_SECONDS"
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), case_sensitive=False, extra="ignore"
    )


settings = Settings()
