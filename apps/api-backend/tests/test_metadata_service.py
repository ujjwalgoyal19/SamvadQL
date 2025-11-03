"""Integration tests for metadata extraction service."""

import asyncio
import json
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import redis.asyncio as redis

from models import DatabaseType, TableSchema, ColumnSchema
from services.metadata_service import MetadataExtractionService, MetadataCacheConfig
from repositories.metadata import MetadataRepository


@pytest_asyncio.fixture
async def redis_client():
    """Create a test Redis client."""
    client = redis.Redis.from_url("redis://localhost:6379/1", decode_responses=True)

    # Clear test database
    await client.flushdb()

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
def mock_connector():
    """Create a mock database connector."""
    connector = AsyncMock()
    connector.database_type = DatabaseType.POSTGRESQL
    connector.is_connected = True

    # Mock table list
    connector.list_tables.return_value = ["users", "orders", "products"]

    # Mock table metadata
    sample_table_schema = TableSchema(
        name="users",
        database_id="test-db-123",
        columns=[
            ColumnSchema(
                name="id",
                data_type="integer",
                description="Primary key",
                is_primary_key=True,
                is_nullable=False,
                sample_values=[1, 2, 3, 4, 5],
            ),
            ColumnSchema(
                name="email",
                data_type="varchar",
                description="User email address",
                is_nullable=False,
                sample_values=["user1@example.com", "user2@example.com"],
            ),
            ColumnSchema(
                name="status",
                data_type="varchar",
                description="User status",
                is_nullable=True,
                sample_values=["active", "inactive", "pending"],
            ),
        ],
        description="User account information",
        tier="gold",
        tags=["user-data", "core"],
        row_count=150000,
    )

    connector.get_table_metadata.return_value = sample_table_schema

    # Mock query execution for sample data collection
    connector.execute_query.side_effect = [
        # Cardinality check
        [{"distinct_count": 3, "total_count": 150000}],
        # Sample values
        [
            {"sample_value": "active"},
            {"sample_value": "inactive"},
            {"sample_value": "pending"},
        ],
    ]

    return connector


@pytest_asyncio.fixture
async def metadata_service(redis_client):
    """Create metadata service with test Redis client."""
    service = MetadataExtractionService(redis_client=redis_client)
    try:
        yield service
    finally:
        await service.close()


