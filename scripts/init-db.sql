-- Initialize SamvadQL database schema

-- User feedback table
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    query_id UUID NOT NULL,
    original_query TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('accept', 'reject', 'modify')),
    comments TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query execution log
CREATE TABLE IF NOT EXISTS query_execution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    original_query TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    schema_versions JSONB NOT NULL,
    execution_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_result TEXT,
    error_message TEXT,
    performance_metrics JSONB
);

-- Database connections
CREATE TABLE IF NOT EXISTS database_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('postgresql', 'mysql', 'snowflake', 'bigquery')),
    connection_string TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table metadata cache
CREATE TABLE IF NOT EXISTS table_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    database_id UUID NOT NULL REFERENCES database_connections(id),
    table_name VARCHAR(255) NOT NULL,
    schema_data JSONB NOT NULL,
    summary TEXT,
    tier VARCHAR(50),
    tags TEXT[],
    row_count BIGINT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(database_id, table_name)
);

-- Query cache
CREATE TABLE IF NOT EXISTS query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL UNIQUE,
    original_query TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    confidence_score FLOAT NOT NULL,
    database_id UUID NOT NULL,
    selected_tables TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- User sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON user_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_query_log_user_id ON query_execution_log(user_id);
CREATE INDEX IF NOT EXISTS idx_query_log_timestamp ON query_execution_log(execution_timestamp);
CREATE INDEX IF NOT EXISTS idx_query_log_schema_versions ON query_execution_log USING GIN (schema_versions);
CREATE INDEX IF NOT EXISTS idx_table_metadata_database_id ON table_metadata(database_id);
CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_query_cache_expires ON query_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);

-- Insert sample database connection for development
INSERT INTO database_connections (name, type, connection_string)
VALUES (
    'Development PostgreSQL',
    'postgresql',
    'postgresql://' || COALESCE(current_setting('samvadql.db_user', true), 'samvadql') || ':' ||
    COALESCE(current_setting('samvadql.db_password', true), 'password') || '@' ||
    COALESCE(current_setting('samvadql.db_host', true), 'postgres') || ':' ||
    COALESCE(current_setting('samvadql.db_port', true), '5432') || '/' ||
    COALESCE(current_setting('samvadql.db_name', true), 'samvadql')
)
ON CONFLICT DO NOTHING;