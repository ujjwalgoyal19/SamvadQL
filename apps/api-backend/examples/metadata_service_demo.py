"""Demo script for metadata extraction service."""

import asyncio
import logging
from datetime import datetime

from models import DatabaseType
from services.metadata_service import MetadataExtractionService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def demo_metadata_extraction():
    """Demonstrate metadata extraction service functionality."""

    # Example database configuration
    database_config = {
        "host": "localhost",
        "port": 5432,
        "database": "samvadql_dev",
        "username": "postgres",
        "password": "password",
    }

    database_id = "demo-postgres-db"
    database_type = DatabaseType.POSTGRESQL

    # Create metadata service
    async with MetadataExtractionService() as metadata_service:

        logger.info("=== Metadata Extraction Service Demo ===")

        try:
            # 1. List all tables
            logger.info("1. Listing all tables...")
            tables = await metadata_service.list_tables(
                database_id=database_id,
                database_type=database_type,
                connection_config=database_config,
            )
            logger.info(f"Found {len(tables)} tables: {tables}")

            if not tables:
                logger.warning(
                    "No tables found. Make sure the database has some tables."
                )
                return

            # 2. Get metadata for the first table
            first_table = tables[0]
            logger.info(f"\n2. Getting metadata for table '{first_table}'...")

            table_metadata = await metadata_service.get_table_metadata(
                database_id=database_id,
                database_type=database_type,
                connection_config=database_config,
                table_name=first_table,
                include_samples=True,
            )

            logger.info(f"Table: {table_metadata.name}")
            logger.info(f"Description: {table_metadata.description}")
            logger.info(f"Row count: {table_metadata.row_count}")
            logger.info(f"Tier: {table_metadata.tier}")
            logger.info(f"Tags: {table_metadata.tags}")
            logger.info(f"Columns ({len(table_metadata.columns)}):")

            for column in table_metadata.columns:
                sample_info = (
                    f" (samples: {column.sample_values[:3]}...)"
                    if column.sample_values
                    else ""
                )
                logger.info(f"  - {column.name}: {column.data_type}{sample_info}")

            # 3. Test caching - second call should be faster
            logger.info(
                f"\n3. Testing cache - getting metadata for '{first_table}' again..."
            )
            start_time = datetime.now()

            cached_metadata = await metadata_service.get_table_metadata(
                database_id=database_id,
                database_type=database_type,
                connection_config=database_config,
                table_name=first_table,
                include_samples=True,
            )

            end_time = datetime.now()
            logger.info(
                f"Cached retrieval took: {(end_time - start_time).total_seconds():.3f} seconds"
            )
            logger.info(
                f"Metadata matches: {cached_metadata.name == table_metadata.name}"
            )

            # 4. Get database summary
            logger.info("\n4. Getting database summary...")
            summary = await metadata_service.get_database_summary(
                database_id=database_id,
                database_type=database_type,
                connection_config=database_config,
            )

            logger.info(f"Database ID: {summary['database_id']}")
            logger.info(f"Database Type: {summary['database_type']}")
            logger.info(f"Total Tables: {summary['total_tables']}")
            logger.info(f"Sample Tables: {len(summary['sample_tables'])}")

            # 5. Refresh metadata for specific tables
            logger.info(f"\n5. Refreshing metadata for specific tables...")
            refresh_result = await metadata_service.refresh_metadata(
                database_id=database_id,
                database_type=database_type,
                connection_config=database_config,
                table_names=[first_table],
            )

            logger.info(f"Refresh result:")
            logger.info(f"  - Total tables: {refresh_result['total_tables']}")
            logger.info(f"  - Refreshed: {refresh_result['refreshed_tables']}")
            logger.info(f"  - Failed: {refresh_result['failed_tables']}")
            logger.info(f"  - Success rate: {refresh_result['success_rate']:.2%}")

            logger.info("\n=== Demo completed successfully! ===")

        except Exception as e:
            logger.error(f"Demo failed with error: {e}")
            raise


async def demo_error_handling():
    """Demonstrate error handling in metadata service."""

    logger.info("\n=== Error Handling Demo ===")

    # Invalid database configuration
    invalid_config = {
        "host": "nonexistent-host",
        "port": 5432,
        "database": "nonexistent_db",
        "username": "invalid_user",
        "password": "invalid_password",
    }

    async with MetadataExtractionService() as metadata_service:

        try:
            # This should fail gracefully
            logger.info("Attempting to connect to invalid database...")
            tables = await metadata_service.list_tables(
                database_id="invalid-db",
                database_type=DatabaseType.POSTGRESQL,
                connection_config=invalid_config,
            )
            logger.warning("Unexpected success - this should have failed")

        except Exception as e:
            logger.info(f"Expected error caught: {type(e).__name__}: {e}")

        try:
            # Test with invalid table name
            logger.info("Attempting to get metadata for nonexistent table...")
            metadata = await metadata_service.get_table_metadata(
                database_id="demo-postgres-db",
                database_type=DatabaseType.POSTGRESQL,
                connection_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "samvadql_dev",
                    "username": "postgres",
                    "password": "password",
                },
                table_name="nonexistent_table",
            )
            logger.warning("Unexpected success - this should have failed")

        except Exception as e:
            logger.info(f"Expected error caught: {type(e).__name__}: {e}")

    logger.info("=== Error handling demo completed ===")


async def demo_performance_comparison():
    """Demonstrate performance difference between cached and uncached operations."""

    logger.info("\n=== Performance Comparison Demo ===")

    database_config = {
        "host": "localhost",
        "port": 5432,
        "database": "samvadql_dev",
        "username": "postgres",
        "password": "password",
    }

    database_id = "perf-test-db"
    database_type = DatabaseType.POSTGRESQL

    async with MetadataExtractionService() as metadata_service:

        try:
            # First call - no cache
            logger.info("First call (no cache)...")
            start_time = datetime.now()

            tables = await metadata_service.list_tables(
                database_id=database_id,
                database_type=database_type,
                connection_config=database_config,
                use_cache=False,
            )

            first_call_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"First call took: {first_call_time:.3f} seconds")

            if not tables:
                logger.warning("No tables found for performance test")
                return

            # Second call - with cache
            logger.info("Second call (with cache)...")
            start_time = datetime.now()

            cached_tables = await metadata_service.list_tables(
                database_id=database_id,
                database_type=database_type,
                connection_config=database_config,
                use_cache=True,
            )

            second_call_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Second call took: {second_call_time:.3f} seconds")

            # Performance improvement
            if first_call_time > 0:
                improvement = (
                    (first_call_time - second_call_time) / first_call_time
                ) * 100
                logger.info(f"Performance improvement: {improvement:.1f}%")

            logger.info(f"Results match: {tables == cached_tables}")

        except Exception as e:
            logger.error(f"Performance demo failed: {e}")

    logger.info("=== Performance comparison completed ===")


async def main():
    """Run all demo functions."""

    logger.info("Starting Metadata Service Demo")
    logger.info("=" * 50)

    try:
        # Run main demo
        await demo_metadata_extraction()

        # Run error handling demo
        await demo_error_handling()

        # Run performance comparison
        await demo_performance_comparison()

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return 1

    logger.info("\nAll demos completed successfully!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
