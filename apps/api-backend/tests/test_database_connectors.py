"""Unit tests for database connectors."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from contextlib import asynccontextmanager

from models import DatabaseType, TableSchema, ColumnSchema
from core.db.connectors import (
    BaseDatabaseConnector,
    ConnectionConfig,
    HealthCheckResult,
    PostgreSQLConnector,
    MySQLConnector,
    SnowflakeConnector,
    BigQueryConnector,
    DatabaseConnectorFactory,
)


class TestConnectionConfig:
    """Test ConnectionConfig model."""

    def test_connection_config_creation(self):
        """Test creating a connection config."""
        config = ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        assert config.database_type == DatabaseType.POSTGRESQL
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.min_connections == 5
        assert config.max_connections == 20

    def test_connection_config_from_url_postgresql(self):
        """Test creating config from PostgreSQL URL."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        config = ConnectionConfig.from_url(url, DatabaseType.POSTGRESQL)

        assert config.database_type == DatabaseType.POSTGRESQL
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.username == "user"
        assert config.password == "pass"

    def test_connection_config_from_url_mysql(self):
        """Test creating config from MySQL URL."""
        url = "mysql://user:pass@localhost:3306/mydb"
        config = ConnectionConfig.from_url(url, DatabaseType.MYSQL)

        assert config.database_type == DatabaseType.MYSQL
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.database == "mydb"
        assert config.username == "user"
        assert config.password == "pass"

    def test_connection_config_default_ports(self):
        """Test default ports for different database types."""
        assert ConnectionConfig._get_default_port(DatabaseType.POSTGRESQL) == 5432
        assert ConnectionConfig._get_default_port(DatabaseType.MYSQL) == 3306
        assert ConnectionConfig._get_default_port(DatabaseType.SNOWFLAKE) == 443
        assert ConnectionConfig._get_default_port(DatabaseType.BIGQUERY) == 443


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_health_check_result_creation(self):
        """Test creating a health check result."""
        result = HealthCheckResult(
            is_healthy=True, response_time_ms=50.5, error_message=None
        )

        assert result.is_healthy is True
        assert result.response_time_ms == 50.5
        assert result.error_message is None
        assert isinstance(result.timestamp, datetime)

    def test_health_check_result_with_error(self):
        """Test creating a health check result with error."""
        result = HealthCheckResult(
            is_healthy=False,
            response_time_ms=1000.0,
            error_message="Connection timeout",
        )

        assert result.is_healthy is False
        assert result.response_time_ms == 1000.0
        assert result.error_message == "Connection timeout"


class MockDatabaseConnector(BaseDatabaseConnector):
    """Mock connector for testing base functionality."""

    async def _create_pool(self):
        return MagicMock()

    async def _close_pool(self):
        pass

    @asynccontextmanager
    async def _get_connection(self):
        yield MagicMock()

    async def _execute_query(self, connection, sql, params=None):
        return [{"id": 1, "name": "test"}]

    async def _explain_query(self, connection, sql):
        return "Mock execution plan"

    async def _get_table_metadata(self, connection, table_name):
        return TableSchema(
            name=table_name,
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=[
                ColumnSchema(
                    name="id",
                    data_type="integer",
                    is_primary_key=True,
                    is_nullable=False,
                )
            ],
        )

    async def _list_tables(self, connection):
        return ["table1", "table2"]

    async def _health_check_query(self, connection):
        pass


