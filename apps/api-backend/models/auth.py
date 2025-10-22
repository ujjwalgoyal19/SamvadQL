"""
Authentication and authorization models for SamvadQL.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum


class Permission(str, Enum):
    """System permissions."""

    # Query permissions
    QUERY_READ = "query:read"
    QUERY_CREATE = "query:create"
    QUERY_DELETE = "query:delete"

    # Table permissions
    TABLE_READ = "table:read"
    TABLE_WRITE = "table:write"
    TABLE_DELETE = "table:delete"

    # User management permissions
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Role management permissions
    ROLE_READ = "role:read"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    # Feedback permissions
    FEEDBACK_CREATE = "feedback:create"
    FEEDBACK_READ = "feedback:read"

    # API access permissions
    API_ACCESS = "api:access"

    # Admin permissions
    ADMIN_ALL = "*"


class ResourceType(str, Enum):
    """Resource types for ABAC."""

    DATABASE = "database"
    TABLE = "table"
    COLUMN = "column"
    QUERY = "query"
    API = "api"


class ResourcePermission(str, Enum):
    """Resource-level permissions for ABAC."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class User(BaseModel):
    """User model."""

    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers, hyphens, and underscores"
            )
        return v.lower()

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation model."""

    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
            )

        return v


class UserUpdate(BaseModel):
    """User update model."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if v is None:
            return v

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
            )

        return v


class UserResponse(BaseModel):
    """User response model (without sensitive data)."""

    id: UUID
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    resource_permissions: Optional[Dict[str, List[Dict[str, Any]]]] = None

    class Config:
        from_attributes = True


class Role(BaseModel):
    """Role model."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate role name format."""
        return v.lower().replace(" ", "_")

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """Role creation model."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        """Validate permissions list."""
        valid_permissions = [perm.value for perm in Permission]
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")
        return v


class RoleUpdate(BaseModel):
    """Role update model."""

    description: Optional[str] = None
    permissions: Optional[List[str]] = None

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        """Validate permissions list."""
        if v is None:
            return v

        valid_permissions = [perm.value for perm in Permission]
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")
        return v


class UserRole(BaseModel):
    """User role assignment model."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    role_id: UUID
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Token payload data."""

    user_id: UUID
    username: str
    permissions: List[str] = Field(default_factory=list)
    resource_permissions: Optional[Dict[str, List[Dict[str, Any]]]] = None
    exp: datetime
    iat: datetime
    jti: str  # JWT ID


class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str = Field(..., min_length=1)


class PasswordChangeRequest(BaseModel):
    """Password change request model."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
            )

        return v


class APIToken(BaseModel):
    """API token model."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    token_name: str = Field(..., min_length=1, max_length=255)
    token_hash: str
    scopes: List[str] = Field(default_factory=list)
    is_active: bool = True
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class APITokenCreate(BaseModel):
    """API token creation model."""

    token_name: str = Field(..., min_length=1, max_length=255)
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APITokenResponse(BaseModel):
    """API token response model."""

    id: UUID
    token_name: str
    token: str  # Only returned on creation
    scopes: List[str]
    expires_at: Optional[datetime] = None
    created_at: datetime


class RefreshToken(BaseModel):
    """Refresh token model."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    token_hash: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ABAC (Attribute-Based Access Control) Models


class ResourcePermissionGrant(BaseModel):
    """Resource permission grant model."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    resource_type: ResourceType
    resource_id: str = Field(..., min_length=1, max_length=255)
    permission: ResourcePermission
    granted_by: UUID
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class RoleResourcePermission(BaseModel):
    """Role resource permission model."""

    id: UUID = Field(default_factory=uuid4)
    role_id: UUID
    resource_type: ResourceType
    resource_id: str = Field(..., min_length=1, max_length=255)
    permission: ResourcePermission
    granted_by: UUID
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class PermissionHierarchy(BaseModel):
    """Permission hierarchy model for parent-child resource relationships."""

    id: UUID = Field(default_factory=uuid4)
    parent_resource_type: ResourceType
    parent_resource_id: str = Field(..., min_length=1, max_length=255)
    child_resource_type: ResourceType
    child_resource_id: str = Field(..., min_length=1, max_length=255)
    inherit_permissions: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ResourcePermissionCreate(BaseModel):
    """Resource permission creation model."""

    user_id: UUID
    resource_type: ResourceType
    resource_id: str = Field(..., min_length=1, max_length=255)
    permission: ResourcePermission
    expires_at: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None


class ResourcePermissionResponse(BaseModel):
    """Resource permission response model."""

    id: UUID
    user_id: UUID
    resource_type: ResourceType
    resource_id: str
    permission: ResourcePermission
    granted_by: UUID
    granted_at: datetime
    expires_at: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class PermissionCheckRequest(BaseModel):
    """Permission check request model."""

    user_id: UUID
    resource_type: ResourceType
    resource_id: str = Field(..., min_length=1, max_length=255)
    permission: ResourcePermission


class PermissionCheckResponse(BaseModel):
    """Permission check response model."""

    has_permission: bool
    permission: ResourcePermission
    resource_type: ResourceType
    resource_id: str
    reason: Optional[str] = None
    granted_through: Optional[str] = None  # 'direct', 'role', 'inherited', 'superuser'

