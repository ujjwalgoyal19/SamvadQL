-- Migration: Create ABAC (Attribute-Based Access Control) Tables
-- Description: Adds resource-level permissions, role resource permissions, and permission hierarchy
-- Created: 2025-02-07
-- Dependencies: 20250206_140000_create_auth_tables.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Resource Permissions Table (user-level resource permissions)
CREATE TABLE IF NOT EXISTS resource_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL CHECK (resource_type IN ('database', 'table', 'column', 'query', 'api')),
    resource_id VARCHAR(255) NOT NULL,
    permission VARCHAR(50) NOT NULL CHECK (permission IN ('read', 'write', 'delete', 'execute', 'admin')),
    granted_by UUID NOT NULL REFERENCES users(id),
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    conditions JSONB NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_resource_permission UNIQUE (user_id, resource_type, resource_id, permission)
);

-- 2. Role Resource Permissions Table (role-level resource permissions)
CREATE TABLE IF NOT EXISTS role_resource_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL CHECK (resource_type IN ('database', 'table', 'column', 'query', 'api')),
    resource_id VARCHAR(255) NOT NULL,
    permission VARCHAR(50) NOT NULL CHECK (permission IN ('read', 'write', 'delete', 'execute', 'admin')),
    granted_by UUID NOT NULL REFERENCES users(id),
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_role_resource_permission UNIQUE (role_id, resource_type, resource_id, permission)
);

-- 3. Permission Hierarchy Table (parent-child resource relationships)
CREATE TABLE IF NOT EXISTS permission_hierarchy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_resource_type VARCHAR(50) NOT NULL CHECK (parent_resource_type IN ('database', 'table', 'column', 'query', 'api')),
    parent_resource_id VARCHAR(255) NOT NULL,
    child_resource_type VARCHAR(50) NOT NULL CHECK (child_resource_type IN ('database', 'table', 'column', 'query', 'api')),
    child_resource_id VARCHAR(255) NOT NULL,
    inherit_permissions BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_parent_child_hierarchy UNIQUE (parent_resource_type, parent_resource_id, child_resource_type, child_resource_id)
);

-- Create indexes for efficient permission lookups

-- Resource Permissions Indexes
CREATE INDEX IF NOT EXISTS idx_resource_permissions_user_id ON resource_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_resource_permissions_resource ON resource_permissions(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_permissions_permission ON resource_permissions(permission);
CREATE INDEX IF NOT EXISTS idx_resource_permissions_expires_at ON resource_permissions(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_resource_permissions_user_resource ON resource_permissions(user_id, resource_type, resource_id);

-- Role Resource Permissions Indexes
CREATE INDEX IF NOT EXISTS idx_role_resource_permissions_role_id ON role_resource_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_resource_permissions_resource ON role_resource_permissions(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_role_resource_permissions_permission ON role_resource_permissions(permission);
CREATE INDEX IF NOT EXISTS idx_role_resource_permissions_role_resource ON role_resource_permissions(role_id, resource_type, resource_id);

-- Permission Hierarchy Indexes
CREATE INDEX IF NOT EXISTS idx_permission_hierarchy_parent ON permission_hierarchy(parent_resource_type, parent_resource_id);
CREATE INDEX IF NOT EXISTS idx_permission_hierarchy_child ON permission_hierarchy(child_resource_type, child_resource_id);
CREATE INDEX IF NOT EXISTS idx_permission_hierarchy_inherit ON permission_hierarchy(inherit_permissions) WHERE inherit_permissions = TRUE;

-- Create trigger function for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_resource_permissions_updated_at
    BEFORE UPDATE ON resource_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_role_resource_permissions_updated_at
    BEFORE UPDATE ON role_resource_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permission_hierarchy_updated_at
    BEFORE UPDATE ON permission_hierarchy
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE resource_permissions IS 'User-level resource permissions for fine-grained access control';
COMMENT ON TABLE role_resource_permissions IS 'Role-level resource permissions inherited by users with those roles';
COMMENT ON TABLE permission_hierarchy IS 'Defines parent-child relationships between resources for permission inheritance';

COMMENT ON COLUMN resource_permissions.conditions IS 'JSONB field for conditional permissions (e.g., time-based, IP-based restrictions)';
COMMENT ON COLUMN resource_permissions.expires_at IS 'Timestamp when the permission expires (NULL for permanent permissions)';
COMMENT ON COLUMN permission_hierarchy.inherit_permissions IS 'Whether child resources inherit permissions from parent resources';
