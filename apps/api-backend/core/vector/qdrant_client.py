"""Qdrant vector database implementation."""

from typing import List, Optional, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    CreateCollection,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
from qdrant_client.http.exceptions import ResponseHandlingException
import structlog

from core.config import settings
from models import (
    VectorDocument,
    VectorSearchResult,
    VectorIndexConfig,
    VectorHealthStatus,
    VectorProvider,
)
from .base import VectorDatabaseInterface

logger = structlog.get_logger(__name__)


class QdrantVectorDatabase(VectorDatabaseInterface):
    """Qdrant vector database implementation."""

    def __init__(self, url: Optional[str] = None):
        self.url = url or settings.qdrant_url
        self.client: Optional[AsyncQdrantClient] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Qdrant."""
        try:
            self.client = AsyncQdrantClient(url=self.url)

            # Test connection
            await self.client.get_collections()
            self._connected = True

            logger.info("Connected to Qdrant", url=self.url)

        except Exception as e:
            logger.error("Failed to connect to Qdrant", url=self.url, error=str(e))
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """Close connection to Qdrant."""
        if self.client:
            await self.client.close()
            self.client = None
            self._connected = False
            logger.info("Disconnected from Qdrant")

    async def create_index(self, config: VectorIndexConfig) -> bool:
        """Create a new collection in Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        try:
            # Map metric to Qdrant distance
            distance_map = {
                "cosine": Distance.COSINE,
                "euclidean": Distance.EUCLID,
                "dot_product": Distance.DOT,
                "manhattan": Distance.MANHATTAN,
            }

            distance = distance_map.get(config.metric, Distance.COSINE)

            # Create collection
            await self.client.create_collection(
                collection_name=config.name,
                vectors_config=VectorParams(
                    size=config.dimension,
                    distance=distance,
                ),
            )

            logger.info(
                "Created Qdrant collection",
                collection=config.name,
                dimension=config.dimension,
                metric=config.metric,
            )
            return True

        except ResponseHandlingException as e:
            if "already exists" in str(e).lower():
                logger.warning("Collection already exists", collection=config.name)
                return True
            logger.error(
                "Failed to create collection", collection=config.name, error=str(e)
            )
            return False
        except Exception as e:
            logger.error(
                "Failed to create collection", collection=config.name, error=str(e)
            )
            return False

    async def delete_index(self, index_name: str) -> bool:
        """Delete a collection from Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        try:
            await self.client.delete_collection(collection_name=index_name)
            logger.info("Deleted Qdrant collection", collection=index_name)
            return True

        except Exception as e:
            logger.error(
                "Failed to delete collection", collection=index_name, error=str(e)
            )
            return False

    async def index_exists(self, index_name: str) -> bool:
        """Check if a collection exists in Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        try:
            collections = await self.client.get_collections()
            return any(col.name == index_name for col in collections.collections)

        except Exception as e:
            logger.error(
                "Failed to check collection existence",
                collection=index_name,
                error=str(e),
            )
            return False

    async def upsert_document(self, index_name: str, document: VectorDocument) -> bool:
        """Insert or update a document in Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        if not document.embedding:
            raise ValueError("Document must have an embedding")

        try:
            point = PointStruct(
                id=document.id,
                vector=document.embedding,
                payload={
                    "content": document.content,
                    "metadata": document.metadata,
                    "created_at": document.created_at.isoformat(),
                },
            )

            await self.client.upsert(
                collection_name=index_name,
                points=[point],
            )

            logger.debug(
                "Upserted document to Qdrant", collection=index_name, doc_id=document.id
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to upsert document",
                collection=index_name,
                doc_id=document.id,
                error=str(e),
            )
            return False

    async def upsert_documents(
        self, index_name: str, documents: List[VectorDocument]
    ) -> int:
        """Insert or update multiple documents in Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        if not documents:
            return 0

        # Validate all documents have embeddings
        for doc in documents:
            if not doc.embedding:
                raise ValueError(f"Document {doc.id} must have an embedding")

        try:
            points = [
                PointStruct(
                    id=doc.id,
                    vector=doc.embedding,
                    payload={
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "created_at": doc.created_at.isoformat(),
                    },
                )
                for doc in documents
            ]

            await self.client.upsert(
                collection_name=index_name,
                points=points,
            )

            logger.info(
                "Upserted documents to Qdrant",
                collection=index_name,
                count=len(documents),
            )
            return len(documents)

        except Exception as e:
            logger.error(
                "Failed to upsert documents",
                collection=index_name,
                count=len(documents),
                error=str(e),
            )
            return 0

    async def delete_document(self, index_name: str, document_id: str) -> bool:
        """Delete a document from Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        try:
            await self.client.delete(
                collection_name=index_name,
                points_selector=[document_id],
            )

            logger.debug(
                "Deleted document from Qdrant",
                collection=index_name,
                doc_id=document_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to delete document",
                collection=index_name,
                doc_id=document_id,
                error=str(e),
            )
            return False

    async def search(
        self,
        index_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> List[VectorSearchResult]:
        """Search for similar vectors in Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        try:
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=f"metadata.{key}",
                            match=MatchValue(value=value),
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            # Perform search
            search_result = await self.client.search(
                collection_name=index_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=min_score,
            )

            # Convert results
            results = []
            for point in search_result:
                # Reconstruct document
                document = VectorDocument(
                    id=str(point.id),
                    content=point.payload["content"],
                    metadata=point.payload.get("metadata", {}),
                    embedding=point.vector,
                    created_at=point.payload["created_at"],
                )

                result = VectorSearchResult(
                    document=document,
                    score=point.score,
                    distance=1.0 - point.score if point.score else None,
                )
                results.append(result)

            logger.debug(
                "Performed vector search",
                collection=index_name,
                results_count=len(results),
                limit=limit,
            )
            return results

        except Exception as e:
            logger.error(
                "Failed to search vectors",
                collection=index_name,
                error=str(e),
            )
            return []

    async def search_by_text(
        self,
        index_name: str,
        query_text: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> List[VectorSearchResult]:
        """Search using text query (requires embedding service)."""
        # This method would need the embedding service to convert text to vector
        # For now, raise NotImplementedError as it requires integration with embedding service
        raise NotImplementedError(
            "Text search requires embedding service integration. Use search() with pre-computed vectors."
        )

    async def get_document(
        self, index_name: str, document_id: str
    ) -> Optional[VectorDocument]:
        """Retrieve a specific document by ID from Qdrant."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        try:
            points = await self.client.retrieve(
                collection_name=index_name,
                ids=[document_id],
                with_vectors=True,
            )

            if not points:
                return None

            point = points[0]
            document = VectorDocument(
                id=str(point.id),
                content=point.payload["content"],
                metadata=point.payload.get("metadata", {}),
                embedding=point.vector,
                created_at=point.payload["created_at"],
            )

            return document

        except Exception as e:
            logger.error(
                "Failed to get document",
                collection=index_name,
                doc_id=document_id,
                error=str(e),
            )
            return None

    async def count_documents(self, index_name: str) -> int:
        """Count documents in a collection."""
        if not self.client:
            raise RuntimeError("Not connected to Qdrant")

        try:
            info = await self.client.get_collection(collection_name=index_name)
            return info.points_count or 0

        except Exception as e:
            logger.error(
                "Failed to count documents", collection=index_name, error=str(e)
            )
            return 0

    async def health_check(self) -> VectorHealthStatus:
        """Perform health check on Qdrant."""
        try:
            if not self.client:
                return VectorHealthStatus(
                    is_healthy=False,
                    provider=VectorProvider.QDRANT,
                    connection_status="disconnected",
                    error_message="Client not initialized",
                )

            # Get collections info
            collections = await self.client.get_collections()
            total_documents = 0

            for collection in collections.collections:
                try:
                    info = await self.client.get_collection(
                        collection_name=collection.name
                    )
                    total_documents += info.points_count or 0
                except Exception:
                    # Skip collections we can't access
                    pass

            return VectorHealthStatus(
                is_healthy=True,
                provider=VectorProvider.QDRANT,
                connection_status="connected",
                index_count=len(collections.collections),
                document_count=total_documents,
            )

        except Exception as e:
            logger.error("Qdrant health check failed", error=str(e))
            return VectorHealthStatus(
                is_healthy=False,
                provider=VectorProvider.QDRANT,
                connection_status="error",
                error_message=str(e),
            )

    @property
    def is_connected(self) -> bool:
        """Check if connected to Qdrant."""
        return self._connected and self.client is not None