class TestBaseDatabaseConnector:
    """Test BaseDatabaseConnector abstract class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

    @pytest.fixture
    def connector(self, config):
        """Create mock connector."""
        return MockDatabaseConnector(config)

    def test_connector_initialization(self, connector, config):
        """Test connector initialization."""
        assert connector.config == config
        assert connector.database_type == DatabaseType.POSTGRESQL
        assert connector.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, connector):
        """Test connection and disconnection."""
        # Test connection
        await connector.connect()
        assert connector.is_connected is True

        # Test disconnection
        await connector.disconnect()
        assert connector.is_connected is False

    @pytest.mark.asyncio
    async def test_execute_query(self, connector):
        """Test query execution."""
        result = await connector.execute_query("SELECT * FROM test")
        assert result == [{"id": 1, "name": "test"}]

    @pytest.mark.asyncio
    async def test_explain_query(self, connector):
        """Test query explanation."""
        result = await connector.explain_query("SELECT * FROM test")
        assert result == "Mock execution plan"

    @pytest.mark.asyncio
    async def test_get_table_metadata(self, connector):
        """Test getting table metadata."""
        result = await connector.get_table_metadata("test_table")
        assert isinstance(result, TableSchema)
        assert result.name == "test_table"
        assert len(result.columns) == 1

    @pytest.mark.asyncio
    async def test_list_tables(self, connector):
        """Test listing tables."""
        result = await connector.list_tables()
        assert result == ["table1", "table2"]

    @pytest.mark.asyncio
    async def test_health_check(self, connector):
        """Test health check."""
        # Test health check when not connected
        result = await connector.health_check()
        assert isinstance(result, HealthCheckResult)
        assert result.is_healthy is False
        assert result.error_message == "Not connected to database"

        # Test health check when connected
        await connector.connect()
        result = await connector.health_check()
        assert isinstance(result, HealthCheckResult)
        assert result.is_healthy is True
        assert result.response_time_ms >= 0

    @pytest.mark.asyncio
    async def test_context_manager(self, connector):
        """Test async context manager."""
        async with connector as conn:
            assert conn.is_connected is True
        assert connector.is_connected is False


class TestPostgreSQLConnector:
    """Test PostgreSQL connector."""

    @pytest.fixture
    def config(self):
        """Create PostgreSQL configuration."""
        return ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

    def test_postgresql_connector_initialization(self, config):
        """Test PostgreSQL connector initialization."""
        connector = PostgreSQLConnector(config)
        assert connector.database_type == DatabaseType.POSTGRESQL

    def test_postgresql_connector_wrong_type(self):
        """Test PostgreSQL connector with wrong database type."""
        config = ConnectionConfig(
            database_type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        with pytest.raises(ValueError, match="Config must be for PostgreSQL database"):
            PostgreSQLConnector(config)

    @pytest.mark.asyncio
    @patch("asyncpg.create_pool")
    async def test_postgresql_create_pool(self, mock_create_pool, config):
        """Test PostgreSQL pool creation."""
        mock_pool = MagicMock()

        # Make the mock awaitable
        async def create_pool_mock(*args, **kwargs):
            return mock_pool

        mock_create_pool.side_effect = create_pool_mock

        connector = PostgreSQLConnector(config)
        pool = await connector._create_pool()

        assert pool == mock_pool
        mock_create_pool.assert_called_once()

    @pytest.mark.asyncio
    async def test_postgresql_execute_query_with_params(self, config):
        """Test PostgreSQL query execution with parameters."""
        connector = PostgreSQLConnector(config)

        # Mock connection
        mock_connection = AsyncMock()
        mock_connection.fetch.return_value = [{"id": 1, "name": "test"}]

        result = await connector._execute_query(
            mock_connection, "SELECT * FROM users WHERE id = :user_id", {"user_id": 1}
        )

        assert result == [{"id": 1, "name": "test"}]
        mock_connection.fetch.assert_called_once()

    def test_postgresql_format_explain_output(self, config):
        """Test PostgreSQL EXPLAIN output formatting."""
        connector = PostgreSQLConnector(config)

        plan = {
            "Plan": {
                "Node Type": "Seq Scan",
                "Total Cost": 100.0,
                "Plan Rows": 1000,
                "Actual Total Time": 50.5,
                "Relation Name": "users",
            }
        }

        result = connector._format_explain_output(plan)

        assert "Node Type: Seq Scan" in result
        assert "Total Cost: 100.0" in result
        assert "Rows: 1000" in result
        assert "Actual Time: 50.50 ms" in result
        assert "Relation: users" in result


class TestMySQLConnector:
    """Test MySQL connector."""

    @pytest.fixture
    def config(self):
        """Create MySQL configuration."""
        return ConnectionConfig(
            database_type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

    def test_mysql_connector_initialization(self, config):
        """Test MySQL connector initialization."""
        connector = MySQLConnector(config)
        assert connector.database_type == DatabaseType.MYSQL

    def test_mysql_connector_wrong_type(self):
        """Test MySQL connector with wrong database type."""
        config = ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        with pytest.raises(ValueError, match="Config must be for MySQL database"):
            MySQLConnector(config)

    @pytest.mark.asyncio
    @patch("aiomysql.create_pool")
    async def test_mysql_create_pool(self, mock_create_pool, config):
        """Test MySQL pool creation."""
        mock_pool = MagicMock()

        # Make the mock awaitable
        async def create_pool_mock(*args, **kwargs):
            return mock_pool

        mock_create_pool.side_effect = create_pool_mock

        connector = MySQLConnector(config)
        pool = await connector._create_pool()

        assert pool == mock_pool
        mock_create_pool.assert_called_once()


class TestSnowflakeConnector:
    """Test Snowflake connector."""

    @pytest.fixture
    def config(self):
        """Create Snowflake configuration."""
        return ConnectionConfig(
            database_type=DatabaseType.SNOWFLAKE,
            host="account.snowflakecomputing.com",
            port=443,
            database="test_db",
            username="test_user",
            password="test_pass",
            options={
                "account": "test_account",
                "warehouse": "test_warehouse",
                "schema": "PUBLIC",
            },
        )

    def test_snowflake_connector_initialization(self, config):
        """Test Snowflake connector initialization."""
        connector = SnowflakeConnector(config)
        assert connector.database_type == DatabaseType.SNOWFLAKE

    def test_snowflake_connector_wrong_type(self):
        """Test Snowflake connector with wrong database type."""
        config = ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        with pytest.raises(ValueError, match="Config must be for Snowflake database"):
            SnowflakeConnector(config)


class TestBigQueryConnector:
    """Test BigQuery connector."""

    @pytest.fixture
    def config(self):
        """Create BigQuery configuration."""
        return ConnectionConfig(
            database_type=DatabaseType.BIGQUERY,
            host="bigquery.googleapis.com",
            port=443,
            database="test_project",
            username="",
            password="",
            options={"project_id": "test_project", "dataset_id": "test_dataset"},
        )

    def test_bigquery_connector_initialization(self, config):
        """Test BigQuery connector initialization."""
        connector = BigQueryConnector(config)
        assert connector.database_type == DatabaseType.BIGQUERY

    def test_bigquery_connector_wrong_type(self):
        """Test BigQuery connector with wrong database type."""
        config = ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        with pytest.raises(ValueError, match="Config must be for BigQuery database"):
            BigQueryConnector(config)


class TestDatabaseConnectorFactory:
    """Test DatabaseConnectorFactory."""

    @pytest.fixture
    def postgresql_config(self):
        """Create PostgreSQL configuration."""
        return ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

    def test_create_postgresql_connector(self, postgresql_config):
        """Test creating PostgreSQL connector."""
        connector = DatabaseConnectorFactory.create_connector(postgresql_config)
        assert isinstance(connector, PostgreSQLConnector)
        assert connector.database_type == DatabaseType.POSTGRESQL

    def test_create_connector_from_url(self):
        """Test creating connector from URL."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        connector = DatabaseConnectorFactory.create_connector_from_url(
            url, DatabaseType.POSTGRESQL
        )

        assert isinstance(connector, PostgreSQLConnector)
        assert connector.config.host == "localhost"
        assert connector.config.port == 5432
        assert connector.config.database == "mydb"

    def test_create_connector_unsupported_type(self):
        """Test creating connector with unsupported type."""
        # Test with a mock config that bypasses Pydantic validation
        mock_config = MagicMock()
        mock_config.database_type = "unsupported_type"

        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseConnectorFactory.create_connector(mock_config)

    def test_get_supported_types(self):
        """Test getting supported database types."""
        supported_types = DatabaseConnectorFactory.get_supported_types()

        assert DatabaseType.POSTGRESQL in supported_types
        assert DatabaseType.MYSQL in supported_types
        assert DatabaseType.SNOWFLAKE in supported_types
        assert DatabaseType.BIGQUERY in supported_types

    def test_register_and_unregister_connector(self):
        """Test registering and unregistering custom connector."""

        # Create a custom database type for testing
        class CustomDatabaseType:
            value = "custom"

        custom_type = CustomDatabaseType()

        # Register custom connector
        DatabaseConnectorFactory.register_connector(custom_type, MockDatabaseConnector)

        # Verify it's registered
        supported_types = DatabaseConnectorFactory.get_supported_types()
        assert custom_type in supported_types

        # Unregister custom connector
        DatabaseConnectorFactory.unregister_connector(custom_type)

        # Verify it's unregistered
        supported_types = DatabaseConnectorFactory.get_supported_types()
        assert custom_type not in supported_types

    def test_register_invalid_connector(self):
        """Test registering invalid connector class."""

        class InvalidConnector:
            pass

        with pytest.raises(
            ValueError, match="Connector class must inherit from BaseDatabaseConnector"
        ):
            DatabaseConnectorFactory.register_connector(
                DatabaseType.POSTGRESQL, InvalidConnector
            )
