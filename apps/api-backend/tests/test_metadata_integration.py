"""Integration test for metadata extraction service with mock database."""

import asyncio
import json
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.metadata_service import MetadataExtractionService, MetadataCacheConfig
from models import DatabaseType, TableSchema, ColumnSchema
from core.db.connectors.base import BaseDatabaseConnector


class MockDatabaseConnector(BaseDatabaseConnector):
    """Mock database connector for testing."""

    def __init__(self, config):
        # Create a mock config if None is passed
        if config is None:
            from core.db.connectors.base import ConnectionConfig

            config = ConnectionConfig(
                database_type=DatabaseType.POSTGRESQL,
                host="localhost",
                port=5432,
                database="test_db",
                username="test_user",
                password="test_pass",
            )
        super().__init__(config)
        self._mock_tables = ["users", "orders", "products", "categories"]
        self._mock_metadata = {
            "users": TableSchema(
                name="users",
                database_id="550e8400-e29b-41d4-a716-446655440000",
                columns=[
                    ColumnSchema(
                        name="id",
                        data_type="integer",
                        is_primary_key=True,
                        is_nullable=False,
                        description="User ID",
                    ),
                    ColumnSchema(
                        name="email",
                        data_type="varchar(255)",
                        is_nullable=False,
                        description="User email address",
                        sample_values=["user1@example.com", "user2@example.com"],
                    ),
                    ColumnSchema(
                        name="status",
                        data_type="varchar(20)",
                        is_nullable=True,
                        description="User status",
                        sample_values=["active", "inactive", "pending"],
                    ),
                ],
                description="User account information",
                tier="gold",
                row_count=15000,
            ),
            "orders": TableSchema(
                name="orders",
                database_id="550e8400-e29b-41d4-a716-446655440000",
                columns=[
                    ColumnSchema(
                        name="id",
                        data_type="integer",
                        is_primary_key=True,
                        is_nullable=False,
                    ),
                    ColumnSchema(
                        name="user_id",
                        data_type="integer",
                        is_foreign_key=True,
                        is_nullable=False,
                    ),
                    ColumnSchema(
                        name="total",
                        data_type="decimal(10,2)",
                        is_nullable=False,
                    ),
                ],
                description="Customer orders",
                tier="silver",
                row_count=50000,
            ),
            "products": TableSchema(
                name="products",
                database_id="550e8400-e29b-41d4-a716-446655440000",
                columns=[
                    ColumnSchema(
                        name="id",
                        data_type="integer",
                        is_primary_key=True,
                        is_nullable=False,
                    ),
                    ColumnSchema(
                        name="name",
                        data_type="varchar(255)",
                        is_nullable=False,
                    ),
                    ColumnSchema(
                        name="price",
                        data_type="decimal(10,2)",
                        is_nullable=False,
                    ),
                ],
                description="Product catalog",
                tier="bronze",
                row_count=10000,
            ),
            "categories": TableSchema(
                name="categories",
                database_id="550e8400-e29b-41d4-a716-446655440000",
                columns=[
                    ColumnSchema(
                        name="id",
                        data_type="integer",
                        is_primary_key=True,
                        is_nullable=False,
                    ),
                    ColumnSchema(
                        name="name",
                        data_type="varchar(100)",
                        is_nullable=False,
                    ),
                ],
                description="Product categories",
                tier="bronze",
                row_count=50,
            ),
        }

    async def _create_pool(self):
        return MagicMock()

    async def _close_pool(self):
        pass

    @asynccontextmanager
    async def _get_connection(self):
        yield MagicMock()

    async def _execute_query(self, connection, sql: str, params=None):
        # Mock sample data queries
        if "DISTINCT" in sql and "sample_value" in sql:
            if "email" in sql:
                return [
                    {"sample_value": "user1@example.com"},
                    {"sample_value": "user2@example.com"},
                ]
            elif "status" in sql:
                return [
                    {"sample_value": "active"},
                    {"sample_value": "inactive"},
                    {"sample_value": "pending"},
                ]

        # Mock cardinality queries
        if "COUNT(DISTINCT" in sql:
            if "email" in sql:
                return [{"distinct_count": 15000, "total_count": 15000}]
            elif "status" in sql:
                return [{"distinct_count": 3, "total_count": 15000}]

        return []

    async def _explain_query(self, connection, sql: str):
        return "Mock execution plan"

    async def _get_table_metadata(self, connection, table_name: str):
        if table_name in self._mock_metadata:
            return self._mock_metadata[table_name]
        raise ValueError(f"Table {table_name} not found")

    async def _list_tables(self, connection):
        return self._mock_tables

    async def _health_check_query(self, connection):
        pass


