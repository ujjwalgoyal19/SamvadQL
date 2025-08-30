"""Tests for vector search service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.vector_search_service import VectorSearchService
from models import (
    TableSchema,
    ColumnSchema,
    TableRecommendation,
    VectorSearchResult,
    VectorDocument,
    EmbeddingModel,
)


class TestVectorSearchService:
    """Test vector search service."""

    @pytest.fixture
    def vector_search_service(self):
        """Create vector search service instance."""
        return VectorSearchService()

    @pytest.fixture
    def mock_vector_db(self):
        """Mock vector database."""
        return AsyncMock()

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        return AsyncMock()

    @pytest.fixture
    def sample_table_schema(self):
        """Create sample table schema."""
        return TableSchema(
            name="users",
            database_id="db-123",
            columns=[
                ColumnSchema(
                    name="id",
                    data_type="integer",
                    description="User ID",
                    is_primary_key=True,
                    is_nullable=False,
                ),
                ColumnSchema(
                    name="email",
                    data_type="varchar",
                    description="User email",
                    is_nullable=False,
                ),
            ],
            description="User accounts table",
            tier="gold",
            tags=["users", "core"],
        )

    async def test_initialize(
        self, vector_search_service, mock_vector_db, mock_embedding_service
    ):
        """Test service initialization."""
        with patch(
            "services.vector_search_service.VectorDatabaseFactory"
        ) as mock_factory:
            mock_factory.create_vector_database.return_value = mock_vector_db

            with patch(
                "services.vector_search_service.EmbeddingService"
            ) as mock_embedding_class:
                mock_embedding_class.return_value = mock_embedding_service
                mock_embedding_service.get_model_dimension.return_value = 1536

                await vector_search_service.initialize()

                assert vector_search_service._initialized is True
                assert vector_search_service.vector_db == mock_vector_db
                assert vector_search_service.embedding_service == mock_embedding_service

                mock_vector_db.connect.assert_called_once()
                mock_embedding_service.initialize.assert_called_once()

    async def test_search_tables(
        self, vector_search_service, mock_vector_db, mock_embedding_service
    ):
        """Test searching for tables."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock embedding generation
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_service.generate_embedding.return_value = query_embedding

        # Mock search results
        mock_document = VectorDocument(
            id="db-123:users",
            content="Table: users | Schema: User accounts table",
            metadata={
                "table_name": "users",
                "database_id": "db-123",
                "description": "User accounts table",
                "tier": "gold",
                "tags": ["users", "core"],
            },
            embedding=query_embedding,
        )

        mock_search_result = VectorSearchResult(
            document=mock_document,
            score=0.95,
        )

        mock_vector_db.search.return_value = [mock_search_result]

        # Perform search
        results = await vector_search_service.search_tables(
            query="find user data",
            database_id="db-123",
            limit=10,
        )

        # Verify results
        assert len(results) == 1
        assert isinstance(results[0], TableRecommendation)
        assert results[0].table_schema.name == "users"
        assert results[0].relevance_score == 0.95
        assert "Semantic similarity" in results[0].match_reason

        # Verify calls
        mock_embedding_service.generate_embedding.assert_called_once_with(
            "find user data", EmbeddingModel.OPENAI_ADA_002
        )
        mock_vector_db.search.assert_called_once()

    async def test_search_tables_not_initialized(self, vector_search_service):
        """Test searching tables when service not initialized."""
        with pytest.raises(RuntimeError, match="Vector search service not initialized"):
            await vector_search_service.search_tables("test query", "db-123")

    async def test_rerank_tables(
        self, vector_search_service, mock_embedding_service, sample_table_schema
    ):
        """Test re-ranking tables."""
        # Setup mocks
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock embeddings
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        table_embedding = [0.2, 0.3, 0.4, 0.5]

        mock_embedding_service.generate_embedding.side_effect = [
            query_embedding,  # For query
            table_embedding,  # For table
        ]
        mock_embedding_service.calculate_similarity.return_value = 0.85

        # Test re-ranking
        candidates = [sample_table_schema]
        results = await vector_search_service.rerank_tables("find users", candidates)

        assert len(results) == 1
        assert results[0] == sample_table_schema

        # Verify embedding calls
        assert mock_embedding_service.generate_embedding.call_count == 2
        mock_embedding_service.calculate_similarity.assert_called_once_with(
            query_embedding, table_embedding
        )

    async def test_rerank_tables_empty_candidates(self, vector_search_service):
        """Test re-ranking with empty candidates."""
        results = await vector_search_service.rerank_tables("test query", [])
        assert results == []

    async def test_index_table(
        self,
        vector_search_service,
        mock_vector_db,
        mock_embedding_service,
        sample_table_schema,
    ):
        """Test indexing a table."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock embedding
        mock_document = VectorDocument(
            id="db-123:users",
            content="test content",
            metadata={},
            embedding=[0.1, 0.2, 0.3, 0.4],
        )
        mock_embedding_service.embed_document.return_value = mock_document
        mock_vector_db.upsert_document.return_value = True

        # Index table
        await vector_search_service.index_table(
            sample_table_schema, "User accounts summary"
        )

        # Verify calls
        mock_embedding_service.embed_document.assert_called_once()
        mock_vector_db.upsert_document.assert_called_once_with(
            vector_search_service.table_index, mock_document
        )

    async def test_index_query(
        self, vector_search_service, mock_vector_db, mock_embedding_service
    ):
        """Test indexing a query."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock embedding
        mock_document = VectorDocument(
            id="query_123",
            content="test content",
            metadata={},
            embedding=[0.1, 0.2, 0.3, 0.4],
        )
        mock_embedding_service.embed_document.return_value = mock_document
        mock_vector_db.upsert_document.return_value = True

        # Index query
        await vector_search_service.index_query(
            query="find all users",
            sql="SELECT * FROM users",
            tables=["users"],
        )

        # Verify calls
        mock_embedding_service.embed_document.assert_called_once()
        mock_vector_db.upsert_document.assert_called_once_with(
            vector_search_service.query_index, mock_document
        )

    async def test_search_similar_queries(
        self, vector_search_service, mock_vector_db, mock_embedding_service
    ):
        """Test searching for similar queries."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock embedding generation
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        mock_embedding_service.generate_embedding.return_value = query_embedding

        # Mock search results
        mock_document = VectorDocument(
            id="query_123",
            content="Query: find users | SQL: SELECT * FROM users",
            metadata={"tables_used": ["users"]},
            embedding=query_embedding,
        )

        mock_search_result = VectorSearchResult(
            document=mock_document,
            score=0.88,
        )

        mock_vector_db.search.return_value = [mock_search_result]

        # Perform search
        results = await vector_search_service.search_similar_queries(
            "find all users", limit=5
        )

        # Verify results
        assert len(results) == 1
        assert isinstance(results[0], VectorSearchResult)
        assert results[0].score == 0.88

        # Verify calls
        mock_embedding_service.generate_embedding.assert_called_once_with(
            "find all users", EmbeddingModel.OPENAI_ADA_002
        )
        mock_vector_db.search.assert_called_once()

    async def test_health_check(
        self, vector_search_service, mock_vector_db, mock_embedding_service
    ):
        """Test health check."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock health check responses
        mock_embedding_service.health_check.return_value = {
            "openai_available": True,
            "sentence_transformer_available": True,
        }

        from models import VectorHealthStatus, VectorProvider

        mock_vector_health = VectorHealthStatus(
            is_healthy=True,
            provider=VectorProvider.QDRANT,
            connection_status="connected",
            index_count=2,
            document_count=100,
        )
        mock_vector_db.health_check.return_value = mock_vector_health
        mock_vector_db.index_exists.return_value = True
        mock_vector_db.count_documents.return_value = 50

        # Perform health check
        status = await vector_search_service.health_check()

        # Verify status
        assert status["initialized"] is True
        assert status["embedding_service"]["openai_available"] is True
        assert status["vector_database"]["is_healthy"] is True
        assert status["indices"]["table_index_exists"] is True
        assert status["indices"]["query_index_exists"] is True

    async def test_ensure_indices_exist(self, vector_search_service, mock_vector_db):
        """Test ensuring indices exist."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service._initialized = True

        # Mock index existence checks
        mock_vector_db.index_exists.side_effect = [
            False,
            False,
        ]  # Both indices don't exist
        mock_vector_db.create_index.return_value = True

        # Call private method
        await vector_search_service._ensure_indices_exist()

        # Verify index creation calls
        assert mock_vector_db.create_index.call_count == 2
        assert mock_vector_db.index_exists.call_count == 2

    def test_extract_query_type(self, vector_search_service):
        """Test extracting query type from SQL."""
        assert (
            vector_search_service._extract_query_type("SELECT * FROM users") == "SELECT"
        )
        assert (
            vector_search_service._extract_query_type("INSERT INTO users VALUES (1)")
            == "INSERT"
        )
        assert (
            vector_search_service._extract_query_type("UPDATE users SET name = 'test'")
            == "UPDATE"
        )
        assert (
            vector_search_service._extract_query_type("DELETE FROM users WHERE id = 1")
            == "DELETE"
        )
        assert (
            vector_search_service._extract_query_type("CREATE TABLE test (id INT)")
            == "CREATE"
        )
        assert (
            vector_search_service._extract_query_type(
                "WITH cte AS (SELECT * FROM users) SELECT * FROM cte"
            )
            == "SELECT"
        )
        assert vector_search_service._extract_query_type("INVALID SQL") == "UNKNOWN"

    async def test_shutdown(self, vector_search_service, mock_vector_db):
        """Test service shutdown."""
        vector_search_service.vector_db = mock_vector_db
        vector_search_service._initialized = True

        await vector_search_service.shutdown()

        assert vector_search_service._initialized is False
        mock_vector_db.disconnect.assert_called_once()

    async def test_error_handling_in_search(
        self, vector_search_service, mock_vector_db, mock_embedding_service
    ):
        """Test error handling in search operations."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock embedding service to raise exception
        mock_embedding_service.generate_embedding.side_effect = Exception(
            "Embedding failed"
        )

        # Search should return empty list on error
        results = await vector_search_service.search_tables("test query", "db-123")
        assert results == []

    async def test_error_handling_in_indexing(
        self,
        vector_search_service,
        mock_vector_db,
        mock_embedding_service,
        sample_table_schema,
    ):
        """Test error handling in indexing operations."""
        # Setup mocks
        vector_search_service.vector_db = mock_vector_db
        vector_search_service.embedding_service = mock_embedding_service
        vector_search_service._initialized = True

        # Mock embedding service to raise exception
        mock_embedding_service.embed_document.side_effect = Exception(
            "Embedding failed"
        )

        # Indexing should not raise exception (error is logged)
        await vector_search_service.index_table(sample_table_schema, "test summary")

        # Verify embedding was attempted
        mock_embedding_service.embed_document.assert_called_once()
