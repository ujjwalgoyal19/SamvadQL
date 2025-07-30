-- Migration: Create schema versioning tables
-- Description: Tables for tracking database schema versions and changes

-- Table for storing versioned table schemas
CREATE TABLE IF NOT EXISTS versioned_table_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    database_id VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    version VARCHAR(100) NOT NULL,
    parent_version VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,

    -- Schema content
    schema_content JSONB NOT NULL,
    schema_hash VARCHAR(64) NOT NULL,

    -- Metadata
    description TEXT,
    tier VARCHAR(50),
    tags TEXT[],
    row_count BIGINT,

    -- Change tracking
    change_reason TEXT,
    changed_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(database_id, table_name, version),
    CHECK (tier IS NULL OR tier IN ('gold', 'silver', 'bronze', 'deprecated'))
);

-- Table for storing schema change history
CREATE TABLE IF NOT EXISTS schema_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    database_id VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    from_version VARCHAR(100),
    to_version VARCHAR(100) NOT NULL,

    -- Change details
    change_type VARCHAR(50) NOT NULL CHECK (change_type IN ('added', 'removed', 'modified')),
    object_type VARCHAR(50) NOT NULL CHECK (object_type IN ('table', 'column')),
    object_name VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    description TEXT NOT NULL,

    -- Metadata
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

-- Table for schema version metadata and relationships
CREATE TABLE IF NOT EXISTS schema_version_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    database_id VARCHAR(255) NOT NULL,
    version VARCHAR(100) NOT NULL,

    -- Version metadata
    version_type VARCHAR(50) DEFAULT 'automatic' CHECK (version_type IN ('automatic', 'manual', 'migration')),
    is_major_change BOOLEAN DEFAULT FALSE,
    compatibility_level VARCHAR(50) DEFAULT 'compatible' CHECK (compatibility_level IN ('compatible', 'breaking', 'deprecated')),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    deprecated_at TIMESTAMP,

    -- Notes and documentation
    release_notes TEXT,
    migration_notes TEXT,

    UNIQUE(database_id, version)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_versioned_schemas_database_id ON versioned_table_schemas(database_id);
CREATE INDEX IF NOT EXISTS idx_versioned_schemas_table_name ON versioned_table_schemas(database_id, table_name);
CREATE INDEX IF NOT EXISTS idx_versioned_schemas_version ON versioned_table_schemas(database_id, table_name, version);
CREATE INDEX IF NOT EXISTS idx_versioned_schemas_active ON versioned_table_schemas(database_id, table_name, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_versioned_schemas_hash ON versioned_table_schemas(schema_hash);
CREATE INDEX IF NOT EXISTS idx_versioned_schemas_created_at ON versioned_table_schemas(created_at);

CREATE INDEX IF NOT EXISTS idx_schema_changes_database_id ON schema_changes(database_id);
CREATE INDEX IF NOT EXISTS idx_schema_changes_table_name ON schema_changes(database_id, table_name);
CREATE INDEX IF NOT EXISTS idx_schema_changes_versions ON schema_changes(from_version, to_version);
CREATE INDEX IF NOT EXISTS idx_schema_changes_detected_at ON schema_changes(detected_at);

CREATE INDEX IF NOT EXISTS idx_schema_version_metadata_database_id ON schema_version_metadata(database_id);
CREATE INDEX IF NOT EXISTS idx_schema_version_metadata_version ON schema_version_metadata(database_id, version);
CREATE INDEX IF NOT EXISTS idx_schema_version_metadata_created_at ON schema_version_metadata(created_at);

-- Function to automatically update schema hash when schema content changes
CREATE OR REPLACE FUNCTION update_schema_hash()
RETURNS TRIGGER AS $$
DECLARE
    schema_structure JSONB;
    hash_input TEXT;
BEGIN
    -- Extract normalized schema structure for hashing
    SELECT jsonb_build_object(
        'name', NEW.table_name,
        'columns', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'name', col->>'name',
                    'data_type', col->>'data_type',
                    'is_nullable', (col->>'is_nullable')::boolean,
                    'is_primary_key', (col->>'is_primary_key')::boolean,
                    'is_foreign_key', (col->>'is_foreign_key')::boolean
                ) ORDER BY col->>'name'
            )
            FROM jsonb_array_elements(NEW.schema_content->'columns') AS col
        )
    ) INTO schema_structure;

    -- Generate hash
    hash_input := schema_structure::text;
    NEW.schema_hash := encode(digest(hash_input, 'sha256'), 'hex');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update schema hash
