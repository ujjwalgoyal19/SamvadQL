"""Tests for semantic search service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.semantic_search_service import SemanticSearchService
from models import (
    TableSchema,
    ColumnSchema,
    TableRecommendation,
    VectorSearchResult,
    VectorDocument,
)


class TestSemanticSearchService:
    """Test semantic search service."""

    @pytest.fixture
    def semantic_search_service(self):
        """Create semantic search service instance."""
        return SemanticSearchService()

    @pytest.fixture
    def mock_vector_search_service(self):
        """Mock vector search service."""
        return AsyncMock()

    @pytest.fixture
    def mock_summarization_service(self):
        """Mock summarization service."""
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
                ColumnSchema(
                    name="created_at",
                    data_type="timestamp",
                    description="Creation timestamp",
                    is_nullable=False,
                ),
            ],
            description="User accounts table",
            tier="gold",
            tags=["users", "core"],
        )

    @pytest.fixture
    def sample_table_recommendation(self, sample_table_schema):
        """Create sample table recommendation."""
        return TableRecommendation(
            table_schema=sample_table_schema,
            relevance_score=0.95,
            match_reason="High semantic similarity",
            summary="User accounts and profile information",
        )

    async def test_initialize(
        self,
        semantic_search_service,
        mock_vector_search_service,
        mock_summarization_service,
        mock_embedding_service,
    ):
        """Test service initialization."""
        with patch(
            "services.semantic_search_service.VectorSearchService"
        ) as mock_vector_class:
            mock_vector_class.return_value = mock_vector_search_service

            with patch(
                "services.semantic_search_service.SummarizationService"
            ) as mock_summ_class:
                mock_summ_class.return_value = mock_summarization_service

                with patch(
                    "services.semantic_search_service.EmbeddingService"
                ) as mock_emb_class:
                    mock_emb_class.return_value = mock_embedding_service

                    await semantic_search_service.initialize()

                    assert semantic_search_service._initialized is True
                    assert (
                        semantic_search_service.vector_search_service
                        == mock_vector_search_service
                    )
                    assert (
                        semantic_search_service.summarization_service
                        == mock_summarization_service
                    )
                    assert (
                        semantic_search_service.embedding_service
                        == mock_embedding_service
                    )

    async def test_search_tables_with_ranking(
        self,
        semantic_search_service,
        mock_vector_search_service,
        mock_summarization_service,
        mock_embedding_service,
        sample_table_recommendation,
    ):
        """Test semantic search with ranking."""
        # Setup mocks
        semantic_search_service.vector_search_service = mock_vector_search_service
        semantic_search_service.summarization_service = mock_summarization_service
        semantic_search_service.embedding_service = mock_embedding_service
        semantic_search_service._initialized = True

        # Mock search results
        mock_vector_search_service.search_tables.return_value = [
            sample_table_recommendation
        ]
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]

        # Perform search
        results = await semantic_search_service.search_tables_with_ranking(
            query="find user data",
            database_id="db-123",
            limit=10,
        )

        # Verify results
        assert len(results) == 1
        assert isinstance(results[0], TableRecommendation)
        assert results[0].table_schema.name == "users"

        # Verify calls
        mock_vector_search_service.search_tables.assert_called_once()

    async def test_search_with_caching(
        self,
        semantic_search_service,
        mock_vector_search_service,
        sample_table_recommendation,
    ):
        """Test search with caching functionality."""
        # Setup
        semantic_search_service.vector_search_service = mock_vector_search_service
        semantic_search_service._initialized = True
        mock_vector_search_service.search_tables.return_value = [
            sample_table_recommendation
        ]

        query = "find users"
        database_id = "db-123"

        # First search - should call vector search
        results1 = await semantic_search_service.search_tables_with_ranking(
            query=query,
            database_id=database_id,
            limit=5,
            use_cache=True,
        )

        # Second search - should use cache
        results2 = await semantic_search_service.search_tables_with_ranking(
            query=query,
            database_id=database_id,
            limit=5,
            use_cache=True,
        )

        # Verify vector search was called only once
        assert mock_vector_search_service.search_tables.call_count == 1
        assert len(results1) == len(results2)

    async def test_find_similar_queries(
        self,
        semantic_search_service,
        mock_vector_search_service,
    ):
        """Test finding similar queries."""
        # Setup
        semantic_search_service.vector_search_service = mock_vector_search_service
        semantic_search_service._initialized = True

        # Mock similar query results
        mock_document = VectorDocument(
            id="query_1",
            content="Find all active users",
            metadata={"original_query": "Find all active users"},
        )
        mock_result = VectorSearchResult(document=mock_document, score=0.85)
        mock_vector_search_service.search_similar_queries.return_value = [mock_result]

        # Find similar queries
        results = await semantic_search_service.find_similar_queries(
            query="find users",
            limit=5,
            min_similarity=0.7,
        )

        # Verify results
        assert len(results) == 1
        assert results[0].score == 0.85
        mock_vector_search_service.search_similar_queries.assert_called_once()

    async def test_get_query_suggestions(
        self,
        semantic_search_service,
        mock_vector_search_service,
    ):
        """Test getting query suggestions."""
        # Setup
        semantic_search_service.vector_search_service = mock_vector_search_service
        semantic_search_service._initialized = True

        # Mock similar query results
        mock_document = VectorDocument(
            id="query_1",
            content="Find all active users",
            metadata={"original_query": "Find all active users"},
        )
        mock_result = VectorSearchResult(document=mock_document, score=0.75)
        mock_vector_search_service.search_similar_queries.return_value = [mock_result]

        # Get suggestions
        suggestions = await semantic_search_service.get_query_suggestions(
            partial_query="find user",
            database_id="db-123",
            limit=5,
        )

        # Verify suggestions
        assert len(suggestions) == 1
        assert suggestions[0] == "Find all active users"

    async def test_analyze_query_intent(
        self,
        semantic_search_service,
        mock_embedding_service,
    ):
        """Test query intent analysis."""
        # Setup
        semantic_search_service.embedding_service = mock_embedding_service
        semantic_search_service._initialized = True
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]

        # Analyze intent
        intent = await semantic_search_service.analyze_query_intent(
            "Count all users created this year"
        )

        # Verify intent analysis
        assert isinstance(intent, dict)
        assert intent["query_type"] == "aggregation"
        assert "count" in intent["aggregations"]
        assert "year" in intent["time_references"]

    def test_classify_query_type(self, semantic_search_service):
        """Test query type classification."""
        test_cases = [
            ("Count all users", "aggregation"),
            ("Find active users", "retrieval"),
            ("Compare sales vs revenue", "comparison"),
            ("Show user growth over time", "temporal"),
            ("What is the weather", "general"),
        ]

        for query, expected_type in test_cases:
            result = semantic_search_service._classify_query_type(query)
            assert result == expected_type

    def test_extract_entities(self, semantic_search_service):
        """Test entity extraction."""
        query = "Find users in New York and California"
        entities = semantic_search_service._extract_entities(query)

        assert "new" in entities
        assert "york" in entities
        assert "california" in entities

    def test_extract_operations(self, semantic_search_service):
        """Test operation extraction."""
        query = "Join users with orders and filter by date"
        operations = semantic_search_service._extract_operations(query)

        assert "join" in operations
        assert "filter" in operations

    def test_extract_time_references(self, semantic_search_service):
        """Test time reference extraction."""
        query = "Show data from last week and this month"
        time_refs = semantic_search_service._extract_time_references(query)

        assert "week" in time_refs
        assert "month" in time_refs

    def test_extract_aggregations(self, semantic_search_service):
        """Test aggregation extraction."""
        query = "Count users and sum their orders"
        aggregations = semantic_search_service._extract_aggregations(query)

        assert "count" in aggregations
        assert "sum" in aggregations

    def test_calculate_tier_score(self, semantic_search_service):
        """Test tier score calculation."""
        assert semantic_search_service._calculate_tier_score("gold") == 1.0
        assert semantic_search_service._calculate_tier_score("silver") == 0.7
        assert semantic_search_service._calculate_tier_score("bronze") == 0.4
        assert semantic_search_service._calculate_tier_score("deprecated") == 0.1
        assert semantic_search_service._calculate_tier_score(None) == 0.5
        assert semantic_search_service._calculate_tier_score("unknown") == 0.5

    async def test_calculate_column_match_score(
        self,
        semantic_search_service,
        sample_table_schema,
    ):
        """Test column match score calculation."""
        # Query mentioning existing columns
        score1 = await semantic_search_service._calculate_column_match_score(
            "find user email and id",
            sample_table_schema,
        )
        assert score1 > 0.0

        # Query not mentioning any columns
        score2 = await semantic_search_service._calculate_column_match_score(
            "find something else",
            sample_table_schema,
        )
        assert score2 == 0.0

    async def test_cache_cleanup(self, semantic_search_service):
        """Test cache cleanup functionality."""
        # Add some cache entries
        old_time = datetime.utcnow() - timedelta(hours=1)
        recent_time = datetime.utcnow() - timedelta(minutes=5)

        semantic_search_service._search_cache = {
            "old_key": ([], old_time),
            "recent_key": ([], recent_time),
        }

        # Cleanup cache
        await semantic_search_service._cleanup_cache()

        # Verify old entry was removed
        assert "old_key" not in semantic_search_service._search_cache
        assert "recent_key" in semantic_search_service._search_cache

    async def test_clear_cache(self, semantic_search_service):
        """Test cache clearing."""
        # Add cache entries
        semantic_search_service._search_cache = {
            "key1": ([], datetime.utcnow()),
            "key2": ([], datetime.utcnow()),
        }

        # Clear cache
        await semantic_search_service.clear_cache()

        # Verify cache is empty
        assert len(semantic_search_service._search_cache) == 0

    async def test_get_cache_stats(self, semantic_search_service):
        """Test cache statistics."""
        # Add cache entries
        current_time = datetime.utcnow()
        old_time = current_time - timedelta(hours=1)

        semantic_search_service._search_cache = {
            "active_key": ([], current_time),
            "expired_key": ([], old_time),
        }

        # Get stats
        stats = await semantic_search_service.get_cache_stats()

        # Verify stats
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 1
        assert stats["cache_ttl_minutes"] == 30

    async def test_health_check(
        self,
        semantic_search_service,
        mock_vector_search_service,
        mock_summarization_service,
        mock_embedding_service,
    ):
        """Test health check."""
        # Setup
        semantic_search_service.vector_search_service = mock_vector_search_service
        semantic_search_service.summarization_service = mock_summarization_service
        semantic_search_service.embedding_service = mock_embedding_service
        semantic_search_service._initialized = True

        # Mock health check responses
        mock_vector_search_service.health_check.return_value = {"status": "healthy"}
        mock_summarization_service.health_check.return_value = {"status": "healthy"}
        mock_embedding_service.health_check.return_value = {"status": "healthy"}

        # Perform health check
        status = await semantic_search_service.health_check()

        # Verify status
        assert status["initialized"] is True
        assert "cache_stats" in status
        assert status["vector_search_service"]["status"] == "healthy"
        assert status["summarization_service"]["status"] == "healthy"
        assert status["embedding_service"]["status"] == "healthy"

    async def test_error_handling_not_initialized(self, semantic_search_service):
        """Test error handling when service not initialized."""
        with pytest.raises(
            RuntimeError, match="Semantic search service not initialized"
        ):
            await semantic_search_service.search_tables_with_ranking(
                "test query", "db-123"
            )

    async def test_error_handling_in_search(
        self,
        semantic_search_service,
        mock_vector_search_service,
    ):
        """Test error handling in search operations."""
        # Setup
        semantic_search_service.vector_search_service = mock_vector_search_service
        semantic_search_service._initialized = True

        # Mock search to raise exception
        mock_vector_search_service.search_tables.side_effect = Exception(
            "Search failed"
        )

        # Search should return empty list on error
        results = await semantic_search_service.search_tables_with_ranking(
            "test query", "db-123"
        )
        assert results == []

    async def test_reranking_logic(
        self,
        semantic_search_service,
        sample_table_recommendation,
    ):
        """Test re-ranking logic with multiple results."""
        # Create enhanced results with different scores
        enhanced_results = [
            {
                "recommendation": sample_table_recommendation,
                "semantic_score": 0.8,
                "tier_score": 1.0,  # Gold tier
                "column_match_score": 0.6,
                "usage_frequency_score": 0.7,
                "recency_score": 0.5,
                "similar_queries_score": 0.4,
            },
            {
                "recommendation": TableRecommendation(
                    table_schema=TableSchema(
                        name="orders",
                        database_id="db-123",
                        columns=[],
                        tier="silver",
                    ),
                    relevance_score=0.9,
                    match_reason="High similarity",
                ),
                "semantic_score": 0.9,
                "tier_score": 0.7,  # Silver tier
                "column_match_score": 0.4,
                "usage_frequency_score": 0.5,
                "recency_score": 0.6,
                "similar_queries_score": 0.3,
            },
        ]

        # Re-rank results
        ranked_results = await semantic_search_service._rerank_results(
            "test query", enhanced_results
        )

        # Verify ranking (first result should have higher composite score)
        assert len(ranked_results) == 2
        assert ranked_results[0].relevance_score >= ranked_results[1].relevance_score
        assert "Composite score:" in ranked_results[0].match_reason
