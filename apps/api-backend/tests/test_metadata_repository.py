"""Tests for metadata repository."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from models import TableSchema, ColumnSchema
from repositories.metadata import MetadataRepository


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    manager = AsyncMock()
    connection = AsyncMock()
    manager.get_connection.return_value.__aenter__.return_value = connection
    manager.get_connection.return_value.__aexit__.return_value = None
    return manager, connection


@pytest.fixture
async def metadata_repo(mock_db_manager):
    """Create metadata repository with mock database."""
    manager, connection = mock_db_manager
    repo = MetadataRepository(db_manager=manager)
    return repo, connection


class TestMetadataRepository:
    """Test cases for MetadataRepository."""

    def test_table_name(self):
        """Test table name is correct."""
        repo = MetadataRepository()
        assert repo.get_table_name() == "metadata_cache"

    def test_to_dict_conversion(self):
        """Test entity to dictionary conversion."""
        repo = MetadataRepository()

        entity = {
            "id": "test-id-123",
            "database_id": "db-123",
            "table_name": "users",
            "metadata_type": "table_metadata",
            "content": {"columns": ["id", "name"]},
            "database_type": "postgresql",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 1, 12, 30, 0),
            "expires_at": datetime(2024, 1, 1, 14, 0, 0),
        }

        result = repo.to_dict(entity)

        assert result["id"] == "test-id-123"
        assert result["database_id"] == "db-123"
        assert result["table_name"] == "users"
        assert result["metadata_type"] == "table_metadata"
        assert result["metadata_content"] == '{"columns": ["id", "name"]}'
        assert result["database_type"] == "postgresql"

    def test_from_dict_conversion(self):
        """Test dictionary to entity conversion."""
        repo = MetadataRepository()

        data = {
            "id": "test-id-123",
            "database_id": "db-123",
            "table_name": "users",
            "metadata_type": "table_metadata",
            "metadata_content": '{"columns": ["id", "name"]}',
            "database_type": "postgresql",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 1, 12, 30, 0),
            "expires_at": datetime(2024, 1, 1, 14, 0, 0),
        }

        result = repo.from_dict(data)

        assert result["id"] == "test-id-123"
        assert result["database_id"] == "db-123"
        assert result["table_name"] == "users"
        assert result["metadata_type"] == "table_metadata"
        assert result["content"] == {"columns": ["id", "name"]}
        assert result["database_type"] == "postgresql"

    @pytest.mark.asyncio
    async def test_get_table_list_cached(self, metadata_repo):
        """Test getting cached table list."""
        repo, connection = metadata_repo

        # Mock database response
        mock_row = {
            "id": "test-id",
            "database_id": "db-123",
            "table_name": None,
            "metadata_type": "table_list",
            "metadata_content": '{"tables": ["users", "orders"], "extracted_at": "2024-01-01T12:00:00"}',
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),  # Not expired
        }

        connection.fetch.return_value = [mock_row]

        result = await repo.get_table_list("db-123")

        assert result == ["users", "orders"]
        connection.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_table_list_expired(self, metadata_repo):
        """Test getting expired table list returns None."""
        repo, connection = metadata_repo

        # Mock expired database response
        mock_row = {
            "id": "test-id",
            "database_id": "db-123",
            "table_name": None,
            "metadata_type": "table_list",
            "metadata_content": '{"tables": ["users", "orders"]}',
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() - timedelta(hours=1),  # Expired
        }

        connection.fetch.return_value = [mock_row]

        result = await repo.get_table_list("db-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_table_list_not_found(self, metadata_repo):
        """Test getting table list when not cached."""
        repo, connection = metadata_repo

        connection.fetch.return_value = []

        result = await repo.get_table_list("db-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_store_table_list(self, metadata_repo):
        """Test storing table list in cache."""
        repo, connection = metadata_repo

        # Mock successful creation
        mock_created_row = {
            "id": "new-id",
            "database_id": "db-123",
            "table_name": None,
            "metadata_type": "table_list",
            "metadata_content": '{"tables": ["users", "orders"], "extracted_at": "2024-01-01T12:00:00"}',
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=3600),
        }

        connection.fetchrow.return_value = mock_created_row
        connection.fetch.return_value = []  # No existing entries to delete

        await repo.store_table_list("db-123", ["users", "orders"], "postgresql", 3600)

        # Should call create (via fetchrow for INSERT ... RETURNING)
        connection.fetchrow.assert_called()

    @pytest.mark.asyncio
    async def test_get_table_metadata_cached(self, metadata_repo):
        """Test getting cached table metadata."""
        repo, connection = metadata_repo

        # Create sample table schema
        table_schema = TableSchema(
            name="users",
            database_id="db-123",
            columns=[
                ColumnSchema(
                    name="id",
                    data_type="integer",
                    is_primary_key=True,
                    is_nullable=False,
                )
            ],
            description="User table",
        )

        mock_row = {
            "id": "test-id",
            "database_id": "db-123",
            "table_name": "users",
            "metadata_type": "table_metadata",
            "metadata_content": f'{{"metadata": {table_schema.model_dump_json()}, "extracted_at": "2024-01-01T12:00:00"}}',
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),  # Not expired
        }

        connection.fetch.return_value = [mock_row]

        result = await repo.get_table_metadata("db-123", "users")

        assert result is not None
        assert result.name == "users"
        assert result.database_id == "db-123"
        assert len(result.columns) == 1
        assert result.columns[0].name == "id"

    @pytest.mark.asyncio
    async def test_store_table_metadata(self, metadata_repo):
        """Test storing table metadata in cache."""
        repo, connection = metadata_repo

        # Create sample table schema
        table_schema = TableSchema(
            name="users",
            database_id="db-123",
            columns=[
                ColumnSchema(
                    name="id",
                    data_type="integer",
                    is_primary_key=True,
                    is_nullable=False,
                )
            ],
            description="User table",
        )

        # Mock successful creation
        mock_created_row = {
            "id": "new-id",
            "database_id": "db-123",
            "table_name": "users",
            "metadata_type": "table_metadata",
            "metadata_content": f'{{"metadata": {table_schema.model_dump_json()}}}',
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=7200),
        }

        connection.fetchrow.return_value = mock_created_row
        connection.fetch.return_value = []  # No existing entries to delete

        await repo.store_table_metadata("db-123", table_schema, "postgresql", 7200)

        # Should call create (via fetchrow for INSERT ... RETURNING)
        connection.fetchrow.assert_called()

    @pytest.mark.asyncio
    async def test_get_sample_data_cached(self, metadata_repo):
        """Test getting cached sample data."""
        repo, connection = metadata_repo

        mock_row = {
            "id": "test-id",
            "database_id": "db-123",
            "table_name": "users",
            "metadata_type": "sample_data",
            "metadata_content": '{"columns": {"status": ["active", "inactive", "pending"]}, "extracted_at": "2024-01-01T12:00:00"}',
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),  # Not expired
        }

        connection.fetch.return_value = [mock_row]

        result = await repo.get_sample_data("db-123", "users", "status")

        assert result == ["active", "inactive", "pending"]

    @pytest.mark.asyncio
    async def test_store_sample_data(self, metadata_repo):
        """Test storing sample data in cache."""
        repo, connection = metadata_repo

        column_samples = {
            "status": ["active", "inactive", "pending"],
            "type": ["admin", "user"],
        }

        # Mock successful creation
        mock_created_row = {
            "id": "new-id",
            "database_id": "db-123",
            "table_name": "users",
            "metadata_type": "sample_data",
            "metadata_content": f'{{"columns": {column_samples}}}',
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=14400),
        }

        connection.fetchrow.return_value = mock_created_row
        connection.fetch.return_value = []  # No existing entries to delete

        await repo.store_sample_data(
            "db-123", "users", column_samples, "postgresql", 14400
        )

        # Should call create (via fetchrow for INSERT ... RETURNING)
        connection.fetchrow.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_expired_metadata(self, metadata_repo):
        """Test cleanup of expired metadata entries."""
        repo, connection = metadata_repo

        # Mock expired entries
        expired_entries = [
            {"id": "expired-1"},
            {"id": "expired-2"},
            {"id": "expired-3"},
        ]

        connection.fetch.return_value = expired_entries
        connection.execute.return_value = "DELETE 1"  # Mock successful deletion

        deleted_count = await repo.cleanup_expired_metadata()

        assert deleted_count == 3
        # Should call delete for each expired entry
        assert connection.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_get_database_stats(self, metadata_repo):
        """Test getting database statistics."""
        repo, connection = metadata_repo

        # Mock statistics query results
        stats_rows = [
            {
                "metadata_type": "table_list",
                "count": 1,
                "last_updated": datetime(2024, 1, 1, 12, 0, 0),
                "active_count": 1,
            },
            {
                "metadata_type": "table_metadata",
                "count": 5,
                "last_updated": datetime(2024, 1, 1, 12, 30, 0),
                "active_count": 4,
            },
            {
                "metadata_type": "sample_data",
                "count": 3,
                "last_updated": datetime(2024, 1, 1, 11, 45, 0),
                "active_count": 2,
            },
        ]

        connection.fetch.return_value = stats_rows

        stats = await repo.get_database_stats("db-123")

        assert stats["database_id"] == "db-123"
        assert stats["total_entries"] == 9  # 1 + 5 + 3
        assert stats["active_entries"] == 7  # 1 + 4 + 2
        assert stats["last_updated"] == "2024-01-01T12:30:00"

        assert "table_list" in stats["by_type"]
        assert stats["by_type"]["table_list"]["total"] == 1
        assert stats["by_type"]["table_list"]["active"] == 1

        assert "table_metadata" in stats["by_type"]
        assert stats["by_type"]["table_metadata"]["total"] == 5
        assert stats["by_type"]["table_metadata"]["active"] == 4

    @pytest.mark.asyncio
    async def test_error_handling_database_error(self, metadata_repo):
        """Test error handling for database errors."""
        repo, connection = metadata_repo

        # Mock database error
        connection.fetch.side_effect = Exception("Database connection failed")

        result = await repo.get_table_list("db-123")

        # Should return None on error, not raise exception
        assert result is None

    @pytest.mark.asyncio
    async def test_error_handling_json_parsing_error(self, metadata_repo):
        """Test error handling for JSON parsing errors."""
        repo, connection = metadata_repo

        # Mock row with invalid JSON
        mock_row = {
            "id": "test-id",
            "database_id": "db-123",
            "table_name": None,
            "metadata_type": "table_list",
            "metadata_content": "invalid json content",  # Invalid JSON
            "database_type": "postgresql",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }

        connection.fetch.return_value = [mock_row]

        result = await repo.get_table_list("db-123")

        # Should return None on JSON parsing error
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
