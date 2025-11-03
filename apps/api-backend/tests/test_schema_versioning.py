"""Tests for schema versioning system."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock

from models.table import TableSchema
from models.column import ColumnSchema
from models.versioned_schema import VersionedTableSchema, SchemaChange, SchemaComparison
from services.metadata_version_manager import MetadataVersionManager
from repositories.versioned_schema import (
    VersionedSchemaRepository,
    SchemaChangeRepository,
)


class TestVersionedTableSchema:
    """Test VersionedTableSchema model."""

    def test_create_versioned_schema(self):
        """Test creating a versioned schema."""
        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            ),
            ColumnSchema(name="name", data_type="varchar(255)", is_nullable=False),
        ]

        schema = VersionedTableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
            version="v1.0.0",
            description="User table",
            change_reason="Initial version",
        )

        assert schema.name == "users"
        assert schema.version == "v1.0.0"
        assert len(schema.columns) == 2
        assert schema.is_active is True
        assert schema.parent_version is None

    def test_from_table_schema(self):
        """Test creating versioned schema from regular TableSchema."""
        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ]

        table_schema = TableSchema(
            name="products",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
            description="Product catalog",
        )

        versioned = VersionedTableSchema.from_table_schema(
            table_schema, version="v1.0.0", change_reason="Initial import"
        )

        assert versioned.name == table_schema.name
        assert versioned.database_id == table_schema.database_id
        assert versioned.version == "v1.0.0"
        assert versioned.change_reason == "Initial import"

    def test_to_table_schema(self):
        """Test converting versioned schema to regular TableSchema."""
        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ]

        versioned = VersionedTableSchema(
            name="orders",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
            version="v1.0.0",
        )

        table_schema = versioned.to_table_schema()

        assert table_schema.name == versioned.name
        assert table_schema.database_id == versioned.database_id
        assert len(table_schema.columns) == len(versioned.columns)

    def test_generate_schema_hash(self):
        """Test schema hash generation."""
        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            ),
            ColumnSchema(name="email", data_type="varchar(255)", is_nullable=False),
        ]

        schema1 = VersionedTableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
            version="v1.0.0",
        )

        schema2 = VersionedTableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
            version="v1.0.1",
        )

        hash1 = schema1.generate_schema_hash()
        hash2 = schema2.generate_schema_hash()

        # Same structure should generate same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_schema_hash_different_for_different_structure(self):
        """Test that different structures generate different hashes."""
        columns1 = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ]

        columns2 = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            ),
            ColumnSchema(name="name", data_type="varchar(255)", is_nullable=False),
        ]

        schema1 = VersionedTableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns1,
            version="v1.0.0",
        )

        schema2 = VersionedTableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns2,
            version="v2.0.0",
        )

        hash1 = schema1.generate_schema_hash()
        hash2 = schema2.generate_schema_hash()

        assert hash1 != hash2


class TestSchemaChange:
    """Test SchemaChange model."""

    def test_create_schema_change(self):
        """Test creating a schema change."""
        change = SchemaChange(
            change_type="added",
            object_type="column",
            object_name="email",
            new_value={"name": "email", "data_type": "varchar(255)"},
            description="Added email column",
        )

        assert change.change_type == "added"
        assert change.object_type == "column"
        assert change.object_name == "email"
        assert change.old_value is None
        assert change.new_value is not None

    def test_validate_change_type(self):
        """Test change type validation."""
        with pytest.raises(ValueError, match="Change type must be one of"):
            SchemaChange(
                change_type="invalid",
                object_type="column",
                object_name="test",
                description="Test",
            )

    def test_validate_object_type(self):
        """Test object type validation."""
        with pytest.raises(ValueError, match="Object type must be one of"):
            SchemaChange(
                change_type="added",
                object_type="invalid",
                object_name="test",
                description="Test",
            )


@pytest.mark.asyncio
class TestMetadataVersionManager:
    """Test MetadataVersionManager service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_schema_repo = AsyncMock(spec=VersionedSchemaRepository)
        self.mock_change_repo = AsyncMock(spec=SchemaChangeRepository)
        self.manager = MetadataVersionManager(
            schema_repo=self.mock_schema_repo, change_repo=self.mock_change_repo
        )

    async def test_create_schema_version_first_time(self):
        """Test creating first schema version."""
        # Mock no existing version
        self.mock_schema_repo.get_active_version.return_value = None
        self.mock_schema_repo.create_version.return_value = MagicMock()

        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ]

        schema = TableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
        )

        version = await self.manager.create_schema_version(
            schema, change_reason="Initial version"
        )

        assert version == "v1.0.0"
        self.mock_schema_repo.get_active_version.assert_called_once()
        self.mock_schema_repo.create_version.assert_called_once()

    async def test_create_schema_version_with_changes(self):
        """Test creating schema version when changes detected."""
        # Mock existing version with different hash
        existing_version = MagicMock()
        existing_version.version = "v1.0.0"
        existing_version.schema_hash = "old_hash"
        existing_version.generate_schema_hash.return_value = "old_hash"

        self.mock_schema_repo.get_active_version.return_value = existing_version
        self.mock_schema_repo.create_version.return_value = MagicMock()

        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            ),
            ColumnSchema(name="email", data_type="varchar(255)", is_nullable=False),
        ]

        schema = TableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
        )

        version = await self.manager.create_schema_version(
            schema, change_reason="Added email column"
        )

        assert version == "v1.0.1"
        self.mock_schema_repo.create_version.assert_called_once()

    async def test_create_schema_version_no_changes(self):
        """Test creating schema version when no changes detected."""
        # Mock existing version with same hash
        existing_version = MagicMock()
        existing_version.version = "v1.0.0"
        existing_version.schema_hash = "same_hash"
        existing_version.generate_schema_hash.return_value = "same_hash"

        self.mock_schema_repo.get_active_version.return_value = existing_version

        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ]

        schema = TableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
        )

        # Mock the hash generation to return same hash
        with pytest.MonkeyPatch().context() as m:

            def mock_generate_hash(self):
                return "same_hash"

            m.setattr(VersionedTableSchema, "generate_schema_hash", mock_generate_hash)

            version = await self.manager.create_schema_version(
                schema, change_reason="No changes"
            )

        assert version == "v1.0.0"  # Should return existing version
        self.mock_schema_repo.create_version.assert_not_called()

    async def test_detect_schema_changes(self):
        """Test automatic schema change detection."""
        # Mock existing schema
        existing_schema = MagicMock()
        existing_schema.schema_hash = "old_hash"
        self.mock_schema_repo.get_active_version.return_value = existing_schema

        # Mock create_version to return new version
        async def mock_create_version(schema, change_reason, changed_by=None):
            return "v1.0.1"

        self.manager.create_schema_version = AsyncMock(side_effect=mock_create_version)

        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ]

        schemas = [
            TableSchema(
                name="users",
                database_id="550e8400-e29b-41d4-a716-446655440000",
                columns=columns,
            )
        ]

        # Mock hash generation to return different hash
        with pytest.MonkeyPatch().context() as m:

            def mock_generate_hash(self):
                return "new_hash"

            m.setattr(VersionedTableSchema, "generate_schema_hash", mock_generate_hash)

            changes = await self.manager.detect_schema_changes(
                "550e8400-e29b-41d4-a716-446655440000", schemas
            )

        assert "users" in changes
        assert changes["users"] == "v1.0.1"

    async def test_compare_schema_versions(self):
        """Test comparing two schema versions."""
        # Mock schema versions
        schema1 = MagicMock()
        schema1.version = "v1.0.0"
        schema1.columns = [
            MagicMock(
                name="id",
                data_type="integer",
                model_dump=lambda: {"name": "id", "data_type": "integer"},
            )
        ]

        schema2 = MagicMock()
        schema2.version = "v1.0.1"
        schema2.columns = [
            MagicMock(
                name="id",
                data_type="integer",
                model_dump=lambda: {"name": "id", "data_type": "integer"},
            ),
            MagicMock(
                name="email",
                data_type="varchar",
                model_dump=lambda: {"name": "email", "data_type": "varchar"},
            ),
        ]

        self.mock_schema_repo.get_version.side_effect = [schema1, schema2]
        self.mock_change_repo.get_changes_between_versions.return_value = []

        comparison = await self.manager.compare_schema_versions(
            "550e8400-e29b-41d4-a716-446655440000", "users", "v1.0.0", "v1.0.1"
        )

        assert comparison.version1 == "v1.0.0"
        assert comparison.version2 == "v1.0.1"
        assert len(comparison.changes) > 0  # Should detect added column

    async def test_get_version_history(self):
        """Test getting version history."""
        mock_versions = [MagicMock(), MagicMock()]
        self.mock_schema_repo.get_version_history.return_value = mock_versions

        history = await self.manager.get_version_history(
            "550e8400-e29b-41d4-a716-446655440000", "users"
        )

        assert len(history) == 2
        self.mock_schema_repo.get_version_history.assert_called_once_with(
            "550e8400-e29b-41d4-a716-446655440000", "users", 50
        )

    async def test_cleanup_old_versions(self):
        """Test cleaning up old versions."""
        self.mock_schema_repo.cleanup_old_versions.return_value = 5

        deleted_count = await self.manager.cleanup_old_versions(
            "550e8400-e29b-41d4-a716-446655440000"
        )

        assert deleted_count == 5
        self.mock_schema_repo.cleanup_old_versions.assert_called_once_with(
            "550e8400-e29b-41d4-a716-446655440000", 10
        )


