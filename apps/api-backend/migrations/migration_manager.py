"""Database migration management system."""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


from core.db.pool import DatabaseConnectionManager
from core.db.manager import get_database_manager

logger = logging.getLogger(__name__)


class Migration:
    """Represents a database migration."""

    def __init__(self, version: str, name: str, up_sql: str, down_sql: str = ""):
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.timestamp = datetime.utcnow()

    def __str__(self) -> str:
        return f"Migration {self.version}: {self.name}"


class MigrationManager:
    """Manages database migrations."""

    def __init__(self, db_manager: Optional[DatabaseConnectionManager] = None):
        self._db_manager = db_manager
        self.migrations_dir = Path(__file__).parent / "sql"
        self.migrations_dir.mkdir(exist_ok=True)

    async def get_db_manager(self) -> DatabaseConnectionManager:
        """Get database manager instance."""
        if self._db_manager is None:
            self._db_manager = await get_database_manager()
        return self._db_manager

    async def initialize_migration_table(self) -> None:
        """Create the migrations tracking table if it doesn't exist."""
        db_manager = await self.get_db_manager()

        create_table_sql = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(64)
            );

            CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at
            ON schema_migrations(applied_at);
        """

        try:
            async with db_manager.get_connection() as connection:
                await connection.execute(create_table_sql)
                logger.info("Migration table initialized")
        except Exception as e:
            logger.error(f"Failed to initialize migration table: {e}")
            raise

    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        db_manager = await self.get_db_manager()

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
                return [row["version"] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []

    def load_migrations_from_directory(self) -> List[Migration]:
        """Load migration files from the migrations directory."""
        migrations = []

        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            try:
                migration = self._parse_migration_file(file_path)
                if migration:
                    migrations.append(migration)
            except Exception as e:
                logger.error(f"Failed to parse migration file {file_path}: {e}")

        return sorted(migrations, key=lambda m: m.version)

    def _parse_migration_file(self, file_path: Path) -> Optional[Migration]:
        """Parse a migration file."""
        filename = file_path.stem

        # Expected format: YYYYMMDD_HHMMSS_migration_name.sql
        parts = filename.split("_", 2)
        if len(parts) < 3:
            logger.warning(f"Invalid migration filename format: {filename}")
            return None

        version = f"{parts[0]}_{parts[1]}"
        name = parts[2].replace("_", " ").title()

        content = file_path.read_text(encoding="utf-8")

        # Split on -- DOWN marker if present
        if "-- DOWN" in content:
            up_sql, down_sql = content.split("-- DOWN", 1)
        else:
            up_sql = content
            down_sql = ""

        return Migration(version, name, up_sql.strip(), down_sql.strip())

    async def apply_migration(self, migration: Migration) -> None:
        """Apply a single migration."""
        db_manager = await self.get_db_manager()

        logger.info(f"Applying migration: {migration}")

        try:
            async with db_manager.get_transaction() as connection:
                try:
                    # Execute the migration SQL
                    await connection.execute(migration.up_sql)
                except Exception as sql_exc:
                    logger.error(
                        f"Error executing migration SQL for version {migration.version}: "
                        f"{str(sql_exc)}\n"
                        f"SQL snippet: {migration.up_sql[:200]}..."
                    )
                    # Optionally, fetch and log database state information here
                    raise

                try:
                    # Record the migration as applied
                    await connection.execute(
                        """
                        INSERT INTO schema_migrations (version, name, applied_at)
                        VALUES ($1, $2, $3)
                        """,
                        migration.version,
                        migration.name,
                        migration.timestamp,
                    )
                except Exception as record_exc:
                    logger.error(
                        f"Error recording migration {migration.version} as applied: {str(record_exc)}"
                    )
                    raise

                logger.info(f"Successfully applied migration: {migration}")
        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise

    async def rollback_migration(self, migration: Migration) -> None:
        """Rollback a single migration."""
        if not migration.down_sql:
            raise ValueError(f"Migration {migration.version} has no rollback SQL")

        db_manager = await self.get_db_manager()

        logger.info(f"Rolling back migration: {migration}")

        try:
            async with db_manager.get_transaction() as connection:
                # Execute the rollback SQL
                await connection.execute(migration.down_sql)

                # Remove the migration record
                await connection.execute(
                    "DELETE FROM schema_migrations WHERE version = $1",
                    migration.version,
                )

                logger.info(f"Successfully rolled back migration: {migration}")
        except Exception as e:
            logger.error(f"Failed to rollback migration {migration}: {e}")
            raise

    async def migrate_up(self, target_version: Optional[str] = None) -> None:
        """Apply all pending migrations up to target version."""
        await self.initialize_migration_table()

        applied_migrations = await self.get_applied_migrations()
        available_migrations = self.load_migrations_from_directory()

        pending_migrations = [
            m for m in available_migrations if m.version not in applied_migrations
        ]

        if target_version:
            pending_migrations = [
                m for m in pending_migrations if m.version <= target_version
            ]

        if not pending_migrations:
            logger.info("No pending migrations to apply")
            return

        logger.info(f"Applying {len(pending_migrations)} migrations")

        for migration in pending_migrations:
            await self.apply_migration(migration)

        logger.info("All migrations applied successfully")

    async def migrate_down(self, target_version: str) -> None:
        """Rollback migrations down to target version."""
        await self.initialize_migration_table()

        applied_migrations = await self.get_applied_migrations()
        available_migrations = self.load_migrations_from_directory()

        # Find migrations to rollback (in reverse order)
        migrations_to_rollback = []
        for migration in reversed(available_migrations):
            if (
                migration.version in applied_migrations
                and migration.version > target_version
            ):
                migrations_to_rollback.append(migration)

        if not migrations_to_rollback:
            logger.info("No migrations to rollback")
            return

        logger.info(f"Rolling back {len(migrations_to_rollback)} migrations")

        for migration in migrations_to_rollback:
            await self.rollback_migration(migration)

        logger.info("All rollbacks completed successfully")

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        await self.initialize_migration_table()

        applied_migrations = await self.get_applied_migrations()
        available_migrations = self.load_migrations_from_directory()

        pending_migrations = [
            m.version
            for m in available_migrations
            if m.version not in applied_migrations
        ]

        return {
            "applied_count": len(applied_migrations),
            "pending_count": len(pending_migrations),
            "applied_migrations": applied_migrations,
            "pending_migrations": pending_migrations,
            "latest_applied": applied_migrations[-1] if applied_migrations else None,
        }

    def create_migration_file(self, name: str, up_sql: str, down_sql: str = "") -> Path:
        """Create a new migration file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name.lower().replace(' ', '_')}.sql"
        file_path = self.migrations_dir / filename

        content = up_sql
        if down_sql:
            content += f"\n\n-- DOWN\n{down_sql}"

        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Created migration file: {file_path}")

        return file_path
