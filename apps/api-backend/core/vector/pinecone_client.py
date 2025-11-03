"""Pinecone vector database client implementation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from models import (
    VectorDocument,
    VectorHealthStatus,
    VectorIndexConfig,
    VectorSearchResult,
)

from .base import VectorDatabaseInterface

logger = logging.getLogger(__name__)


class PineconeVectorClient(VectorDatabaseInterface):
    """Pinecone vector database client with async support."""

    def __init__(
        self,
        api_key: str,
        environment: str = "us-east-1-aws",
        index_name: str = "samvadql-vectors",
        embedding_dimension: int = 1536,
        embedding_model_name: str = "text-embedding-3-small",
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize Pinecone client.

        Args:
            api_key: Pinecone API key
            environment: Cloud region/environment (e.g., 'us-east-1-aws')
            index_name: Default index name to use
            embedding_dimension: Dimension of embeddings (default 1536 for OpenAI)
            embedding_model_name: Name of embedding model (default OpenAI text-embedding-3-small)
            openai_api_key: OpenAI API key for embeddings (required for text search)
        """
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError:
            raise ImportError(
                "pinecone-client is required. Install with: pip install pinecone-client"
            )

        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.embedding_dimension = embedding_dimension
        self.embedding_model_name = embedding_model_name
        self.openai_api_key = openai_api_key
        self._client = Pinecone(api_key=api_key)
        self._connected = False
        self._serverless_spec = ServerlessSpec(cloud="aws", region=environment)

    async def connect(self) -> None:
        """Establish connection to Pinecone."""
        try:
            # Verify connection by listing indexes (non-blocking via executor)
            loop = asyncio.get_running_loop()
            indexes_response = await loop.run_in_executor(
                None, self._client.list_indexes
            )
            # Use dict access for v7 client responses
            index_names = [
                idx.get("name") for idx in indexes_response.get("indexes", [])
            ]
            self._connected = True
            logger.info(f"Connected to Pinecone. Found {len(index_names)} indexes.")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Pinecone."""
        self._connected = False
        logger.info("Disconnected from Pinecone")

    async def create_index(self, config: VectorIndexConfig) -> bool:
        """
        Create a new serverless Pinecone index.

        Args:
            config: Vector index configuration

        Returns:
            True if index was created successfully
        """
        try:
            from pinecone import ServerlessSpec

            if await self.index_exists(config.name):
                logger.warning(f"Index {config.name} already exists")
                return False

            metric = config.metric or "cosine"
            # Use configured embedding dimension for consistency
            dimension = config.dimension or self.embedding_dimension

            # Run blocking create_index call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                self._client.create_index,
                config.name,
                dimension,
                metric,
                ServerlessSpec(cloud="aws", region=self.environment),
            )

            logger.info(
                f"Created Pinecone index: {config.name} with dimension {dimension}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create index {config.name}: {e}")
            raise

    async def delete_index(self, index_name: str) -> bool:
        """
        Delete a Pinecone index.

        Args:
            index_name: Name of index to delete

        Returns:
            True if index was deleted successfully
        """
        try:
            # Run blocking delete_index call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._client.delete_index, index_name)
            logger.info(f"Deleted Pinecone index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            raise

    async def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.

        Args:
            index_name: Name of index to check

        Returns:
            True if index exists
        """
        try:
            # Run blocking list_indexes call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            indexes_response = await loop.run_in_executor(
                None, self._client.list_indexes
            )
            # Use dict access for v7 client responses
            index_names = [
                idx.get("name") for idx in indexes_response.get("indexes", [])
            ]
            return index_name in index_names
        except Exception as e:
            logger.error(f"Failed to check if index exists: {e}")
            return False

    async def upsert_document(
        self, index_name: str, document: VectorDocument, namespace: Optional[str] = None
    ) -> bool:
        """
        Insert or update a single document.

        Args:
            index_name: Target index name
            document: Vector document to upsert
            namespace: Optional namespace for multi-tenancy isolation

        Returns:
            True if successful
        """
        try:
            index = self._client.Index(index_name)
            vectors = [
                {
                    "id": document.id,
                    "values": document.vector,
                    "metadata": document.metadata or {},
                }
            ]
            # Run blocking upsert call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            if namespace:
                await loop.run_in_executor(
                    None, lambda: index.upsert(vectors, namespace=namespace)
                )
            else:
                await loop.run_in_executor(None, index.upsert, vectors)
            return True
        except Exception as e:
            logger.error(f"Failed to upsert document {document.id}: {e}")
            raise

    async def upsert_documents(
        self,
        index_name: str,
        documents: List[VectorDocument],
        namespace: Optional[str] = None,
    ) -> int:
        """
        Insert or update multiple documents.

        Args:
            index_name: Target index name
            documents: List of vector documents to upsert
            namespace: Optional namespace for multi-tenancy isolation

        Returns:
            Number of documents upserted
        """
        try:
            index = self._client.Index(index_name)

            # Convert to Pinecone format
            vectors = [
                {
                    "id": doc.id,
                    "values": doc.vector,
                    "metadata": doc.metadata or {},
                }
                for doc in documents
            ]

            # Upsert in batches (Pinecone has batch limits)
            batch_size = 100
            upserted_count = 0
            loop = asyncio.get_running_loop()

            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                # Run blocking upsert call in executor to avoid blocking event loop
                if namespace:
                    await loop.run_in_executor(
                        None, lambda: index.upsert(batch, namespace=namespace)
                    )
                else:
                    await loop.run_in_executor(None, index.upsert, batch)
                upserted_count += len(batch)

            logger.info(f"Upserted {upserted_count} documents to {index_name}")
            return upserted_count
        except Exception as e:
            logger.error(f"Failed to upsert documents: {e}")
            raise

    async def delete_document(
        self, index_name: str, document_id: str, namespace: Optional[str] = None
    ) -> bool:
        """
        Delete a document from index.

        Args:
            index_name: Target index name
            document_id: ID of document to delete
            namespace: Optional namespace for multi-tenancy isolation

        Returns:
            True if successful
        """
        try:
            index = self._client.Index(index_name)
            # Run blocking delete call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            if namespace:
                await loop.run_in_executor(
                    None, lambda: index.delete([document_id], namespace=namespace)
                )
            else:
                await loop.run_in_executor(None, index.delete, [document_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    async def search(
        self,
        index_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        namespace: Optional[str] = None,
    ) -> List[VectorSearchResult]:
        """
        Search by vector similarity.

        Args:
            index_name: Target index name
            query_vector: Query vector
            limit: Number of results to return
            filters: Metadata filters (Pinecone metadata filter expression)
            min_score: Minimum similarity score
            namespace: Optional namespace for multi-tenancy isolation

        Returns:
            List of search results
        """
        try:
            index = self._client.Index(index_name)

            # Run blocking query call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            if namespace:
                results = await loop.run_in_executor(
                    None,
                    lambda: index.query(
                        vector=query_vector,
                        top_k=limit,
                        include_metadata=True,
                        filter=filters,
                        namespace=namespace,
                    ),
                )
            else:
                results = await loop.run_in_executor(
                    None,
                    index.query,
                    query_vector,
                    limit,
                    True,
                    filters,
                )

            search_results = []
            # Use dict access for v7 client responses
            matches = results.get("matches", [])
            for match in matches:
                match_score = match.get("score", 0)
                if min_score is None or match_score >= min_score:
                    search_results.append(
                        VectorSearchResult(
                            id=match.get("id"),
                            score=match_score,
                            metadata=match.get("metadata", {}),
                        )
                    )

            return search_results
        except Exception as e:
            logger.error(f"Search failed in {index_name}: {e}")
            raise

    async def search_by_text(
        self,
        index_name: str,
        query_text: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        namespace: Optional[str] = None,
    ) -> List[VectorSearchResult]:
        """
        Search by text (will be embedded using OpenAI).

        Args:
            index_name: Target index name
            query_text: Text query
            limit: Number of results to return
            filters: Metadata filters
            min_score: Minimum similarity score
            namespace: Optional namespace for multi-tenancy isolation

        Returns:
            List of search results
        """
        try:
            if not self.openai_api_key:
                raise ValueError(
                    "OpenAI API key required for text search. Set OPENAI_API_KEY environment variable."
                )

            # Import OpenAI client
            from openai import OpenAI

            client = OpenAI(api_key=self.openai_api_key)

            # Run blocking embeddings call in executor to avoid blocking event loop
            def _create_embedding():
                response = client.embeddings.create(
                    model=self.embedding_model_name,
                    input=query_text,
                )
                return response.data[0].embedding

            loop = asyncio.get_running_loop()
            query_vector = await loop.run_in_executor(None, _create_embedding)

            return await self.search(
                index_name=index_name,
                query_vector=query_vector,
                limit=limit,
                filters=filters,
                min_score=min_score,
                namespace=namespace,
            )
        except Exception as e:
            logger.error(f"Text search failed in {index_name}: {e}")
            raise

    async def get_document(
        self, index_name: str, document_id: str
    ) -> Optional[VectorDocument]:
        """
        Retrieve a document by ID.

        Args:
            index_name: Target index name
            document_id: Document ID

        Returns:
            Vector document if found, None otherwise
        """
        try:
            index = self._client.Index(index_name)
            # Run blocking fetch call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, index.fetch, [document_id])

            # Use dict access for v7 client responses
            vectors = result.get("vectors", {})
            if vectors and document_id in vectors:
                vector_data = vectors[document_id]
                return VectorDocument(
                    id=document_id,
                    vector=vector_data.get("values", []),
                    metadata=vector_data.get("metadata", {}),
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    async def count_documents(self, index_name: str) -> int:
        """
        Count documents in an index.

        Args:
            index_name: Target index name

        Returns:
            Number of documents in index
        """
        try:
            index = self._client.Index(index_name)
            # Run blocking describe_index_stats call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            stats = await loop.run_in_executor(None, index.describe_index_stats)
            # Use dict access for v7 client responses
            return stats.get("total_vector_count", 0)
        except Exception as e:
            logger.error(f"Failed to count documents in {index_name}: {e}")
            raise

    async def health_check(self) -> VectorHealthStatus:
        """
        Perform health check on Pinecone.

        Returns:
            Health status
        """
        try:
            if not self._connected:
                await self.connect()

            # Run blocking list_indexes call in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            indexes_response = await loop.run_in_executor(
                None, self._client.list_indexes
            )
            # Use dict access for v7 client responses
            available_indexes = [
                idx.get("name") for idx in indexes_response.get("indexes", [])
            ]
            status = VectorHealthStatus(
                is_healthy=True,
                status_message="Pinecone is operational",
                available_indexes=available_indexes,
            )
            return status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return VectorHealthStatus(
                is_healthy=False,
                status_message=f"Health check failed: {str(e)}",
                available_indexes=[],
            )

    @property
    def is_connected(self) -> bool:
        """Check if connected to Pinecone."""
        return self._connected
        return self._connected
