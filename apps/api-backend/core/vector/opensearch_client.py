"""OpenSearch vector database implementation."""

from typing import List, Optional, Dict, Any
from opensearchpy import AsyncOpenSearch
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


class OpenSearchVectorDatabase(VectorDatabaseInterface):
    """OpenSearch vector database implementation."""

    def __init__(self, url: Optional[str] = None):
        self.url = url or settings.opensearch_url
        self.client: Optional[AsyncOpenSearch] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to OpenSearch."""
        try:
            # Parse URL to extract host and port
            if self.url.startswith("http://"):
                host = self.url[7:]
            elif self.url.startswith("https://"):
                host = self.url[8:]
            else:
                host = self.url

            if ":" in host:
                host, port = host.split(":", 1)
                port = int(port)
            else:
                port = 9200

            self.client = AsyncOpenSearch(
                hosts=[{"host": host, "port": port}],
                use_ssl=self.url.startswith("https://"),
                verify_certs=False,  # For development
                ssl_show_warn=False,
            )

            # Test connection
            await self.client.info()
            self._connected = True

            logger.info("Connected to OpenSearch", url=self.url)

        except Exception as e:
            logger.error("Failed to connect to OpenSearch", url=self.url, error=str(e))
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """Close connection to OpenSearch."""
        if self.client:
            await self.client.close()
            self.client = None
            self._connected = False
            logger.info("Disconnected from OpenSearch")

    async def create_index(self, config: VectorIndexConfig) -> bool:
        """Create a new index in OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        try:
            # Map metric to OpenSearch space type
            space_type_map = {
                "cosine": "cosinesimil",
                "euclidean": "l2",
                "dot_product": "innerproduct",
                "manhattan": "l1",
            }

            space_type = space_type_map.get(config.metric, "cosinesimil")

            # Create index mapping
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "metadata": {"type": "object"},
                        "created_at": {"type": "date"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": config.dimension,
                            "method": {
                                "name": "hnsw",
                                "space_type": space_type,
                                "engine": "nmslib",
                            },
                        },
                    }
                },
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100,
                        "knn.algo_param.ef_construction": 128,
                        "knn.algo_param.m": 24,
                    }
                },
            }

            # Create index
            response = await self.client.indices.create(
                index=config.name, body=mapping, ignore=400
            )

            if (
                response.get("acknowledged")
                or "already exists" in str(response).lower()
            ):
                logger.info(
                    "Created OpenSearch index",
                    index=config.name,
                    dimension=config.dimension,
                    metric=config.metric,
                )
                return True
            else:
                logger.error(
                    "Failed to create index", index=config.name, response=response
                )
                return False

        except Exception as e:
            logger.error("Failed to create index", index=config.name, error=str(e))
            return False

    async def delete_index(self, index_name: str) -> bool:
        """Delete an index from OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        try:
            await self.client.indices.delete(index=index_name)
            logger.info("Deleted OpenSearch index", index=index_name)
            return True

        except Exception as e:
            logger.error("Failed to delete index", index=index_name, error=str(e))
            return False

    async def index_exists(self, index_name: str) -> bool:
        """Check if an index exists in OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        try:
            return await self.client.indices.exists(index=index_name)

        except Exception as e:
            logger.error(
                "Failed to check index existence", index=index_name, error=str(e)
            )
            return False

    async def upsert_document(self, index_name: str, document: VectorDocument) -> bool:
        """Insert or update a document in OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        if not document.embedding:
            raise ValueError("Document must have an embedding")

        try:
            doc_body = {
                "content": document.content,
                "metadata": document.metadata,
                "created_at": document.created_at.isoformat(),
                "embedding": document.embedding,
            }

            await self.client.index(
                index=index_name,
                id=document.id,
                body=doc_body,
                refresh=True,
            )

            logger.debug(
                "Upserted document to OpenSearch", index=index_name, doc_id=document.id
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to upsert document",
                index=index_name,
                doc_id=document.id,
                error=str(e),
            )
            return False

    async def upsert_documents(
        self, index_name: str, documents: List[VectorDocument]
    ) -> int:
        """Insert or update multiple documents in OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        if not documents:
            return 0

        # Validate all documents have embeddings
        for doc in documents:
            if not doc.embedding:
                raise ValueError(f"Document {doc.id} must have an embedding")

        try:
            # Prepare bulk operations
            bulk_body = []
            for doc in documents:
                bulk_body.append({"index": {"_index": index_name, "_id": doc.id}})
                bulk_body.append(
                    {
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "created_at": doc.created_at.isoformat(),
                        "embedding": doc.embedding,
                    }
                )

            # Execute bulk operation
            response = await self.client.bulk(body=bulk_body, refresh=True)

            # Count successful operations
            successful = 0
            if response.get("items"):
                for item in response["items"]:
                    if "index" in item and item["index"].get("status") in [200, 201]:
                        successful += 1

            logger.info(
                "Upserted documents to OpenSearch",
                index=index_name,
                total=len(documents),
                successful=successful,
            )
            return successful

        except Exception as e:
            logger.error(
                "Failed to upsert documents",
                index=index_name,
                count=len(documents),
                error=str(e),
            )
            return 0

    async def delete_document(self, index_name: str, document_id: str) -> bool:
        """Delete a document from OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        try:
            await self.client.delete(
                index=index_name,
                id=document_id,
                refresh=True,
            )

            logger.debug(
                "Deleted document from OpenSearch", index=index_name, doc_id=document_id
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to delete document",
                index=index_name,
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
        """Search for similar vectors in OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        try:
            # Build query
            query = {
                "size": limit,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": limit,
                        }
                    }
                },
            }

            # Add filters if provided
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append({"term": {f"metadata.{key}": value}})

                if filter_conditions:
                    query["query"] = {
                        "bool": {
                            "must": [query["query"]],
                            "filter": filter_conditions,
                        }
                    }

            # Add minimum score threshold
            if min_score is not None:
                query["min_score"] = min_score

            # Execute search
            response = await self.client.search(index=index_name, body=query)

            # Convert results
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]

                # Reconstruct document
                document = VectorDocument(
                    id=hit["_id"],
                    content=source["content"],
                    metadata=source.get("metadata", {}),
                    embedding=source.get("embedding"),
                    created_at=source["created_at"],
                )

                result = VectorSearchResult(
                    document=document,
                    score=hit["_score"],
                )
                results.append(result)

            logger.debug(
                "Performed vector search",
                index=index_name,
                results_count=len(results),
                limit=limit,
            )
            return results

        except Exception as e:
            logger.error(
                "Failed to search vectors",
                index=index_name,
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
        """Retrieve a specific document by ID from OpenSearch."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        try:
            response = await self.client.get(index=index_name, id=document_id)

            if not response.get("found"):
                return None

            source = response["_source"]
            document = VectorDocument(
                id=response["_id"],
                content=source["content"],
                metadata=source.get("metadata", {}),
                embedding=source.get("embedding"),
                created_at=source["created_at"],
            )

            return document

        except Exception as e:
            logger.error(
                "Failed to get document",
                index=index_name,
                doc_id=document_id,
                error=str(e),
            )
            return None

    async def count_documents(self, index_name: str) -> int:
        """Count documents in an index."""
        if not self.client:
            raise RuntimeError("Not connected to OpenSearch")

        try:
            response = await self.client.count(index=index_name)
            return response.get("count", 0)

        except Exception as e:
            logger.error("Failed to count documents", index=index_name, error=str(e))
            return 0

    async def health_check(self) -> VectorHealthStatus:
        """Perform health check on OpenSearch."""
        try:
            if not self.client:
                return VectorHealthStatus(
                    is_healthy=False,
                    provider=VectorProvider.OPENSEARCH,
                    connection_status="disconnected",
                    error_message="Client not initialized",
                )

            # Get cluster health
            health = await self.client.cluster.health()

            # Get indices info
            indices = await self.client.cat.indices(format="json")
            total_documents = sum(int(idx.get("docs.count", 0)) for idx in indices)

            is_healthy = health.get("status") in ["green", "yellow"]

            return VectorHealthStatus(
                is_healthy=is_healthy,
                provider=VectorProvider.OPENSEARCH,
                connection_status=health.get("status", "unknown"),
                index_count=len(indices),
                document_count=total_documents,
            )

        except Exception as e:
            logger.error("OpenSearch health check failed", error=str(e))
            return VectorHealthStatus(
                is_healthy=False,
                provider=VectorProvider.OPENSEARCH,
                connection_status="error",
                error_message=str(e),
            )

    @property
    def is_connected(self) -> bool:
        """Check if connected to OpenSearch."""
        return self._connected and self.client is not None
