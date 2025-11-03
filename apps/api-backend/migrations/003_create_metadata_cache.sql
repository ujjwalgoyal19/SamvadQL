-- Migration: Create metadata cache table
-- Description: Table for caching database metadata including table lists, schemas, and sample data

CREATE TABLE IF NOT EXISTS metadata_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    database_id VARCHAR(255) NOT NULL,
    table_name VARCHAR(255),
    metadata_type VARCHAR(50) NOT NULL CHECK (metadata_type IN ('table_list', 'table_metadata', 'sample_data')),
    metadata_content JSONB NOT NULL,
    database_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_metadata_cache_database_id ON metadata_cache(database_id);
CREATE INDEX IF NOT EXISTS idx_metadata_cache_database_table ON metadata_cache(database_id, table_name);
CREATE INDEX IF NOT EXISTS idx_metadata_cache_type ON metadata_cache(metadata_type);
CREATE INDEX IF NOT EXISTS idx_metadata_cache_expires ON metadata_cache(expires_at) WHERE expires_at IS NOT NULL;

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_metadata_cache_lookup ON metadata_cache(database_id, metadata_type, table_name);

-- Trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_metadata_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_metadata_cache_updated_at
    BEFORE UPDATE ON metadata_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_metadata_cache_updated_at();

-- Comments for documentation
COMMENT ON TABLE metadata_cache IS 'Cache for database metadata including table lists, schemas, and sample data';
COMMENT ON COLUMN metadata_cache.database_id IS 'Identifier for the source database';
COMMENT ON COLUMN metadata_cache.table_name IS 'Name of the table (null for database-level metadata)';
COMMENT ON COLUMN metadata_cache.metadata_type IS 'Type of metadata: table_list, table_metadata, or sample_data';
COMMENT ON COLUMN metadata_cache.metadata_content IS 'JSON content of the cached metadata';
COMMENT ON COLUMN metadata_cache.database_type IS 'Type of source database (postgresql, mysql, etc.)';
COMMENT ON COLUMN metadata_cache.expires_at IS 'When this cache entry expires (null for no expiration)';