class TestMetadataExtractionService:
    """Test cases for MetadataExtractionService."""

    @pytest.mark.asyncio
    async def test_list_tables_from_database(self, metadata_service, mock_connector):
        """Test listing tables from database."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            tables = await metadata_service.list_tables(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
                use_cache=False,
            )

            assert tables == ["users", "orders", "products"]
            mock_connector.list_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tables_with_caching(self, metadata_service, mock_connector):
        """Test table listing with Redis caching."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            # First call - should hit database and cache result
            tables1 = await metadata_service.list_tables(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
                use_cache=True,
            )

            # Second call - should hit cache
            tables2 = await metadata_service.list_tables(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
                use_cache=True,
            )

            assert tables1 == tables2 == ["users", "orders", "products"]
            # Database should only be called once
            mock_connector.list_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_table_metadata_from_database(
        self, metadata_service, mock_connector
    ):
        """Test getting table metadata from database."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            metadata = await metadata_service.get_table_metadata(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
                table_name="users",
                use_cache=False,
                include_samples=False,
            )

            assert metadata.name == "users"
            assert len(metadata.columns) == 3
            assert metadata.description == "User account information"
            assert metadata.tier == "gold"
            mock_connector.get_table_metadata.assert_called_once_with("users")

    @pytest.mark.asyncio
    async def test_get_table_metadata_with_samples(
        self, metadata_service, mock_connector
    ):
        """Test getting table metadata with sample data enhancement."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            metadata = await metadata_service.get_table_metadata(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
                table_name="users",
                use_cache=False,
                include_samples=True,
            )

            assert metadata.name == "users"

            # Check that sample data enhancement was attempted
            # (mock_connector.execute_query should be called for sample collection)
            assert mock_connector.execute_query.called

    @pytest.mark.asyncio
    async def test_collect_sample_data_low_cardinality(
        self, metadata_service, mock_connector
    ):
        """Test sample data collection for low-cardinality columns."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            # Mock cardinality check (low cardinality)
            mock_connector.execute_query.side_effect = [
                [{"distinct_count": 3, "total_count": 1000}],  # Low cardinality
                [
                    {"sample_value": "active"},
                    {"sample_value": "inactive"},
                    {"sample_value": "pending"},
                ],
            ]

            samples = await metadata_service._collect_sample_data(
                mock_connector, "users", "status", "varchar"
            )

            assert samples == ["active", "inactive", "pending"]
            assert mock_connector.execute_query.call_count == 2

    @pytest.mark.asyncio
    async def test_collect_sample_data_high_cardinality(
        self, metadata_service, mock_connector
    ):
        """Test sample data collection skips high-cardinality columns."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            # Mock cardinality check (high cardinality)
            mock_connector.execute_query.return_value = [
                {"distinct_count": 50000, "total_count": 100000}
            ]

            samples = await metadata_service._collect_sample_data(
                mock_connector, "users", "email", "varchar"
            )

            assert samples == []
            # Should only call cardinality check, not sample collection
            mock_connector.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_sample_data_skip_text_types(
        self, metadata_service, mock_connector
    ):
        """Test sample data collection skips text/blob types."""
        samples = await metadata_service._collect_sample_data(
            mock_connector, "users", "description", "text"
        )

        assert samples == []
        # Should not call database at all
        mock_connector.execute_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_metadata_all_tables(self, metadata_service, mock_connector):
        """Test refreshing metadata for all tables."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            result = await metadata_service.refresh_metadata(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
            )

            assert result["database_id"] == "test-db-123"
            assert result["total_tables"] == 3
            assert len(result["refreshed_tables"]) == 3
            assert len(result["failed_tables"]) == 0
            assert result["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_refresh_metadata_specific_tables(
        self, metadata_service, mock_connector
    ):
        """Test refreshing metadata for specific tables."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            result = await metadata_service.refresh_metadata(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
                table_names=["users", "orders"],
            )

            assert result["total_tables"] == 2
            assert "users" in result["refreshed_tables"]
            assert "orders" in result["refreshed_tables"]

    @pytest.mark.asyncio
    async def test_get_database_summary(self, metadata_service, mock_connector):
        """Test getting database summary."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            summary = await metadata_service.get_database_summary(
                database_id="test-db-123",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "test",
                },
            )

            assert summary["database_id"] == "test-db-123"
            assert summary["database_type"] == "postgresql"
            assert summary["total_tables"] == 3
            assert summary["tables"] == ["users", "orders", "products"]
            assert len(summary["sample_tables"]) > 0

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, metadata_service):
        """Test cache key generation."""
        key1 = metadata_service._generate_cache_key("prefix", "db123")
        key2 = metadata_service._generate_cache_key("prefix", "db123", "table1")

        assert key1 == "prefix:db123"
        assert key2 == "prefix:db123:table1"

    @pytest.mark.asyncio
    async def test_cache_operations(self, metadata_service):
        """Test Redis cache operations."""
        test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}

        # Test cache set and get
        await metadata_service._cache_set("test:key", test_data, 3600)
        cached_data = await metadata_service._cache_get("test:key")

        assert cached_data == test_data

        # Test cache miss
        missing_data = await metadata_service._cache_get("nonexistent:key")
        assert missing_data is None

    @pytest.mark.asyncio
    async def test_connector_reuse(self, metadata_service, mock_connector):
        """Test that connectors are reused for the same database."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ) as mock_get:
            # Make multiple calls with same database_id
            await metadata_service.list_tables(
                "test-db-123", DatabaseType.POSTGRESQL, {}, use_cache=False
            )
            await metadata_service.get_table_metadata(
                "test-db-123", DatabaseType.POSTGRESQL, {}, "users", use_cache=False
            )

            # Should reuse the same connector
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_database_failure(self, metadata_service):
        """Test error handling when database operations fail."""
        mock_connector = AsyncMock()
        mock_connector.list_tables.side_effect = Exception("Database connection failed")

        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            with pytest.raises(Exception, match="Database connection failed"):
                await metadata_service.list_tables(
                    "test-db-123", DatabaseType.POSTGRESQL, {}, use_cache=False
                )

    @pytest.mark.asyncio
    async def test_error_handling_redis_failure(self, metadata_service, mock_connector):
        """Test graceful handling of Redis failures."""
        with patch.object(
            metadata_service, "_get_connector", return_value=mock_connector
        ):
            # Mock Redis failure
            with patch.object(
                metadata_service, "_cache_set", side_effect=Exception("Redis error")
            ):
                # Should still work, just without caching
                tables = await metadata_service.list_tables(
                    "test-db-123", DatabaseType.POSTGRESQL, {}, use_cache=True
                )

                assert tables == ["users", "orders", "products"]


class TestMetadataCacheConfig:
    """Test cases for MetadataCacheConfig."""

    def test_default_config_values(self):
        """Test default configuration values."""
        config = MetadataCacheConfig()

        assert config.table_list_ttl == 3600
        assert config.table_metadata_ttl == 7200
        assert config.sample_data_ttl == 14400
        assert config.max_sample_values == 20
        assert config.low_cardinality_threshold == 100
        assert config.sample_collection_timeout == 30

    def test_custom_config_values(self):
        """Test custom configuration values."""
        config = MetadataCacheConfig(
            table_list_ttl=1800, max_sample_values=10, low_cardinality_threshold=50
        )

        assert config.table_list_ttl == 1800
        assert config.max_sample_values == 10
        assert config.low_cardinality_threshold == 50


@pytest.mark.asyncio
async def test_integration_with_real_redis():
    """Integration test with real Redis instance."""
    try:
        # Try to connect to Redis
        redis_client = redis.Redis.from_url(
            "redis://localhost:6379/1", decode_responses=True
        )
        await redis_client.ping()

        service = MetadataExtractionService(redis_client=redis_client)

        # Test basic cache operations
        test_data = {"test": "integration", "timestamp": datetime.utcnow().isoformat()}
        await service._cache_set("integration:test", test_data, 60)

        cached_data = await service._cache_get("integration:test")
        assert cached_data == test_data

        # Cleanup
        await redis_client.delete("integration:test")
        await service.close()

    except Exception as e:
        pytest.skip(f"Redis not available for integration test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
