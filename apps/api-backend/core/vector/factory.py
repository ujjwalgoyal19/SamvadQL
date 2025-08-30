"""Vector database factory for creating database instances."""

from typing import Optional
from core.config import settings
from models import VectorProvider
from .base import VectorDatabaseInterface
from .qdrant_client import QdrantVectorDatabase
from .opensearch_client import OpenSearchVectorDatabase
import structlog

logger = structlog.get_logger(__name__)


class VectorDatabaseFactory:
    """Factory for creating vector database instances."""

    @staticmethod
    def create_vector_database(
        provider: Optional[VectorProvider] = None,
        url: Optional[str] = None,
    ) -> VectorDatabaseInterface:
        """Create a vector database instance based on provider."""

        # Use provider from settings if not specified
        if provider is None:
            provider_str = settings.vector_db_provider.lower()
            try:
                provider = VectorProvider(provider_str)
            except ValueError:
                logger.warning(
                    "Invalid vector database provider in settings, defaulting to Qdrant",
                    provider=provider_str,
                )
                provider = VectorProvider.QDRANT

        # Create appropriate database instance
        if provider == VectorProvider.QDRANT:
            return QdrantVectorDatabase(url=url or settings.qdrant_url)
        elif provider == VectorProvider.OPENSEARCH:
            return OpenSearchVectorDatabase(url=url or settings.opensearch_url)
        elif provider == VectorProvider.WEAVIATE:
            # Weaviate implementation would go here
            raise NotImplementedError("Weaviate implementation not yet available")
        else:
            raise ValueError(f"Unsupported vector database provider: {provider}")

    @staticmethod
    def get_supported_providers() -> list[VectorProvider]:
        """Get list of supported vector database providers."""
        return [VectorProvider.QDRANT, VectorProvider.OPENSEARCH]

    @staticmethod
    def is_provider_supported(provider: VectorProvider) -> bool:
        """Check if a provider is supported."""
        return provider in VectorDatabaseFactory.get_supported_providers()
