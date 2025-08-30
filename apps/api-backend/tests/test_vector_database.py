"""Tests for vector database implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List

from models import (
    VectorDocument,
    VectorSearchResult,
    VectorIndexConfig,
    VectorProvider,
    EmbeddingModel,
    VectorHealthStatus,
)
from core.vector.qdrant_client import QdrantVectorDatabase
from core.vector.opensearch_client import OpenSearchVectorDatabase
from core.vector.factory import VectorDatabaseFactory


class TestVectorDocument:
    """Test VectorDocument model."""

    def test_vector_document_creation(self):
        """Test creating a vector document."""
        doc = VectorDocument(
            id="test-doc-1",
            content="This is a test document",
            metadata={"type": "test"},
            embedding=[0.1, 0.2, 0.3],
        )

        assert doc.id == "test-doc-1"
        assert doc.content == "This is a test document"
        assert doc.metadata == {"type": "test"}
        assert doc.embedding == [0.1, 0.2, 0.3]
        assert isinstance(doc.created_at, datetime)

    def test_vector_document_validation(self):
        """Test vector document validation."""
        # Empty content should raise error
        with pytest.raises(ValueError, match="Content cannot be empty"):
            VectorDocument(id="test", content="", metadata={})

        # Whitespace-only content should raise error
        with pytest.raises(ValueError, match="Content cannot be empty"):
            VectorDocument(id="test", content="   ", metadata={})


class TestVectorIndexConfig:
    """Test VectorIndexConfig model."""

    def test_index_config_creation(self):
        """Test creating a vector index config."""
        config = VectorIndexConfig(
            name="test-index",
            dimension=1536,
            metric="cosine",
            provider=VectorProvider.QDRANT,
            embedding_model=EmbeddingModel.OPENAI_ADA_002,
        )

        assert config.name == "test-index"
        assert config.dimension == 1536
        assert config.metric == "cosine"
        assert config.provider == VectorProvider.QDRANT

    def test_index_config_validation(self):
        """Test index config validation."""
        # Invalid metric should raise error
        with pytest.raises(ValueError, match="Metric must be one of"):
            VectorIndexConfig(
                name="test",
                dimension=1536,
                metric="invalid",
                provider=VectorProvider.QDRANT,
                embedding_model=EmbeddingModel.OPENAI_ADA_002,
            )

        # Zero dimension should raise error
        with pytest.raises(ValueError):
            VectorIndexConfig(
                name="test",
                dimension=0,
                metric="cosine",
                provider=VectorProvider.QDRANT,
                embedding_model=EmbeddingModel.OPENAI_ADA_002,
            )


class TestQdrantVectorDatabase:
    """Test Qdrant vector database implementation."""

    @pytest.fixture
    def qdrant_db(self):
        """Create Qdrant database instance."""
        return QdrantVectorDatabase("http://localhost:6333")

    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client."""
        with patch("core.vector.qdrant_client.AsyncQdrantClient") as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def sample_document(self):
        """Create sample vector document."""
        return VectorDocument(
            id="test-doc-1",
            content="Sample document content",
            metadata={"type": "test", "category": "sample"},
            embedding=[0.1, 0.2, 0.3, 0.4],
        )

    @pytest.fixture
    def sample_config(self):
        """Create sample index config."""
        return VectorIndexConfig(
            name="test-index",
            dimension=4,
            metric="cosine",
            provider=VectorProvider.QDRANT,
            embedding_model=EmbeddingModel.OPENAI_ADA_002,
        )

    async def test_connect(self, qdrant_db, mock_qdrant_client):
        """Test connecting to Qdrant."""
        mock_qdrant_client.get_collections.return_value = MagicMock()

        await qdrant_db.connect()

        assert qdrant_db.is_connected
        mock_qdrant_client.get_collections.assert_called_once()

    async def test_connect_failure(self, qdrant_db, mock_qdrant_client):
        """Test connection failure."""
        mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            await qdrant_db.connect()

        assert not qdrant_db.is_connected

    async def test_create_index(self, qdrant_db, mock_qdrant_client, sample_config):
        """Test creating an index."""
        qdrant_db.client = mock_qdrant_client
        qdrant_db._connected = True

        mock_qdrant_client.create_collection.return_value = None

        result = await qdrant_db.create_index(sample_config)

        assert result is True
        mock_qdrant_client.create_collection.assert_called_once()

    async def test_upsert_document(
        self, qdrant_db, mock_qdrant_client, sample_document
    ):
        """Test upserting a document."""
        qdrant_db.client = mock_qdrant_client
        qdrant_db._connected = True

        mock_qdrant_client.upsert.return_value = None

        result = await qdrant_db.upsert_document("test-index", sample_document)

        assert result is True
        mock_qdrant_client.upsert.assert_called_once()

    async def test_upsert_document_without_embedding(
        self, qdrant_db, mock_qdrant_client
    ):
        """Test upserting document without embedding fails."""
        qdrant_db.client = mock_qdrant_client
        qdrant_db._connected = True

        doc = VectorDocument(
            id="test",
            content="test content",
            metadata={},
        )

        with pytest.raises(ValueError, match="Document must have an embedding"):
            await qdrant_db.upsert_document("test-index", doc)

    async def test_search(self, qdrant_db, mock_qdrant_client):
        """Test vector search."""
        qdrant_db.client = mock_qdrant_client
        qdrant_db._connected = True

        # Mock search result
        mock_point = MagicMock()
        mock_point.id = "test-doc-1"
        mock_point.score = 0.95
        mock_point.vector = [0.1, 0.2, 0.3, 0.4]
        mock_point.payload = {
            "content": "Test content",
            "metadata": {"type": "test"},
            "created_at": "2024-01-01T00:00:00",
        }

        mock_qdrant_client.search.return_value = [mock_point]

        results = await qdrant_db.search(
            index_name="test-index",
            query_vector=[0.1, 0.2, 0.3, 0.4],
            limit=10,
        )

        assert len(results) == 1
        assert isinstance(results[0], VectorSearchResult)
        assert results[0].document.id == "test-doc-1"
        assert results[0].score == 0.95

    async def test_health_check(self, qdrant_db, mock_qdrant_client):
        """Test health check."""
        qdrant_db.client = mock_qdrant_client
        qdrant_db._connected = True

        # Mock collections response
        mock_collections = MagicMock()
        mock_collections.collections = [MagicMock(name="test-index")]
        mock_qdrant_client.get_collections.return_value = mock_collections

        # Mock collection info
        mock_info = MagicMock()
        mock_info.points_count = 100
        mock_qdrant_client.get_collection.return_value = mock_info

        health = await qdrant_db.health_check()

        assert isinstance(health, VectorHealthStatus)
        assert health.is_healthy is True
        assert health.provider == VectorProvider.QDRANT
        assert health.index_count == 1
        assert health.document_count == 100


