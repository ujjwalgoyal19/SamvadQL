from pydantic import BaseModel
from urllib.parse import urlparse


class DatabaseConfig(BaseModel):
    """Database configuration model."""

    host: str
    port: int
    database: str
    username: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60


def parse_database_url(url: str) -> DatabaseConfig:
    """Parse database URL into configuration."""
    parsed = urlparse(url)

    return DatabaseConfig(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") if parsed.path else "samvadql",
        username=parsed.username or "samvadql",
        password=parsed.password or "password",
    )
