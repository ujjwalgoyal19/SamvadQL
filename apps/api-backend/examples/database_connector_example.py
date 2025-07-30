"""Example usage of database connectors."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import DatabaseType
from core.db.connectors import (
    ConnectionConfig,
    DatabaseConnectorFactory,
    PostgreSQLConnector,
    MySQLConnector,
    SnowflakeConnector,
    BigQueryConnector,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def postgresql_example():
    """Example using PostgreSQL connector."""
    logger.info("=== PostgreSQL Connector Example ===")

    # Create configuration
    config = ConnectionConfig(
        database_type=DatabaseType.POSTGRESQL,
        host="localhost",
        port=5432,
        database="samvadql",
        username="postgres",
        password="password",
        min_connections=2,
        max_connections=10,
    )

    # Create connector using factory
    connector = DatabaseConnectorFactory.create_connector(config)

    try:
        # Connect to database
        await connector.connect()
        logger.info(f"Connected to {connector.database_type.value}")

        # Perform health check
        health = await connector.health_check()
        logger.info(
            f"Health check: {health.is_healthy} ({health.response_time_ms:.2f}ms)"
        )

        # List tables
        tables = await connector.list_tables()
        logger.info(f"Found {len(tables)} tables: {tables[:5]}...")  # Show first 5

        # Get metadata for a table (if exists)
        if tables:
            table_name = tables[0]
            metadata = await connector.get_table_metadata(table_name)
            logger.info(f"Table '{table_name}' has {len(metadata.columns)} columns")

            # Execute a simple query
            result = await connector.execute_query(
                f"SELECT COUNT(*) as row_count FROM {table_name} LIMIT 1"
            )
            logger.info(f"Query result: {result}")

            # Get execution plan
            plan = await connector.explain_query(f"SELECT * FROM {table_name} LIMIT 10")
            logger.info(f"Execution plan: {plan[:100]}...")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Disconnect
        await connector.disconnect()
        logger.info("Disconnected")


async def mysql_example():
    """Example using MySQL connector."""
    logger.info("=== MySQL Connector Example ===")

    # Create configuration from URL
    connector = DatabaseConnectorFactory.create_connector_from_url(
        "mysql://root:password@localhost:3306/samvadql",
        DatabaseType.MYSQL,
        min_connections=2,
        max_connections=8,
    )

    try:
        # Use as async context manager
        async with connector:
            logger.info(f"Connected to {connector.database_type.value}")

            # Perform operations
            health = await connector.health_check()
            logger.info(f"Health check: {health.is_healthy}")

            tables = await connector.list_tables()
            logger.info(f"Found {len(tables)} tables")

    except Exception as e:
        logger.error(f"Error: {e}")


async def snowflake_example():
    """Example using Snowflake connector."""
    logger.info("=== Snowflake Connector Example ===")

    config = ConnectionConfig(
        database_type=DatabaseType.SNOWFLAKE,
        host="account.snowflakecomputing.com",
        port=443,
        database="SAMVADQL_DB",
        username="username",
        password="password",
        options={
            "account": "your_account",
            "warehouse": "COMPUTE_WH",
            "schema": "PUBLIC",
            "role": "ACCOUNTADMIN",
        },
    )

    connector = SnowflakeConnector(config)

    try:
        await connector.connect()
        logger.info("Connected to Snowflake")

        # Example operations (would work with real credentials)
        # tables = await connector.list_tables()
        # logger.info(f"Found {len(tables)} tables")

    except Exception as e:
        logger.error(
            f"Snowflake connection error (expected with dummy credentials): {e}"
        )
    finally:
        await connector.disconnect()


async def bigquery_example():
    """Example using BigQuery connector."""
    logger.info("=== BigQuery Connector Example ===")

    config = ConnectionConfig(
        database_type=DatabaseType.BIGQUERY,
        host="bigquery.googleapis.com",
        port=443,
        database="your-project-id",
        username="",
        password="",
        options={
            "project_id": "your-project-id",
            "dataset_id": "your_dataset",
            # "credentials_path": "/path/to/service-account.json",
        },
    )

    connector = BigQueryConnector(config)

    try:
        await connector.connect()
        logger.info("Connected to BigQuery")

        # Example operations (would work with real credentials)
        # tables = await connector.list_tables()
        # logger.info(f"Found {len(tables)} tables")

    except Exception as e:
        logger.error(
            f"BigQuery connection error (expected with dummy credentials): {e}"
        )
    finally:
        await connector.disconnect()


async def factory_example():
    """Example using the factory pattern."""
    logger.info("=== Factory Pattern Example ===")

    # Get supported database types
    supported_types = DatabaseConnectorFactory.get_supported_types()
    logger.info(f"Supported database types: {[t.value for t in supported_types]}")

    # Create different connectors using the factory
    configs = [
        ConnectionConfig(
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="user",
            password="pass",
        ),
        ConnectionConfig(
            database_type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            database="test_db",
            username="user",
            password="pass",
        ),
    ]

    for config in configs:
        connector = DatabaseConnectorFactory.create_connector(config)
        logger.info(f"Created {connector.database_type.value} connector")

        # Test basic properties
        logger.info(f"  - Database type: {connector.database_type}")
        logger.info(f"  - Is connected: {connector.is_connected}")
        logger.info(f"  - Host: {connector.config.host}:{connector.config.port}")


async def main():
    """Run all examples."""
    logger.info("Starting database connector examples...")

    # Run examples (comment out those that require actual database connections)
    await factory_example()

    # Uncomment these if you have the respective databases running:
    # await postgresql_example()
    # await mysql_example()
    # await snowflake_example()
    # await bigquery_example()

    logger.info("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