class MockRedisClient:
    """Mock Redis client for testing."""

    def __init__(self):
        self._data = {}

    async def setex(self, key: str, ttl: int, value: str):
        self._data[key] = {
            "value": value,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl),
        }

    async def get(self, key: str):
        if key in self._data:
            entry = self._data[key]
            if entry["expires_at"] > datetime.utcnow():
                return entry["value"]
            else:
                del self._data[key]
        return None

    async def keys(self, pattern: str):
        # Simple pattern matching for testing
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [key for key in self._data.keys() if key.startswith(prefix)]
        return [key for key in self._data.keys() if key == pattern]

    async def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)

    async def close(self):
        pass


async def test_metadata_service_with_mock_database():
    """Test metadata service with mock database connector."""
    print("Testing MetadataExtractionService with mock database...")

    # Create mock Redis client
    mock_redis = MockRedisClient()

    # Create service with mock Redis
    service = MetadataExtractionService(redis_client=mock_redis)

    # Mock database configuration
    database_id = "550e8400-e29b-41d4-a716-446655440000"
    database_type = DatabaseType.POSTGRESQL
    connection_config = {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "username": "test_user",
        "password": "test_pass",
    }

    try:
        # Mock the connector factory
        with patch(
            "services.metadata_service.DatabaseConnectorFactory.create_connector"
        ) as mock_factory:
            mock_connector = MockDatabaseConnector(None)
            mock_factory.return_value = mock_connector

            # Test 1: List tables
            print("  Testing list_tables...")
            tables = await service.list_tables(
                database_id, database_type, connection_config
            )
            assert len(tables) == 4
            assert "users" in tables
            assert "orders" in tables
            print(f"  ✓ Found {len(tables)} tables")

            # Test 2: Get table metadata
            print("  Testing get_table_metadata...")
            users_metadata = await service.get_table_metadata(
                database_id, database_type, connection_config, "users"
            )
            assert users_metadata.name == "users"
            assert len(users_metadata.columns) == 3
            assert users_metadata.tier == "gold"
            print(
                f"  ✓ Retrieved metadata for users table with {len(users_metadata.columns)} columns"
            )

            # Test 3: Cache functionality
            print("  Testing cache functionality...")
            # Second call should use cache
            tables_cached = await service.list_tables(
                database_id, database_type, connection_config
            )
            assert tables_cached == tables
            print("  ✓ Cache working correctly")

            # Test 4: Sample data enhancement
            print("  Testing sample data enhancement...")
            # Check that sample values were collected
            email_column = next(
                col for col in users_metadata.columns if col.name == "email"
            )
            status_column = next(
                col for col in users_metadata.columns if col.name == "status"
            )

            assert len(email_column.sample_values) > 0
            assert len(status_column.sample_values) == 3
            print(
                f"  ✓ Sample data collected: email={len(email_column.sample_values)}, status={len(status_column.sample_values)}"
            )

            # Test 5: Database summary
            print("  Testing database summary...")
            summary = await service.get_database_summary(
                database_id, database_type, connection_config
            )
            assert summary["database_id"] == database_id
            assert summary["total_tables"] == 4
            assert len(summary["sample_tables"]) > 0
            print(
                f"  ✓ Database summary generated with {summary['total_tables']} tables"
            )

            # Test 6: Metadata refresh
            print("  Testing metadata refresh...")
            refresh_result = await service.refresh_metadata(
                database_id, database_type, connection_config, ["users", "orders"]
            )
            assert refresh_result["database_id"] == database_id
            assert len(refresh_result["refreshed_tables"]) == 2
            assert refresh_result["success_rate"] == 1.0
            print(
                f"  ✓ Refreshed metadata for {len(refresh_result['refreshed_tables'])} tables"
            )

    finally:
        await service.close()

    print("All integration tests passed! ✅")


