"""Tests for database connection and utilities."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.db.config import DatabaseConfig, parse_database_url
from core.db.pool import DatabaseConnectionManager


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_database_config_creation(self):
        """Test creating a database config."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.min_connections == 5  # default
        assert config.max_connections == 20  # default


class TestDatabaseUrlParsing:
    """Tests for database URL parsing."""

    def test_parse_complete_url(self):
        """Test parsing a complete database URL."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        config = parse_database_url(url)

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.username == "user"
        assert config.password == "pass"

    def test_parse_url_with_defaults(self):
        """Test parsing URL with missing components."""
        url = "postgresql://user@localhost/mydb"
        config = parse_database_url(url)

        assert config.host == "localhost"
        assert config.port == 5432  # default
        assert config.database == "mydb"
        assert config.username == "user"
        assert config.password == "password"  # default

    def test_parse_minimal_url(self):
        """Test parsing minimal URL."""
        url = "postgresql:///mydb"
        config = parse_database_url(url)

        assert config.host == "localhost"  # default
        assert config.port == 5432  # default
        assert config.database == "mydb"
        assert config.username == "samvadql"  # default
        assert config.password == "password"  # default


@pytest.mark.asyncio
class TestDatabaseConnectionManager:
    """Tests for DatabaseConnectionManager."""

    @pytest.fixture
    def config(self):
        """Test database configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
            min_connections=1,
            max_connections=2,
        )

    @pytest.fixture
    def manager(self, config):
        """Database connection manager instance."""
        return DatabaseConnectionManager(config)

    @patch("core.database.asyncpg.create_pool")
    async def test_initialize_pool(self, mock_create_pool, manager):
        """Test pool initialization."""
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool

        await manager.initialize()

        mock_create_pool.assert_called_once_with(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass",
            min_size=1,
            max_size=2,
            command_timeout=60,
        )
        assert manager._pool == mock_pool

    @patch("core.database.asyncpg.create_pool")
    async def test_close_pool(self, mock_create_pool, manager):
        """Test pool closure."""
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool

        await manager.initialize()
        await manager.close()

        mock_pool.close.assert_called_once()
        assert manager._pool is None

    @patch("core.database.asyncpg.create_pool")
    async def test_execute_query_with_fetch(self, mock_create_pool, manager):
        """Test executing query with fetch."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_row = {"id": 1, "name": "test"}

        mock_create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetch.return_value = [mock_row]

        await manager.initialize()
        result = await manager.execute_query("SELECT * FROM test", fetch=True)

        assert result == [{"id": 1, "name": "test"}]
        mock_connection.fetch.assert_called_once_with("SELECT * FROM test")

    @patch("core.database.asyncpg.create_pool")
    async def test_execute_query_without_fetch(self, mock_create_pool, manager):
        """Test executing query without fetch."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()

        mock_create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection

        await manager.initialize()
        result = await manager.execute_query("INSERT INTO test VALUES (1)", fetch=False)

        assert result is None
        mock_connection.execute.assert_called_once_with("INSERT INTO test VALUES (1)")

    @patch("core.database.asyncpg.create_pool")
    async def test_health_check_success(self, mock_create_pool, manager):
        """Test successful health check."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()

        mock_create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetchval.return_value = 1

        await manager.initialize()
        result = await manager.health_check()

        assert result is True
        mock_connection.fetchval.assert_called_once_with("SELECT 1")

    @patch("core.database.asyncpg.create_pool")
    async def test_health_check_failure(self, mock_create_pool, manager):
        """Test failed health check."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()

        mock_create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.fetchval.side_effect = Exception("Connection failed")

        await manager.initialize()
        result = await manager.health_check()

        assert result is False
