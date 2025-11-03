"""Base vector database interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from models import (
    VectorDocument,
    VectorHealthStatus,
    VectorIndexConfig,
    VectorSearchResult,
)


class VectorDatabaseInterface(ABC):
    """Abstract base class for vector database implementations."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to vector database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to vector database."""
        pass

    @abstractmethod
    async def create_index(self, config: VectorIndexConfig) -> bool:
        """Create a new vector index."""
        pass

    @abstractmethod
    async def delete_index(self, index_name: str) -> bool:
        """Delete a vector index."""
        pass

    @abstractmethod
    async def index_exists(self, index_name: str) -> bool:
        """Check if an index exists."""
        pass

    @abstractmethod
    async def upsert_document(
        self, index_name: str, document: VectorDocument, namespace: Optional[str] = None
    ) -> bool:
        """Insert or update a document in the index."""
        pass

    @abstractmethod
    async def upsert_documents(
        self,
        index_name: str,
        documents: List[VectorDocument],
        namespace: Optional[str] = None,
    ) -> int:
        """Insert or update multiple documents in the index."""
        pass

    @abstractmethod
    async def delete_document(
        self, index_name: str, document_id: str, namespace: Optional[str] = None
    ) -> bool:
        """Delete a document from the index."""
        pass

    @abstractmethod
    async def search(
        self,
        index_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        namespace: Optional[str] = None,
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def search_by_text(
        self,
        index_name: str,
        query_text: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        namespace: Optional[str] = None,
    ) -> List[VectorSearchResult]:
        """Search using text query (will be embedded internally)."""
        pass

    @abstractmethod
    async def get_document(
        self, index_name: str, document_id: str
    ) -> Optional[VectorDocument]:
        """Retrieve a specific document by ID."""
        pass

    @abstractmethod
    async def count_documents(self, index_name: str) -> int:
        """Count documents in an index."""
        pass

    @abstractmethod
    async def health_check(self) -> VectorHealthStatus:
        """Perform health check on the vector database."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the vector database."""
        pass
        pass