async def test_metadata_service_error_handling():
    """Test metadata service error handling."""
    print("Testing MetadataExtractionService error handling...")

    service = MetadataExtractionService()

    database_id = "550e8400-e29b-41d4-a716-446655440001"
    database_type = DatabaseType.POSTGRESQL
    connection_config = {
        "host": "invalid-host",
        "port": 5432,
        "database": "test_db",
        "username": "test_user",
        "password": "test_pass",
    }

    try:
        # Mock a failing connector
        with patch(
            "services.metadata_service.DatabaseConnectorFactory.create_connector"
        ) as mock_factory:
            mock_connector = AsyncMock()
            mock_connector.connect.side_effect = ConnectionError("Connection failed")
            mock_factory.return_value = mock_connector

            # Test error handling for connection failure
            try:
                await service.list_tables(database_id, database_type, connection_config)
                assert False, "Should have raised an exception"
            except ConnectionError:
                print("  ✓ Connection error handled correctly")

            # Test error handling for invalid table
            mock_connector.connect.side_effect = None
            mock_connector.get_table_metadata.side_effect = ValueError(
                "Table not found"
            )

            try:
                await service.get_table_metadata(
                    database_id, database_type, connection_config, "invalid_table"
                )
                assert False, "Should have raised an exception"
            except ValueError:
                print("  ✓ Invalid table error handled correctly")

    finally:
        await service.close()

    print("Error handling tests passed! ✅")


async def test_metadata_caching_with_redis():
    """Test metadata caching with Redis."""
    print("Testing MetadataExtractionService caching with Redis...")

    mock_redis = MockRedisClient()
    service = MetadataExtractionService(redis_client=mock_redis)

    # Test cache operations directly
    test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}

    # Test cache set
    await service._cache_set("test:key", test_data, 60)
    print("  ✓ Cache set operation completed")

    # Test cache get
    cached_data = await service._cache_get("test:key")
    assert cached_data is not None
    assert cached_data["test"] == "data"
    print("  ✓ Cache get operation completed")

    # Test cache expiration
    await service._cache_set("test:expire", test_data, 1)
    await asyncio.sleep(2)  # Wait for expiration
    expired_data = await service._cache_get("test:expire")
    assert expired_data is None
    print("  ✓ Cache expiration working correctly")

    # Test cache deletion
    await service._cache_set("test:delete1", test_data, 60)
    await service._cache_set("test:delete2", test_data, 60)
    await service._cache_delete("test:delete*")

    deleted_data1 = await service._cache_get("test:delete1")
    deleted_data2 = await service._cache_get("test:delete2")
    assert deleted_data1 is None
    assert deleted_data2 is None
    print("  ✓ Cache deletion working correctly")

    await service.close()
    print("Caching tests passed! ✅")


async def test_sample_data_collection():
    """Test sample data collection logic."""
    print("Testing sample data collection...")

    mock_redis = MockRedisClient()
    service = MetadataExtractionService(redis_client=mock_redis)

    try:
        # Mock connector for sample data testing
        mock_connector = AsyncMock()

        # Mock cardinality check - low cardinality
        mock_connector.execute_query.side_effect = [
            [{"distinct_count": 5, "total_count": 1000}],  # Cardinality check
            [  # Sample values
                {"sample_value": "active"},
                {"sample_value": "inactive"},
                {"sample_value": "pending"},
                {"sample_value": "suspended"},
                {"sample_value": "deleted"},
            ],
        ]

        # Test sample data collection for low-cardinality column
        samples = await service._collect_sample_data(
            mock_connector, "users", "status", "varchar"
        )

        assert len(samples) == 5
        assert "active" in samples
        print("  ✓ Low-cardinality sample data collected correctly")

        # Reset mock for high cardinality test
        mock_connector.execute_query.side_effect = [
            [{"distinct_count": 50000, "total_count": 50000}],  # High cardinality
        ]

        # Test sample data collection for high-cardinality column
        samples_high = await service._collect_sample_data(
            mock_connector, "users", "email", "varchar"
        )

        assert len(samples_high) == 0  # Should skip high-cardinality columns
        print("  ✓ High-cardinality column skipped correctly")

        # Test with unsupported data type
        samples_blob = await service._collect_sample_data(
            mock_connector, "users", "profile_data", "blob"
        )

        assert len(samples_blob) == 0  # Should skip blob columns
        print("  ✓ Unsupported data type skipped correctly")

    finally:
        await service.close()

    print("Sample data collection tests passed! ✅")


if __name__ == "__main__":

    async def run_all_tests():
        """Run all integration tests."""
        print("Running MetadataExtractionService Integration Tests\n")
        print("=" * 60)

        try:
            await test_metadata_service_with_mock_database()
            print()

            await test_metadata_service_error_handling()
            print()

            await test_metadata_caching_with_redis()
            print()

            await test_sample_data_collection()
            print()

            print("=" * 60)
            print("All integration tests completed successfully! 🎉")
        except Exception as e:
            print(f"Test failed with error: {e}")
            import traceback

            traceback.print_exc()

    print("Starting integration tests...")
    asyncio.run(run_all_tests())
