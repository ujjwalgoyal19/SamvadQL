"""Example demonstrating schema versioning functionality."""

import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.table import TableSchema
from models.column import ColumnSchema
from models.versioned_schema import VersionedTableSchema, SchemaChange
from services.metadata_version_manager import MetadataVersionManager


async def demonstrate_schema_versioning():
    """Demonstrate the schema versioning system."""
    print("=== Schema Versioning System Demo ===\n")

    # Create initial table schema
    print("1. Creating initial table schema...")
    initial_columns = [
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
    ]

    initial_schema = TableSchema(
        name="users",
        database_id="550e8400-e29b-41d4-a716-446655440000",
        columns=initial_columns,
        description="User account table",
        tier="gold",
    )

    print(f"   Table: {initial_schema.name}")
    print(f"   Columns: {[col.name for col in initial_schema.columns]}")
    print(f"   Description: {initial_schema.description}")

    # Convert to versioned schema
    print("\n2. Creating first version...")
    v1_schema = VersionedTableSchema.from_table_schema(
        initial_schema,
        version="v1.0.0",
        change_reason="Initial table creation",
        changed_by="developer",
    )

    v1_hash = v1_schema.generate_schema_hash()
    print(f"   Version: {v1_schema.version}")
    print(f"   Schema Hash: {v1_hash[:16]}...")
    print(f"   Change Reason: {v1_schema.change_reason}")

    # Create modified schema (add email column)
    print("\n3. Creating modified schema...")
    modified_columns = initial_columns + [
        ColumnSchema(
            name="email",
            data_type="varchar(255)",
            is_nullable=False,
            description="User email address",
        )
    ]

    modified_schema = TableSchema(
        name="users",
        database_id="550e8400-e29b-41d4-a716-446655440000",
        columns=modified_columns,
        description="User account table with email",
        tier="gold",
    )

    v2_schema = VersionedTableSchema.from_table_schema(
        modified_schema,
        version="v2.0.0",
        parent_version="v1.0.0",
        change_reason="Added email column",
        changed_by="developer",
    )

    v2_hash = v2_schema.generate_schema_hash()
    print(f"   Version: {v2_schema.version}")
    print(f"   Parent Version: {v2_schema.parent_version}")
    print(f"   Schema Hash: {v2_hash[:16]}...")
    print(f"   Change Reason: {v2_schema.change_reason}")
    print(f"   Hash Changed: {v1_hash != v2_hash}")

    # Demonstrate schema comparison
    print("\n4. Comparing schema versions...")

    # Mock version manager for demonstration
    mock_schema_repo = MagicMock()
    mock_change_repo = MagicMock()
    version_manager = MetadataVersionManager(
        schema_repo=mock_schema_repo, change_repo=mock_change_repo
    )

    # Compute differences
    changes = await version_manager._compute_schema_differences(v1_schema, v2_schema)

    print(f"   Changes detected: {len(changes)}")
    for change in changes:
        print(
            f"   - {change.change_type.upper()}: {change.object_type} '{change.object_name}'"
        )
        print(f"     Description: {change.description}")

    # Assess compatibility
    is_compatible, notes = version_manager._assess_compatibility(changes)
    print(f"   Backward Compatible: {is_compatible}")
    for note in notes:
        print(f"   - {note}")

    # Create breaking change example
    print("\n5. Demonstrating breaking change...")
    breaking_columns = [
        ColumnSchema(
            name="id",
            data_type="integer",
            is_primary_key=True,
            is_nullable=False,
            description="Primary key",
        ),
        ColumnSchema(
            name="email",  # Removed username, kept email
            data_type="varchar(255)",
            is_nullable=False,
            description="User email address",
        ),
    ]

    breaking_schema = TableSchema(
        name="users",
        database_id="550e8400-e29b-41d4-a716-446655440000",
        columns=breaking_columns,
        description="User account table - removed username",
        tier="gold",
    )

    v3_schema = VersionedTableSchema.from_table_schema(
        breaking_schema,
        version="v3.0.0",
        parent_version="v2.0.0",
        change_reason="Removed username column",
        changed_by="developer",
    )

    breaking_changes = await version_manager._compute_schema_differences(
        v2_schema, v3_schema
    )
    is_breaking, breaking_notes = version_manager._assess_compatibility(
        breaking_changes
    )

    print(f"   Changes: {len(breaking_changes)}")
    for change in breaking_changes:
        print(
            f"   - {change.change_type.upper()}: {change.object_type} '{change.object_name}'"
        )

    print(f"   Backward Compatible: {is_breaking}")
    for note in breaking_notes:
        print(f"   - {note}")

    # Demonstrate automatic change detection
    print("\n6. Demonstrating automatic change detection...")

    # Mock repositories for change detection
    mock_schema_repo.get_active_version = AsyncMock(return_value=v2_schema)
    mock_schema_repo.create_version = AsyncMock()

    # Mock create_schema_version to return version ID
    async def mock_create_version(schema, change_reason, changed_by=None):
        return "v2.0.1"

    version_manager.create_schema_version = AsyncMock(side_effect=mock_create_version)

    # Simulate detecting changes in current schemas
    current_schemas = [modified_schema]  # Same as v2, should not create new version

    # Mock hash to simulate no changes
    v2_schema.schema_hash = v2_hash

    changes_detected = await version_manager.detect_schema_changes(
        "550e8400-e29b-41d4-a716-446655440000", current_schemas
    )

    print(f"   Schema changes detected: {len(changes_detected)}")
    if changes_detected:
        for table_name, version in changes_detected.items():
            print(f"   - {table_name}: {version}")
    else:
        print("   - No changes detected (schemas match)")

    print("\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✓ Schema versioning with hash-based change detection")
    print("✓ Automatic version ID generation")
    print("✓ Schema comparison and difference detection")
    print("✓ Backward compatibility assessment")
    print("✓ Breaking change identification")
    print("✓ Automatic change detection workflow")


