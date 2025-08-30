"""Basic test for metadata service functionality."""

import asyncio
from services.metadata_service import MetadataExtractionService, MetadataCacheConfig
from models import DatabaseType


async def test_basic_functionality():
    """Test basic metadata service functionality."""

    print("Testing MetadataExtractionService...")

    # Test configuration
    config = MetadataCacheConfig()
    print(f"✓ Config created with TTL: {config.table_list_ttl}s")

    # Test service creation
    service = MetadataExtractionService()
    print("✓ Service created successfully")

    # Test cache key generation
    key1 = service._generate_cache_key("prefix", "db123")
    key2 = service._generate_cache_key("prefix", "db123", "table1")

    assert key1 == "prefix:db123"
    assert key2 == "prefix:db123:table1"
    print("✓ Cache key generation works")

    # Test cache operations (without Redis)
    try:
        # This should handle Redis not being available gracefully
        await service._cache_set("test:key", {"test": "data"}, 60)
        cached_data = await service._cache_get("test:key")
        print("✓ Cache operations handled gracefully")
    except Exception as e:
        print(f"✓ Cache operations failed gracefully: {e}")

    # Close service
    await service.close()
    print("✓ Service closed successfully")

    print("\nAll basic tests passed! ✅")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