CREATE TRIGGER trigger_update_schema_hash
    BEFORE INSERT OR UPDATE OF schema_content ON versioned_table_schemas
    FOR EACH ROW
    EXECUTE FUNCTION update_schema_hash();

-- Function to detect schema changes and create change records
CREATE OR REPLACE FUNCTION detect_schema_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_schema JSONB;
    new_schema JSONB;
    old_columns JSONB;
    new_columns JSONB;
    old_col JSONB;
    new_col JSONB;
    col_name TEXT;
    change_detected BOOLEAN := FALSE;
BEGIN
    -- Only process if this is an update and schema content changed
    IF TG_OP = 'UPDATE' AND OLD.schema_content != NEW.schema_content THEN
        old_schema := OLD.schema_content;
        new_schema := NEW.schema_content;
        old_columns := old_schema->'columns';
        new_columns := new_schema->'columns';

        -- Check for removed columns
        FOR old_col IN SELECT * FROM jsonb_array_elements(old_columns) LOOP
            col_name := old_col->>'name';
            IF NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements(new_columns) AS nc
                WHERE nc->>'name' = col_name
            ) THEN
                INSERT INTO schema_changes (
                    database_id, table_name, from_version, to_version,
                    change_type, object_type, object_name, old_value, new_value, description
                ) VALUES (
                    NEW.database_id, NEW.table_name, OLD.version, NEW.version,
                    'removed', 'column', col_name, old_col, NULL,
                    'Column ' || col_name || ' was removed'
                );
                change_detected := TRUE;
            END IF;
        END LOOP;

        -- Check for added or modified columns
        FOR new_col IN SELECT * FROM jsonb_array_elements(new_columns) LOOP
            col_name := new_col->>'name';

            -- Find corresponding old column
            SELECT col INTO old_col
            FROM jsonb_array_elements(old_columns) AS col
            WHERE col->>'name' = col_name;

            IF old_col IS NULL THEN
                -- Column was added
                INSERT INTO schema_changes (
                    database_id, table_name, from_version, to_version,
                    change_type, object_type, object_name, old_value, new_value, description
                ) VALUES (
                    NEW.database_id, NEW.table_name, OLD.version, NEW.version,
                    'added', 'column', col_name, NULL, new_col,
                    'Column ' || col_name || ' was added'
                );
                change_detected := TRUE;
            ELSIF old_col != new_col THEN
                -- Column was modified
                INSERT INTO schema_changes (
                    database_id, table_name, from_version, to_version,
                    change_type, object_type, object_name, old_value, new_value, description
                ) VALUES (
                    NEW.database_id, NEW.table_name, OLD.version, NEW.version,
                    'modified', 'column', col_name, old_col, new_col,
                    'Column ' || col_name || ' was modified'
                );
                change_detected := TRUE;
            END IF;
        END LOOP;

        -- If changes were detected, deactivate the old version
        IF change_detected THEN
            UPDATE versioned_table_schemas
            SET is_active = FALSE
            WHERE id = OLD.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to detect schema changes
CREATE TRIGGER trigger_detect_schema_changes
    AFTER INSERT OR UPDATE ON versioned_table_schemas
    FOR EACH ROW
    EXECUTE FUNCTION detect_schema_changes();

-- Comments for documentation
COMMENT ON TABLE versioned_table_schemas IS 'Stores versioned table schemas with change tracking';
COMMENT ON COLUMN versioned_table_schemas.schema_content IS 'Complete schema definition in JSON format';
COMMENT ON COLUMN versioned_table_schemas.schema_hash IS 'SHA-256 hash of normalized schema structure';
COMMENT ON COLUMN versioned_table_schemas.is_active IS 'Whether this is the currently active version';
COMMENT ON COLUMN versioned_table_schemas.parent_version IS 'Version this schema was derived from';

COMMENT ON TABLE schema_changes IS 'Records individual changes between schema versions';
COMMENT ON COLUMN schema_changes.change_type IS 'Type of change: added, removed, or modified';
COMMENT ON COLUMN schema_changes.object_type IS 'Type of object changed: table or column';

COMMENT ON TABLE schema_version_metadata IS 'Metadata about schema versions including compatibility and release information';
COMMENT ON COLUMN schema_version_metadata.compatibility_level IS 'Backward compatibility level of this version';