def demonstrate_model_features():
    """Demonstrate model validation and features."""
    print("\n=== Model Features Demo ===\n")

    print("1. Schema validation...")
    try:
        # Valid schema
        valid_schema = VersionedTableSchema(
            name="products",
            database_id="550e8400-e29b-41d4-a716-446655440000",
            columns=[
                ColumnSchema(
                    name="id",
                    data_type="integer",
                    is_primary_key=True,
                    is_nullable=False,
                )
            ],
            version="v1.0.0",
        )
        print("   ✓ Valid schema created successfully")

        # Invalid table name
        try:
            invalid_schema = VersionedTableSchema(
                name="123invalid",  # Invalid: starts with number
                database_id="550e8400-e29b-41d4-a716-446655440000",
                columns=[
                    ColumnSchema(
                        name="id",
                        data_type="integer",
                        is_primary_key=True,
                        is_nullable=False,
                    )
                ],
                version="v1.0.0",
            )
        except ValueError as e:
            print(f"   ✓ Invalid table name rejected: {str(e)[:50]}...")

        # Invalid database ID
        try:
            invalid_db_schema = VersionedTableSchema(
                name="products",
                database_id="not-a-uuid",  # Invalid UUID
                columns=[
                    ColumnSchema(
                        name="id",
                        data_type="integer",
                        is_primary_key=True,
                        is_nullable=False,
                    )
                ],
                version="v1.0.0",
            )
        except ValueError as e:
            print(f"   ✓ Invalid database ID rejected: {str(e)[:50]}...")

    except Exception as e:
        print(f"   ✗ Validation test failed: {e}")

    print("\n2. Schema change validation...")
    try:
        # Valid change
        valid_change = SchemaChange(
            change_type="added",
            object_type="column",
            object_name="email",
            description="Added email column",
        )
        print("   ✓ Valid schema change created")

        # Invalid change type
        try:
            invalid_change = SchemaChange(
                change_type="invalid_type",
                object_type="column",
                object_name="email",
                description="Test",
            )
        except ValueError as e:
            print(f"   ✓ Invalid change type rejected: {str(e)[:50]}...")

    except Exception as e:
        print(f"   ✗ Change validation test failed: {e}")


async def main():
    """Run the complete demonstration."""
    await demonstrate_schema_versioning()
    demonstrate_model_features()


if __name__ == "__main__":
    asyncio.run(main())