class TestOpenSearchVectorDatabase:
    """Test OpenSearch vector database implementation."""

    @pytest.fixture
    def opensearch_db(self):
        """Create OpenSearch database instance."""
        return OpenSearchVectorDatabase("http://localhost:9200")

    @pytest.fixture
    def mock_opensearch_client(self):
        """Mock OpenSearch client."""
        with patch("core.vector.opensearch_client.AsyncOpenSearch") as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client

    async def test_connect(self, opensearch_db, mock_opensearch_client):
        """Test connecting to OpenSearch."""
        mock_opensearch_client.info.return_value = {"version": {"number": "2.0.0"}}

        await opensearch_db.connect()

        assert opensearch_db.is_connected
        mock_opensearch_client.info.assert_called_once()

    async def test_create_index(self, opensearch_db, mock_opensearch_client):
        """Test creating an index."""
        opensearch_db.client = mock_opensearch_client
        opensearch_db._connected = True

        config = VectorIndexConfig(
            name="test-index",
            dimension=4,
            metric="cosine",
            provider=VectorProvider.OPENSEARCH,
            embedding_model=EmbeddingModel.OPENAI_ADA_002,
        )

        mock_opensearch_client.indices.create.return_value = {"acknowledged": True}

        result = await opensearch_db.create_index(config)

        assert result is True
        mock_opensearch_client.indices.create.assert_called_once()

    async def test_search(self, opensearch_db, mock_opensearch_client):
        """Test vector search."""
        opensearch_db.client = mock_opensearch_client
        opensearch_db._connected = True

        # Mock search response
        mock_response = {
            "hits": {
                "hits": [
                    {
                        "_id": "test-doc-1",
                        "_score": 0.95,
                        "_source": {
                            "content": "Test content",
                            "metadata": {"type": "test"},
                            "created_at": "2024-01-01T00:00:00",
                            "embedding": [0.1, 0.2, 0.3, 0.4],
                        },
                    }
                ]
            }
        }

        mock_opensearch_client.search.return_value = mock_response

        results = await opensearch_db.search(
            index_name="test-index",
            query_vector=[0.1, 0.2, 0.3, 0.4],
            limit=10,
        )

        assert len(results) == 1
        assert isinstance(results[0], VectorSearchResult)
        assert results[0].document.id == "test-doc-1"
        assert results[0].score == 0.95


