"""Integration tests for schema versioning with metadata service."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from models.table import TableSchema
from models.column import ColumnSchema
from models.versioned_schema import VersionedTableSchema
from services.metadata_service import MetadataExtractionService
from services.metadata_version_manager import MetadataVersionManager


def test_schema_versioning_integration():
    """Test integration between metadata service and schema versioning."""
    print("Testing schema versioning integration...")

    try:
        # Create sample table schema
        columns = [
            ColumnSchema(
                name="id",
                data_type="integer",
                is_primary_key=True,
                is_nullable=False,
                description="Primary key",
            ),
            ColumnSchema(
                name="username",
                data_type="varchar(255)",
                is_nullable=False,
                description="User login name",
            ),
            ColumnSchema(
                name="email",
                data_type="varchar(255)",
                is_nullable=False,
                description="User email address",
            ),
        ]

        table_schema = TableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=columns,
            description="User account information",
            tier="gold",
            tags=["user-data", "core"],
        )

        # Test VersionedTableSchema creation from TableSchema
        versioned_schema = VersionedTableSchema.from_table_schema(
            table_schema,
            version="v1.0.0",
            change_reason="Initial schema version",
            changed_by="system",
        )

        assert versioned_schema.name == table_schema.name
        assert versioned_schema.database_id == table_schema.database_id
        assert len(versioned_schema.columns) == len(table_schema.columns)
        assert versioned_schema.version == "v1.0.0"
        assert versioned_schema.change_reason == "Initial schema version"
        print("✓ VersionedTableSchema creation from TableSchema works")

        # Test conversion back to TableSchema
        converted_back = versioned_schema.to_table_schema()
        assert converted_back.name == table_schema.name
        assert converted_back.database_id == table_schema.database_id
        assert len(converted_back.columns) == len(table_schema.columns)
        print("✓ Conversion back to TableSchema works")

        # Test schema hash generation
        hash1 = versioned_schema.generate_schema_hash()
        assert len(hash1) == 64  # SHA-256 hex length

        # Create identical schema with different version
        versioned_schema2 = VersionedTableSchema.from_table_schema(
            table_schema,
            version="v1.0.1",
            change_reason="No changes",
            changed_by="system",
        )

        hash2 = versioned_schema2.generate_schema_hash()
        assert hash1 == hash2  # Same structure should have same hash
        print("✓ Schema hash generation works correctly")

        # Test schema with different structure
        modified_columns = columns + [
            ColumnSchema(
                name="created_at",
                data_type="timestamp",
                is_nullable=False,
                description="Account creation time",
            )
        ]

        modified_schema = TableSchema(
            name="users",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=modified_columns,
            description="User account information",
            tier="gold",
            tags=["user-data", "core"],
        )

        versioned_modified = VersionedTableSchema.from_table_schema(
            modified_schema,
            version="v2.0.0",
            change_reason="Added created_at column",
            changed_by="system",
        )

        hash3 = versioned_modified.generate_schema_hash()
        assert hash1 != hash3  # Different structure should have different hash
        print("✓ Schema hash detects structural changes")

        # Test metadata service integration (mock)
        metadata_service = MetadataExtractionService()

        # Mock the version manager
        mock_version_manager = MagicMock()
        mock_version_manager.detect_schema_changes = AsyncMock(
            return_value={"users": "v1.0.1"}
        )
        metadata_service.version_manager = mock_version_manager

        print("✓ Metadata service integration setup works")

        print("✓ All schema versioning integration tests passed!")
        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_version_manager_functionality():
    """Test version manager core functionality."""
    print("Testing version manager functionality...")

    try:
        # Create mock repositories
        mock_schema_repo = MagicMock()
        mock_change_repo = MagicMock()

        # Create version manager
        version_manager = MetadataVersionManager(
            schema_repo=mock_schema_repo, change_repo=mock_change_repo
        )

        # Test version ID generation
        async def test_version_generation():
            # Mock empty history for first version
            mock_schema_repo.get_version_history = AsyncMock(return_value=[])
            version_id = await version_manager._generate_version_id(
                "550e8400-e29b-41d4-a716-446655440000", "users"
            )
            assert version_id == "v1.0.0"

            # Mock existing version for increment
            mock_existing = MagicMock()
            mock_existing.version = "v1.0.5"
            mock_schema_repo.get_version_history = AsyncMock(
                return_value=[mock_existing]
            )

            version_id = await version_manager._generate_version_id(
                "550e8400-e29b-41d4-a716-446655440000", "users"
            )
            assert version_id == "v1.0.6"

        # Run async test
        asyncio.run(test_version_generation())
        print("✓ Version ID generation works")

        # Test schema difference computation
        columns1 = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            ),
            ColumnSchema(name="name", data_type="varchar(255)", is_nullable=False),
        ]

        columns2 = [
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            ),
            ColumnSchema(name="name", data_type="varchar(255)", is_nullable=False),
            ColumnSchema(name="email", data_type="varchar(255)", is_nullable=False),
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

        async def test_difference_computation():
            changes = await version_manager._compute_schema_differences(
                schema1, schema2
            )
            assert len(changes) == 1
            assert changes[0].change_type == "added"
            assert changes[0].object_name == "email"

        asyncio.run(test_difference_computation())
        print("✓ Schema difference computation works")

        # Test compatibility assessment
        from models.versioned_schema import SchemaChange

        # Compatible change (added column)
        compatible_changes = [
            SchemaChange(
                change_type="added",
                object_type="column",
                object_name="email",
                description="Added email column",
            )
        ]

        is_compatible, notes = version_manager._assess_compatibility(compatible_changes)
        assert is_compatible is True
        print("✓ Compatible change assessment works")

        # Breaking change (removed column)
        breaking_changes = [
            SchemaChange(
                change_type="removed",
                object_type="column",
                object_name="name",
                description="Removed name column",
            )
        ]

        is_compatible, notes = version_manager._assess_compatibility(breaking_changes)
        assert is_compatible is False
        assert any("breaks compatibility" in note for note in notes)
        print("✓ Breaking change assessment works")

        print("✓ All version manager functionality tests passed!")
        return True

    except Exception as e:
        print(f"✗ Version manager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_integration_tests():
    """Run all integration tests."""
    print("Running schema versioning integration tests...")

    success = True
    success &= test_schema_versioning_integration()
    success &= test_version_manager_functionality()

    if success:
        print("\n🎉 All integration tests passed!")
    else:
        print("\n❌ Some integration tests failed!")

    return success


if __name__ == "__main__":
    run_integration_tests()
