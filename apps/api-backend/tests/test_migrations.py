"""Tests for migration system."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from migrations.migration_manager import Migration, MigrationManager


class TestMigration:
    """Tests for Migration class."""

    def test_migration_creation(self):
        """Test creating a migration."""
        migration = Migration(
            version="20240101_120000",
            name="Test Migration",
            up_sql="CREATE TABLE test (id INTEGER);",
            down_sql="DROP TABLE test;",
        )

        assert migration.version == "20240101_120000"
        assert migration.name == "Test Migration"
        assert migration.up_sql == "CREATE TABLE test (id INTEGER);"
        assert migration.down_sql == "DROP TABLE test;"
        assert isinstance(migration.timestamp, datetime)

    def test_migration_string_representation(self):
        """Test migration string representation."""
        migration = Migration(
            version="20240101_120000",
            name="Test Migration",
            up_sql="CREATE TABLE test (id INTEGER);",
        )

        assert str(migration) == "Migration 20240101_120000: Test Migration"


@pytest.mark.asyncio
class TestMigrationManager:
    """Tests for MigrationManager."""

    @pytest.fixture
    def manager(self):
        """Create migration manager with mocked database."""
        manager = MigrationManager()
        manager._db_manager = AsyncMock()
        return manager

    @pytest.fixture
    def sample_migration(self):
        """Sample migration for testing."""
        return Migration(
            version="20240101_120000",
            name="Test Migration",
            up_sql="CREATE TABLE test (id INTEGER);",
            down_sql="DROP TABLE test;",
        )

    async def test_initialize_migration_table(self, manager):
        """Test initializing migration table."""
        mock_connection = AsyncMock()
        manager._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )

        await manager.initialize_migration_table()

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS schema_migrations" in call_args

    async def test_get_applied_migrations(self, manager):
        """Test getting applied migrations."""
        mock_connection = AsyncMock()
        mock_rows = [
            {"version": "20240101_120000"},
            {"version": "20240102_120000"},
        ]

        manager._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetch.return_value = mock_rows

        result = await manager.get_applied_migrations()

        assert result == ["20240101_120000", "20240102_120000"]
        mock_connection.fetch.assert_called_once_with(
            "SELECT version FROM schema_migrations ORDER BY version"
        )

    async def test_get_applied_migrations_error(self, manager):
        """Test getting applied migrations with error."""
        mock_connection = AsyncMock()
        manager._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetch.side_effect = Exception("Database error")

        result = await manager.get_applied_migrations()

        assert result == []

    def test_parse_migration_file_complete(self, manager, tmp_path):
        """Test parsing a complete migration file."""
        migration_content = """-- Test migration
CREATE TABLE test (id INTEGER);

-- DOWN
DROP TABLE test;"""

        migration_file = tmp_path / "20240101_120000_test_migration.sql"
        migration_file.write_text(migration_content)

        migration = manager._parse_migration_file(migration_file)

        assert migration is not None
        assert migration.version == "20240101_120000"
        assert migration.name == "Test Migration"
        assert "CREATE TABLE test" in migration.up_sql
        assert "DROP TABLE test" in migration.down_sql

    def test_parse_migration_file_up_only(self, manager, tmp_path):
        """Test parsing migration file with only up SQL."""
        migration_content = """-- Test migration