class TestVectorDatabaseFactory:
    """Test vector database factory."""

    def test_create_qdrant_database(self):
        """Test creating Qdrant database."""
        db = VectorDatabaseFactory.create_vector_database(VectorProvider.QDRANT)
        assert isinstance(db, QdrantVectorDatabase)

    def test_create_opensearch_database(self):
        """Test creating OpenSearch database."""
        db = VectorDatabaseFactory.create_vector_database(VectorProvider.OPENSEARCH)
        assert isinstance(db, OpenSearchVectorDatabase)

    def test_create_unsupported_database(self):
        """Test creating unsupported database raises error."""
        with pytest.raises(NotImplementedError):
            VectorDatabaseFactory.create_vector_database(VectorProvider.WEAVIATE)

    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = VectorDatabaseFactory.get_supported_providers()
        assert VectorProvider.QDRANT in providers
        assert VectorProvider.OPENSEARCH in providers

    def test_is_provider_supported(self):
        """Test checking if provider is supported."""
        assert VectorDatabaseFactory.is_provider_supported(VectorProvider.QDRANT)
        assert VectorDatabaseFactory.is_provider_supported(VectorProvider.OPENSEARCH)
        assert not VectorDatabaseFactory.is_provider_supported(VectorProvider.WEAVIATE)


@pytest.mark.asyncio
class TestVectorDatabaseIntegration:
    """Integration tests for vector database operations."""

    @pytest.fixture
    async def vector_db(self):
        """Create and connect to vector database for testing."""
        # Use Qdrant for integration tests
        db = VectorDatabaseFactory.create_vector_database(VectorProvider.QDRANT)

        # Mock the connection for testing
        with patch.object(db, "connect") as mock_connect:
            mock_connect.return_value = None
            db._connected = True
            db.client = AsyncMock()
            yield db

    async def test_full_document_lifecycle(self, vector_db):
        """Test complete document lifecycle: create, upsert, search, delete."""
        # Create test index
        config = VectorIndexConfig(
            name="test-lifecycle",
            dimension=4,
            metric="cosine",
            provider=VectorProvider.QDRANT,
            embedding_model=EmbeddingModel.OPENAI_ADA_002,
        )

        vector_db.client.create_collection.return_value = None
        await vector_db.create_index(config)

        # Create test document
        doc = VectorDocument(
            id="lifecycle-test",
            content="Test document for lifecycle",
            metadata={"test": "lifecycle"},
            embedding=[0.1, 0.2, 0.3, 0.4],
        )

        # Upsert document
        vector_db.client.upsert.return_value = None
        result = await vector_db.upsert_document("test-lifecycle", doc)
        assert result is True

        # Search for document
        mock_point = MagicMock()
        mock_point.id = "lifecycle-test"
        mock_point.score = 0.99
        mock_point.vector = [0.1, 0.2, 0.3, 0.4]
        mock_point.payload = {
            "content": "Test document for lifecycle",
            "metadata": {"test": "lifecycle"},
            "created_at": doc.created_at.isoformat(),
        }
        vector_db.client.search.return_value = [mock_point]

        search_results = await vector_db.search(
            "test-lifecycle", [0.1, 0.2, 0.3, 0.4], limit=1
        )
        assert len(search_results) == 1
        assert search_results[0].document.id == "lifecycle-test"

        # Delete document
        vector_db.client.delete.return_value = None
        delete_result = await vector_db.delete_document(
            "test-lifecycle", "lifecycle-test"
        )
        assert delete_result is True
