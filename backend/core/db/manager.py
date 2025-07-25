"""Database connection utilities and connection pooling."""

from typing import Optional

from .config import parse_database_url
from .pool import DatabaseConnectionManager
from core.config import settings

# Global database manager instance
_db_manager: Optional[DatabaseConnectionManager] = None


async def get_database_manager() -> DatabaseConnectionManager:
    """Get the global database manager instance."""
    global _db_manager

    if _db_manager is None:
        if not settings.database_url:
            raise ValueError("DATABASE_URL not configured")

        config = parse_database_url(settings.database_url)
        _db_manager = DatabaseConnectionManager(config)
        await _db_manager.initialize()

    return _db_manager


async def close_database_manager() -> None:
    """Close the global database manager."""
    global _db_manager

    if _db_manager:
        await _db_manager.close()
        _db_manager = None
