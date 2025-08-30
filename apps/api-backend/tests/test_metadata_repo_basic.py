"""Basic test for metadata repository functionality."""

import json
from datetime import datetime, timedelta
from repositories.metadata import MetadataRepository
from models import TableSchema, ColumnSchema


def test_basic_repository_functionality():
    """Test basic metadata repository functionality."""

    print("Testing MetadataRepository...")

    # Test repository creation
    repo = MetadataRepository()
    print("✓ Repository created successfully")

    # Test table name
    assert repo.get_table_name() == "metadata_cache"
    print("✓ Table name is correct")

    # Test entity conversion
    entity = {
        "id": "test-id-123",
        "database_id": "db-123",
        "table_name": "users",
        "metadata_type": "table_metadata",
        "content": {"columns": ["id", "name"]},
        "database_type": "postgresql",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 30, 0),
        "expires_at": datetime(2024, 1, 1, 14, 0, 0),
    }

    # Test to_dict conversion
    dict_result = repo.to_dict(entity)
    assert dict_result["id"] == "test-id-123"
    assert dict_result["database_id"] == "db-123"
    assert dict_result["metadata_content"] == '{"columns": ["id", "name"]}'
    print("✓ Entity to dict conversion works")

    # Test from_dict conversion
    data = {
        "id": "test-id-123",
        "database_id": "db-123",
        "table_name": "users",
        "metadata_type": "table_metadata",
        "metadata_content": '{"columns": ["id", "name"]}',
        "database_type": "postgresql",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 30, 0),
        "expires_at": datetime(2024, 1, 1, 14, 0, 0),
    }

    entity_result = repo.from_dict(data)
    assert entity_result["id"] == "test-id-123"
    assert entity_result["content"] == {"columns": ["id", "name"]}
    print("✓ Dict to entity conversion works")

    # Test TableSchema serialization
    table_schema = TableSchema(
        name="users",
        database_id="550e8400-e29b-41d4-a716-446655440000",
        columns=[
            ColumnSchema(
                name="id", data_type="integer", is_primary_key=True, is_nullable=False
            )
        ],
        description="User table",
    )

    # Test that we can serialize and deserialize TableSchema
    serialized = table_schema.model_dump()
    deserialized = TableSchema(**serialized)
    assert deserialized.name == "users"
    assert len(deserialized.columns) == 1
    print("✓ TableSchema serialization works")

    print("\nAll basic repository tests passed! ✅")


if __name__ == "__main__":
    test_basic_repository_functionality()
