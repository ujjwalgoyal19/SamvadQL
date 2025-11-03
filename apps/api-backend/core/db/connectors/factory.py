"""Database connector factory for creating appropriate connectors."""

import logging
from typing import Dict, Type

from models import DatabaseType
from .base import BaseDatabaseConnector, ConnectionConfig
from .postgresql import PostgreSQLConnector
from .mysql import MySQLConnector

logger = logging.getLogger(__name__)


class DatabaseConnectorFactory:
    """Factory class for creating database connectors."""

    _connectors: Dict[DatabaseType, Type[BaseDatabaseConnector]] = {
        DatabaseType.POSTGRESQL: PostgreSQLConnector,
        DatabaseType.MYSQL: MySQLConnector,
    }

    @classmethod
    def create_connector(
        cls, database_type: DatabaseType, connection_config: Dict
    ) -> BaseDatabaseConnector:
        """Create a database connector based on the database type and configuration."""
        if database_type not in cls._connectors:
            raise ValueError(
                f"Unsupported database type: {database_type}. "
                f"Supported types: PostgreSQL, MySQL"
            )

        connector_class = cls._connectors[database_type]

        # Create ConnectionConfig from the dictionary
        config = ConnectionConfig(database_type=database_type, **connection_config)

        logger.info(f"Creating {database_type.value} connector")
        return connector_class(config)

    @classmethod
    def create_connector_from_url(
        cls, url: str, database_type: DatabaseType, **kwargs
    ) -> BaseDatabaseConnector:
        """Create a database connector from a URL."""
        config = ConnectionConfig.from_url(url, database_type)

        # Apply any additional configuration options
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                config.options[key] = value

        return cls.create_connector(database_type, config.model_dump())

    @classmethod
    def get_supported_types(cls) -> list[DatabaseType]:
        """Get list of supported database types."""
        return list(cls._connectors.keys())

    @classmethod
    def register_connector(
        cls, database_type: DatabaseType, connector_class: Type[BaseDatabaseConnector]
    ) -> None:
        """Register a new connector type."""
        if not issubclass(connector_class, BaseDatabaseConnector):
            raise ValueError("Connector class must inherit from BaseDatabaseConnector")

        cls._connectors[database_type] = connector_class
        logger.info(f"Registered connector for {database_type.value}")

    @classmethod
    def unregister_connector(cls, database_type: DatabaseType) -> None:
        """Unregister a connector type."""
        if database_type in cls._connectors:
            del cls._connectors[database_type]
            logger.info(f"Unregistered connector for {database_type.value}")
        else:
            logger.warning(f"Connector for {database_type.value} not found")
