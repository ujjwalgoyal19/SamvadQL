"""Database connection utilities for SQLAlchemy sessions."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from core.config import settings

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine = None
_session_maker = None


def get_engine():
    """Get or create the SQLAlchemy async engine."""
    global _engine

    if _engine is None:
        if not settings.database_url:
            raise ValueError("DATABASE_URL not configured")

        # Convert postgres:// to postgresql+asyncpg:// if needed
        db_url = settings.database_url
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        _engine = create_async_engine(
            db_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,
            poolclass=NullPool,  # Disable connection pooling to avoid issues
        )

        logger.info("SQLAlchemy async engine created")

    return _engine


def get_session_maker():
    """Get or create the SQLAlchemy session maker."""
    global _session_maker

    if _session_maker is None:
        engine = get_engine()
        _session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("SQLAlchemy session maker created")

    return _session_maker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    session_maker = get_session_maker()

    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def close_db_connections():
    """Close database connections."""
    global _engine, _session_maker

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_maker = None
        logger.info("Database connections closed")