@pytest.mark.asyncio
class TestVersionedSchemaRepository:
    """Test VersionedSchemaRepository."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repo = VersionedSchemaRepository()
        # Mock the database operations
        self.repo.execute_raw_query = AsyncMock()
        self.repo.find_by = AsyncMock()
        self.repo.create = AsyncMock()

    async def test_create_version(self):
        """Test creating a new schema version."""
        columns = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ]

        schema = VersionedTableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
            version="v1.0.0",
        )

        # Mock deactivation and creation
        self.repo._deactivate_previous_versions = AsyncMock()
        self.repo.create.return_value = schema

        result = await self.repo.create_version(schema)

        assert result == schema
        self.repo._deactivate_previous_versions.assert_called_once()
        self.repo.create.assert_called_once()

    async def test_get_active_version(self):
        """Test getting active version."""
        mock_schema = MagicMock()
        self.repo.find_by.return_value = [mock_schema]

        result = await self.repo.get_active_version(
            "550e8400-e29b-41d4-a716-446655440000", "users"
        )

        assert result == mock_schema
        self.repo.find_by.assert_called_once_with(
            {
                "database_id": "550e8400-e29b-41d4-a716-446655440000",
                "table_name": "users",
                "is_active": True,
            },
            limit=1,
            order_by="created_at DESC",
        )

    async def test_get_version_history(self):
        """Test getting version history."""
        mock_versions = [MagicMock(), MagicMock()]
        self.repo.find_by.return_value = mock_versions

        result = await self.repo.get_version_history(
            "550e8400-e29b-41d4-a716-446655440000", "users"
        )

        assert len(result) == 2
        self.repo.find_by.assert_called_once_with(
            {
                "database_id": "550e8400-e29b-41d4-a716-446655440000",
                "table_name": "users",
            },
            limit=50,
            order_by="created_at DESC",
        )

    async def test_find_by_hash(self):
        """Test finding schemas by hash."""
        mock_schemas = [MagicMock()]
        self.repo.find_by.return_value = mock_schemas

        result = await self.repo.find_by_hash("test_hash")

        assert len(result) == 1
        self.repo.find_by.assert_called_once_with({"schema_hash": "test_hash"})


def run_basic_tests():
    """Run basic schema versioning tests."""
    print("Running schema versioning tests...")

    try:
        # Test model creation
        test_model = TestVersionedTableSchema()
        test_model.test_create_versioned_schema()
        test_model.test_from_table_schema()
        test_model.test_to_table_schema()
        test_model.test_generate_schema_hash()
        test_model.test_schema_hash_different_for_different_structure()
        print("✓ VersionedTableSchema model tests passed")

        # Test schema change model
        test_change = TestSchemaChange()
        test_change.test_create_schema_change()
        print("✓ SchemaChange model tests passed")

        print("✓ All basic schema versioning tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_basic_tests()
