#!/usr/bin/env python3
"""Migration CLI tool for SamvadQL."""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from migrations.migration_manager import MigrationManager
from core.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def migrate_up(target_version: str = None):
    """Apply pending migrations."""
    if not settings.database_url:
        logger.error("DATABASE_URL not configured")
        sys.exit(1)

    manager = MigrationManager()
    try:
        await manager.migrate_up(target_version)
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


async def migrate_down(target_version: str):
    """Rollback migrations."""
    if not settings.database_url:
        logger.error("DATABASE_URL not configured")
        sys.exit(1)

    manager = MigrationManager()
    try:
        await manager.migrate_down(target_version)
        logger.info("Rollback completed successfully")
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        sys.exit(1)


async def migration_status():
    """Show migration status."""
    if not settings.database_url:
        logger.error("DATABASE_URL not configured")
        sys.exit(1)

    manager = MigrationManager()
    try:
        status = await manager.get_migration_status()

        print(f"Applied migrations: {status['applied_count']}")
        print(f"Pending migrations: {status['pending_count']}")

        if status["latest_applied"]:
            print(f"Latest applied: {status['latest_applied']}")

        if status["pending_migrations"]:
            print("\nPending migrations:")
            for version in status["pending_migrations"]:
                print(f"  - {version}")

        if status["applied_migrations"]:
            print("\nApplied migrations:")
            for version in status["applied_migrations"]:
                print(f"  - {version}")

    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        sys.exit(1)


def create_migration(name: str, up_sql: str, down_sql: str = ""):
    """Create a new migration file."""
    manager = MigrationManager()
    try:
        file_path = manager.create_migration_file(name, up_sql, down_sql)
        print(f"Created migration file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="SamvadQL Database Migration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Migrate up command
    up_parser = subparsers.add_parser("up", help="Apply pending migrations")
    up_parser.add_argument("--target", help="Target migration version")

    # Migrate down command
    down_parser = subparsers.add_parser("down", help="Rollback migrations")
    down_parser.add_argument("target", help="Target migration version")

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("name", help="Migration name")
    create_parser.add_argument("--up-sql", required=True, help="Up migration SQL")
    create_parser.add_argument("--down-sql", default="", help="Down migration SQL")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "up":
        asyncio.run(migrate_up(args.target))
    elif args.command == "down":
        asyncio.run(migrate_down(args.target))
    elif args.command == "status":
        asyncio.run(migration_status())
    elif args.command == "create":
        create_migration(args.name, args.up_sql, args.down_sql)


if __name__ == "__main__":
    main()
