"""Vector database factory for creating database instances."""

import structlog
from core.config import settings

from .base import VectorDatabaseInterface
from .pinecone_client import PineconeVectorClient

logger = structlog.get_logger(__name__)


class PineconeConfigurationError(Exception):
    """Raised when Pinecone configuration is invalid or incomplete."""
    pass


def _validate_pinecone_settings() -> None:
    """
    Validate Pinecone settings at startup to fail fast.

    Raises:
        PineconeConfigurationError: If any required setting is missing or invalid.
    """
    errors = []

    # Validate API key (required)
    if not settings.pinecone_api_key or settings.pinecone_api_key.strip() == "":
        errors.append(
            "PINECONE_API_KEY is required. Set the environment variable and restart the application."
        )

    # Validate index name (required)
    if not settings.pinecone_index_name or settings.pinecone_index_name.strip() == "":
        errors.append(
            "PINECONE_INDEX_NAME is required. Set the environment variable and restart the application."
        )

    # Validate environment string (should not be empty)
    if not settings.pinecone_environment or settings.pinecone_environment.strip() == "":
        errors.append(
            "PINECONE_ENVIRONMENT is required. Set the environment variable and restart the application."
        )

    # If any errors, raise with all of them
    if errors:
        error_message = "Pinecone configuration validation failed:\n  - " + "\n  - ".join(
            errors
        )
        logger.error("pinecone_validation_failed", errors=errors)
        raise PineconeConfigurationError(error_message)

    logger.info(
        "pinecone_settings_valid",
        index_name=settings.pinecone_index_name,
        environment=settings.pinecone_environment,
    )


class VectorDatabaseFactory:
    """Factory for creating vector database instances."""

    @staticmethod
    def create_vector_database() -> VectorDatabaseInterface:
        """
        Create a Pinecone vector database instance.

        Validates Pinecone settings at startup to fail fast on configuration errors.

        Returns:
            PineconeVectorClient: Configured and validated Pinecone client.

        Raises:
            PineconeConfigurationError: If Pinecone settings are missing or invalid.
        """
        # Validate settings before creating client
        _validate_pinecone_settings()

        logger.info("Creating Pinecone vector database client")
        return PineconeVectorClient(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
            index_name=settings.pinecone_index_name,
        )
            index_name=settings.pinecone_index_name,
        )