CREATE TABLE test (id INTEGER);"""

        migration_file = tmp_path / "20240101_120000_test_migration.sql"
        migration_file.write_text(migration_content)

        migration = manager._parse_migration_file(migration_file)

        assert migration is not None
        assert migration.version == "20240101_120000"
        assert migration.name == "Test Migration"
        assert "CREATE TABLE test" in migration.up_sql
        assert migration.down_sql == ""

    def test_parse_migration_file_invalid_name(self, manager, tmp_path):
        """Test parsing migration file with invalid name."""
        migration_content = "CREATE TABLE test (id INTEGER);"

        migration_file = tmp_path / "invalid_name.sql"
        migration_file.write_text(migration_content)

        migration = manager._parse_migration_file(migration_file)

        assert migration is None

    @patch("migrations.migration_manager.Path.glob")
    def test_load_migrations_from_directory(self, mock_glob, manager):
        """Test loading migrations from directory."""
        # Mock file paths
        mock_file1 = MagicMock()
        mock_file1.stem = "20240101_120000_first_migration"
        mock_file1.read_text.return_value = "CREATE TABLE test1 (id INTEGER);"

        mock_file2 = MagicMock()
        mock_file2.stem = "20240102_120000_second_migration"
        mock_file2.read_text.return_value = "CREATE TABLE test2 (id INTEGER);"

        mock_glob.return_value = [mock_file1, mock_file2]

        migrations = manager.load_migrations_from_directory()

        assert len(migrations) == 2
        assert migrations[0].version == "20240101_120000"
        assert migrations[1].version == "20240102_120000"

    async def test_apply_migration(self, manager, sample_migration):
        """Test applying a migration."""
        mock_connection = AsyncMock()
        manager._db_manager.get_transaction.return_value.__aenter__.return_value = (
            mock_connection
        )

        await manager.apply_migration(sample_migration)

        # Check that both the migration SQL and the record insertion were called
        assert mock_connection.execute.call_count == 2

        # First call should be the migration SQL
        first_call = mock_connection.execute.call_args_list[0][0][0]
        assert first_call == sample_migration.up_sql

        # Second call should be the record insertion
        second_call = mock_connection.execute.call_args_list[1]
        assert "INSERT INTO schema_migrations" in second_call[0][0]

    async def test_rollback_migration(self, manager, sample_migration):
        """Test rolling back a migration."""
        mock_connection = AsyncMock()
        manager._db_manager.get_transaction.return_value.__aenter__.return_value = (
            mock_connection
        )

        await manager.rollback_migration(sample_migration)

        # Check that both the rollback SQL and the record deletion were called
        assert mock_connection.execute.call_count == 2

        # First call should be the rollback SQL
        first_call = mock_connection.execute.call_args_list[0][0][0]
        assert first_call == sample_migration.down_sql

        # Second call should be the record deletion
        second_call = mock_connection.execute.call_args_list[1]
        assert "DELETE FROM schema_migrations" in second_call[0][0]

    async def test_rollback_migration_no_down_sql(self, manager):
        """Test rolling back migration without down SQL."""
        migration = Migration(
            version="20240101_120000",
            name="Test Migration",
            up_sql="CREATE TABLE test (id INTEGER);",
        )

        with pytest.raises(ValueError, match="has no rollback SQL"):
            await manager.rollback_migration(migration)

    async def test_migrate_up_no_pending(self, manager):
        """Test migrate up with no pending migrations."""
        manager.initialize_migration_table = AsyncMock()
        manager.get_applied_migrations = AsyncMock(return_value=["20240101_120000"])
        manager.load_migrations_from_directory = MagicMock(
            return_value=[
                Migration("20240101_120000", "Test", "CREATE TABLE test (id INTEGER);")
            ]
        )

        await manager.migrate_up()

        manager.initialize_migration_table.assert_called_once()
        manager.get_applied_migrations.assert_called_once()

    async def test_migrate_up_with_pending(self, manager):
        """Test migrate up with pending migrations."""
        pending_migration = Migration(
            "20240102_120000", "Test 2", "CREATE TABLE test2 (id INTEGER);"
        )

        manager.initialize_migration_table = AsyncMock()
        manager.get_applied_migrations = AsyncMock(return_value=["20240101_120000"])
        manager.load_migrations_from_directory = MagicMock(
            return_value=[
                Migration(
                    "20240101_120000", "Test 1", "CREATE TABLE test1 (id INTEGER);"
                ),
                pending_migration,
            ]
        )
        manager.apply_migration = AsyncMock()

        await manager.migrate_up()

        manager.apply_migration.assert_called_once_with(pending_migration)

    async def test_get_migration_status(self, manager):
        """Test getting migration status."""
        applied_migrations = ["20240101_120000", "20240102_120000"]
        available_migrations = [
            Migration("20240101_120000", "Test 1", "CREATE TABLE test1 (id INTEGER);"),
            Migration("20240102_120000", "Test 2", "CREATE TABLE test2 (id INTEGER);"),
            Migration("20240103_120000", "Test 3", "CREATE TABLE test3 (id INTEGER);"),
        ]

        manager.initialize_migration_table = AsyncMock()
        manager.get_applied_migrations = AsyncMock(return_value=applied_migrations)
        manager.load_migrations_from_directory = MagicMock(
            return_value=available_migrations
        )

        status = await manager.get_migration_status()

        assert status["applied_count"] == 2
        assert status["pending_count"] == 1
        assert status["applied_migrations"] == applied_migrations
        assert status["pending_migrations"] == ["20240103_120000"]
        assert status["latest_applied"] == "20240102_120000"

    def test_create_migration_file(self, manager, tmp_path):
        """Test creating a migration file."""
        manager.migrations_dir = tmp_path

        with patch("migrations.migration_manager.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value.strftime.return_value = "20240101_120000"

            file_path = manager.create_migration_file(
                name="Test Migration",
                up_sql="CREATE TABLE test (id INTEGER);",
                down_sql="DROP TABLE test;",
            )

            assert file_path.name == "20240101_120000_test_migration.sql"
            assert file_path.exists()

            content = file_path.read_text()
            assert "CREATE TABLE test (id INTEGER);" in content
            assert "-- DOWN" in content
            assert "DROP TABLE test;" in content
