"""
Authentication repositories for SamvadQL.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import text

from models.auth import (
    User,
    UserCreate,
    UserUpdate,
    Role,
    RoleCreate,
    RoleUpdate,
    UserRole,
    RefreshToken,
    APIToken,
    ResourceType,
    ResourcePermission,
    ResourcePermissionGrant,
    RoleResourcePermission,
    PermissionHierarchy,
)
from core.db.connection import get_db_session


class UserRepository:
    """Repository for user management."""

    def __init__(self):
        pass

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create a new user."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser)
                VALUES (:username, :email, :hashed_password, :full_name, :is_active, :is_superuser)
                RETURNING id, username, email, hashed_password, full_name, is_active, is_superuser,
                         created_at, updated_at, last_login
            """
            )

            result = await session.execute(
                query,
                {
                    "username": user_data.username.lower(),
                    "email": user_data.email.lower(),
                    "hashed_password": hashed_password,
                    "full_name": user_data.full_name,
                    "is_active": True,
                    "is_superuser": False,
                },
            )

            row = result.fetchone()
            if not row:
                raise Exception("Failed to create user")

            await session.commit()
            return User(**dict(row._mapping))

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, username, email, hashed_password, full_name, is_active, is_superuser,
                       created_at, updated_at, last_login
                FROM users
                WHERE username = :username AND is_active = true
            """
            )

            result = await session.execute(query, {"username": username.lower()})
            row = result.fetchone()
            return User(**dict(row._mapping)) if row else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, username, email, hashed_password, full_name, is_active, is_superuser,
                       created_at, updated_at, last_login
                FROM users
                WHERE email = :email AND is_active = true
            """
            )

            result = await session.execute(query, {"email": email.lower()})
            row = result.fetchone()
            return User(**dict(row._mapping)) if row else None

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, username, email, hashed_password, full_name, is_active, is_superuser,
                       created_at, updated_at, last_login
                FROM users
                WHERE id = :user_id AND is_active = true
            """
            )

            result = await session.execute(query, {"user_id": user_id})
            row = result.fetchone()
            return User(**dict(row._mapping)) if row else None

    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        async with get_db_session() as session:
            # Build dynamic update query
            update_fields = []
            params = {"user_id": user_id, "updated_at": datetime.now(timezone.utc)}

            if user_data.email is not None:
                update_fields.append("email = :email")
                params["email"] = user_data.email.lower()

            if user_data.full_name is not None:
                update_fields.append("full_name = :full_name")
                params["full_name"] = user_data.full_name

            if user_data.is_active is not None:
                update_fields.append("is_active = :is_active")
                params["is_active"] = user_data.is_active

            if not update_fields:
                return await self.get_user_by_id(user_id)

            update_fields.append("updated_at = :updated_at")

            query = text(
                f"""
                UPDATE users
                SET {", ".join(update_fields)}
                WHERE id = :user_id
                RETURNING id, username, email, hashed_password, full_name, is_active, is_superuser,
                         created_at, updated_at, last_login
            """
            )

            result = await session.execute(query, params)
            row = result.fetchone()

            if row:
                await session.commit()
                return User(**dict(row._mapping))
            return None

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        async with get_db_session() as session:
            query = text(
                """
                UPDATE users
                SET last_login = :last_login, updated_at = :updated_at
                WHERE id = :user_id
            """
            )

            await session.execute(
                query,
                {
                    "user_id": user_id,
                    "last_login": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all active users."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, username, email, hashed_password, full_name, is_active, is_superuser,
                       created_at, updated_at, last_login
                FROM users
                WHERE is_active = true
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """
            )

            result = await session.execute(query, {"skip": skip, "limit": limit})
            rows = result.fetchall()
            return [User(**dict(row._mapping)) for row in rows]


class RoleRepository:
    """Repository for role management."""

    def __init__(self):
        pass

    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO roles (name, description, permissions)
                VALUES (:name, :description, :permissions)
                RETURNING id, name, description, permissions, created_at, updated_at
            """
            )

            result = await session.execute(
                query,
                {
                    "name": role_data.name.lower(),
                    "description": role_data.description,
                    "permissions": role_data.permissions,
                },
            )

            row = result.fetchone()
            if not row:
                raise Exception("Failed to create role")

            await session.commit()
            return Role(**dict(row._mapping))

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, name, description, permissions, created_at, updated_at
                FROM roles
                WHERE name = :name
            """
            )

            result = await session.execute(query, {"name": name.lower()})
            row = result.fetchone()
            return Role(**dict(row._mapping)) if row else None

    async def get_role_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, name, description, permissions, created_at, updated_at
                FROM roles
                WHERE id = :role_id
            """
            )

            result = await session.execute(query, {"role_id": role_id})
            row = result.fetchone()
            return Role(**dict(row._mapping)) if row else None

    async def list_roles(self) -> List[Role]:
        """List all roles."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, name, description, permissions, created_at, updated_at
                FROM roles
                ORDER BY name
            """
            )

            result = await session.execute(query)
            rows = result.fetchall()
            return [Role(**dict(row._mapping)) for row in rows]

    async def update_role(self, role_id: UUID, role_data: RoleUpdate) -> Optional[Role]:
        """Update role information."""
        async with get_db_session() as session:
            update_fields = []
            params = {"role_id": role_id, "updated_at": datetime.now(timezone.utc)}

            if role_data.description is not None:
                update_fields.append("description = :description")
                params["description"] = role_data.description

            if role_data.permissions is not None:
                update_fields.append("permissions = :permissions")
                params["permissions"] = role_data.permissions

            if not update_fields:
                return await self.get_role_by_id(role_id)

            update_fields.append("updated_at = :updated_at")

            query = text(
                f"""
                UPDATE roles
                SET {", ".join(update_fields)}
                WHERE id = :role_id
                RETURNING id, name, description, permissions, created_at, updated_at
            """
            )

            result = await session.execute(query, params)
            row = result.fetchone()

            if row:
                await session.commit()
                return Role(**dict(row._mapping))
            return None


class UserRoleRepository:
    """Repository for user-role relationships."""

    def __init__(self):
        pass

    async def assign_role_to_user(self, user_id: UUID, role_id: UUID) -> UserRole:
        """Assign a role to a user."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                ON CONFLICT (user_id, role_id) DO NOTHING
                RETURNING user_id, role_id, assigned_at
            """
            )

            result = await session.execute(
                query, {"user_id": user_id, "role_id": role_id}
            )

            row = result.fetchone()
            if not row:
                # Check if assignment already exists
                existing = await self.get_user_role(user_id, role_id)
                if existing:
                    return existing
                raise Exception("Failed to assign role to user")

            await session.commit()
            return UserRole(**dict(row._mapping))

    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Remove a role from a user."""
        async with get_db_session() as session:
            query = text(
                """
                DELETE FROM user_roles
                WHERE user_id = :user_id AND role_id = :role_id
            """
            )

            result = await session.execute(
                query, {"user_id": user_id, "role_id": role_id}
            )
            row = result.scalar_one_or_none()
            await session.commit()

            return row is not None

    async def get_user_role(self, user_id: UUID, role_id: UUID) -> Optional[UserRole]:
        """Get specific user-role assignment."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT user_id, role_id, assigned_at
                FROM user_roles
                WHERE user_id = :user_id AND role_id = :role_id
            """
            )

            result = await session.execute(
                query, {"user_id": user_id, "role_id": role_id}
            )
            row = result.fetchone()
            return UserRole(**dict(row._mapping)) if row else None

    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles for a user."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT r.id, r.name, r.description, r.permissions, r.created_at, r.updated_at
                FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = :user_id
                ORDER BY r.name
            """
            )

            result = await session.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            return [Role(**dict(row._mapping)) for row in rows]

    async def get_role_users(self, role_id: UUID) -> List[User]:
        """Get all users with a specific role."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT u.id, u.username, u.email, u.hashed_password, u.full_name,
                       u.is_active, u.is_superuser, u.created_at, u.updated_at, u.last_login
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                WHERE ur.role_id = :role_id AND u.is_active = true
                ORDER BY u.username
            """
            )

            result = await session.execute(query, {"role_id": role_id})
            rows = result.fetchall()
            return [User(**dict(row._mapping)) for row in rows]


class RefreshTokenRepository:
    """Repository for refresh token management."""

    def __init__(self):
        pass

    async def create_refresh_token(
        self, user_id: UUID, token: str, expires_at: datetime
    ) -> RefreshToken:
        """Create a new refresh token."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO refresh_tokens (user_id, token, expires_at)
                VALUES (:user_id, :token, :expires_at)
                RETURNING id, user_id, token, expires_at, created_at, is_revoked
            """
            )

            result = await session.execute(
                query, {"user_id": user_id, "token": token, "expires_at": expires_at}
            )

            row = result.fetchone()
            if not row:
                raise Exception("Failed to create refresh token")

            await session.commit()
            return RefreshToken(**dict(row._mapping))

    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, user_id, token, expires_at, created_at, is_revoked
                FROM refresh_tokens
                WHERE token = :token AND is_revoked = false
            """
            )

            result = await session.execute(query, {"token": token})
            row = result.fetchone()
            return RefreshToken(**dict(row._mapping)) if row else None

    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        async with get_db_session() as session:
            query = text(
                """
                UPDATE refresh_tokens
                SET is_revoked = true
                WHERE token = :token
            """
            )

            result = await session.execute(query, {"token": token})
            row = result.scalar_one_or_none()
            await session.commit()
            return row is not None

    async def revoke_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user."""
        async with get_db_session() as session:
            query = text(
                """
                UPDATE refresh_tokens
                SET is_revoked = true
                WHERE user_id = :user_id AND is_revoked = false
            """
            )

            result = await session.execute(query, {"user_id": user_id})
            row = result.scalar_one_or_none()
            await session.commit()
            return row is not None

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired refresh tokens."""
        async with get_db_session() as session:
            query = text(
                """
                DELETE FROM refresh_tokens
                WHERE expires_at < :now OR is_revoked = true
            """
            )

            result = await session.execute(query, {"now": datetime.now(timezone.utc)})
            row = result.scalar_one_or_none()
            await session.commit()
            return row is not None


class APITokenRepository:
    """Repository for API token management."""

    def __init__(self):
        pass

    async def create_api_token(
        self,
        user_id: UUID,
        name: str,
        token: str,
        expires_at: Optional[datetime] = None,
    ) -> APIToken:
        """Create a new API token."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO api_tokens (user_id, name, token, expires_at)
                VALUES (:user_id, :name, :token, :expires_at)
                RETURNING id, user_id, name, token, expires_at, created_at, last_used, is_active
            """
            )

            result = await session.execute(
                query,
                {
                    "user_id": user_id,
                    "name": name,
                    "token": token,
                    "expires_at": expires_at,
                },
            )

            row = result.fetchone()
            if not row:
                raise Exception("Failed to create API token")

            await session.commit()
            return APIToken(**dict(row._mapping))

    async def get_api_token(self, token: str) -> Optional[APIToken]:
        """Get API token by token string."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, user_id, name, token, expires_at, created_at, last_used, is_active
                FROM api_tokens
                WHERE token = :token AND is_active = true
                AND (expires_at IS NULL OR expires_at > :now)
            """
            )

            result = await session.execute(
                query, {"token": token, "now": datetime.now(timezone.utc)}
            )
            row = result.fetchone()
            return APIToken(**dict(row._mapping)) if row else None

    async def update_token_last_used(self, token: str) -> None:
        """Update the last used timestamp for an API token."""
        async with get_db_session() as session:
            query = text(
                """
                UPDATE api_tokens
                SET last_used = :last_used
                WHERE token = :token
            """
            )

            await session.execute(
                query, {"token": token, "last_used": datetime.now(timezone.utc)}
            )
            await session.commit()

    async def get_user_api_tokens(self, user_id: UUID) -> List[APIToken]:
        """Get all API tokens for a user."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, user_id, name, token, expires_at, created_at, last_used, is_active
                FROM api_tokens
                WHERE user_id = :user_id AND is_active = true
                ORDER BY created_at DESC
            """
            )

            result = await session.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            return [APIToken(**dict(row._mapping)) for row in rows]

    async def revoke_api_token(self, token_id: UUID, user_id: UUID) -> bool:
        """Revoke an API token."""
        async with get_db_session() as session:
            query = text(
                """
                UPDATE api_tokens
                SET is_active = false
                WHERE id = :token_id AND user_id = :user_id
            """
            )

            result = await session.execute(
                query, {"token_id": token_id, "user_id": user_id}
            )
            row = result.scalar_one_or_none()
            await session.commit()
            return row is not None

    async def cleanup_expired_tokens(self) -> int:
        """Deactivate expired API tokens."""
        async with get_db_session() as session:
            query = text(
                """
                UPDATE api_tokens
                SET is_active = false
                WHERE expires_at < :now AND is_active = true
            """
            )

            result = await session.execute(query, {"now": datetime.now(timezone.utc)})
            row = result.scalar_one_or_none()
            await session.commit()
            return row is not None


class ResourcePermissionRepository:
    """Repository for resource-level permissions."""

    def __init__(self):
        pass

    async def grant_permission(
        self,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
        granted_by: UUID,
        expires_at: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> ResourcePermissionGrant:
        """Grant a resource permission to a user."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO resource_permissions
                (user_id, resource_type, resource_id, permission, granted_by, expires_at, conditions)
                VALUES (:user_id, :resource_type, :resource_id, :permission, :granted_by, :expires_at, :conditions)
                ON CONFLICT (user_id, resource_type, resource_id, permission)
                DO UPDATE SET expires_at = :expires_at, conditions = :conditions, updated_at = CURRENT_TIMESTAMP
                RETURNING id, user_id, resource_type, resource_id, permission, granted_by,
                         granted_at, expires_at, conditions, created_at, updated_at
            """
            )

            result = await session.execute(
                query,
                {
                    "user_id": user_id,
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "permission": permission.value,
                    "granted_by": granted_by,
                    "expires_at": expires_at,
                    "conditions": conditions,
                },
            )
            await session.commit()
            row = result.fetchone()
            if not row:
                raise Exception("Failed to grant permission")
            return ResourcePermissionGrant(**dict(row._mapping))

    async def revoke_permission(
        self,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
    ) -> bool:
        """Revoke a resource permission from a user."""
        async with get_db_session() as session:
            query = text(
                """
                DELETE FROM resource_permissions
                WHERE user_id = :user_id AND resource_type = :resource_type
                AND resource_id = :resource_id AND permission = :permission
            """
            )

            result = await session.execute(
                query,
                {
                    "user_id": user_id,
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "permission": permission.value,
                },
            )
            row = result.scalar_one_or_none()
            await session.commit()
            return row is not None

    async def get_user_resource_permissions(
        self,
        user_id: UUID,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None,
    ) -> List[ResourcePermissionGrant]:
        """Get all permissions for a user on specific resource(s)."""
        async with get_db_session() as session:
            conditions = [
                "user_id = :user_id",
                "(expires_at IS NULL OR expires_at > :now)",
            ]
            params = {"user_id": user_id, "now": datetime.now(timezone.utc)}

            if resource_type:
                conditions.append("resource_type = :resource_type")
                params["resource_type"] = resource_type.value

            if resource_id:
                conditions.append("resource_id = :resource_id")
                params["resource_id"] = resource_id

            query = text(
                f"""
                SELECT id, user_id, resource_type, resource_id, permission, granted_by,
                       granted_at, expires_at, conditions, created_at, updated_at
                FROM resource_permissions
                WHERE {" AND ".join(conditions)}
                ORDER BY created_at DESC
            """
            )

            result = await session.execute(query, params)
            rows = result.fetchall()
            return [ResourcePermissionGrant(**dict(row._mapping)) for row in rows]

    async def get_all_user_permissions(
        self, user_id: UUID
    ) -> List[ResourcePermissionGrant]:
        """Get all resource permissions for a user."""
        return await self.get_user_resource_permissions(user_id)

    async def check_permission(
        self,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
    ) -> bool:
        """Check if user has a specific permission on a resource."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT COUNT(*) as count
                FROM resource_permissions
                WHERE user_id = :user_id AND resource_type = :resource_type
                AND resource_id = :resource_id AND permission = :permission
                AND (expires_at IS NULL OR expires_at > :now)
            """
            )

            result = await session.execute(
                query,
                {
                    "user_id": user_id,
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "permission": permission.value,
                    "now": datetime.now(timezone.utc),
                },
            )
            row = result.fetchone()
            if not row:
                return False
            return row[0] > 0

    async def list_users_with_permission(
        self,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
    ) -> List[UUID]:
        """List all users with a specific permission on a resource."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT DISTINCT user_id
                FROM resource_permissions
                WHERE resource_type = :resource_type AND resource_id = :resource_id
                AND permission = :permission
                AND (expires_at IS NULL OR expires_at > :now)
            """
            )

            result = await session.execute(
                query,
                {
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "permission": permission.value,
                    "now": datetime.now(timezone.utc),
                },
            )
            rows = result.fetchall()
            return [row[0] for row in rows]


class RoleResourcePermissionRepository:
    """Repository for role-level resource permissions."""

    def __init__(self):
        pass

    async def grant_role_permission(
        self,
        role_id: UUID,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
        granted_by: UUID,
    ) -> RoleResourcePermission:
        """Grant a resource permission to a role."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO role_resource_permissions
                (role_id, resource_type, resource_id, permission, granted_by)
                VALUES (:role_id, :resource_type, :resource_id, :permission, :granted_by)
                ON CONFLICT (role_id, resource_type, resource_id, permission)
                DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING id, role_id, resource_type, resource_id, permission, granted_by,
                         granted_at, created_at, updated_at
            """
            )

            result = await session.execute(
                query,
                {
                    "role_id": role_id,
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "permission": permission.value,
                    "granted_by": granted_by,
                },
            )
            await session.commit()
            row = result.fetchone()
            if not row:
                raise Exception("Failed to grant role permission")
            return RoleResourcePermission(**dict(row._mapping))

    async def revoke_role_permission(
        self,
        role_id: UUID,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
    ) -> bool:
        """Revoke a resource permission from a role."""
        async with get_db_session() as session:
            query = text(
                """
                DELETE FROM role_resource_permissions
                WHERE role_id = :role_id AND resource_type = :resource_type
                AND resource_id = :resource_id AND permission = :permission
            """
            )

            result = await session.execute(
                query,
                {
                    "role_id": role_id,
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "permission": permission.value,
                },
            )
            row = result.scalar_one_or_none()
            await session.commit()
            return row is not None

    async def get_role_resource_permissions(
        self, role_id: UUID
    ) -> List[RoleResourcePermission]:
        """Get all resource permissions for a role."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, role_id, resource_type, resource_id, permission, granted_by,
                       granted_at, created_at, updated_at
                FROM role_resource_permissions
                WHERE role_id = :role_id
                ORDER BY created_at DESC
            """
            )

            result = await session.execute(query, {"role_id": role_id})
            rows = result.fetchall()
            return [RoleResourcePermission(**dict(row._mapping)) for row in rows]

    async def list_roles_with_permission(
        self,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
    ) -> List[UUID]:
        """List all roles with a specific permission on a resource."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT DISTINCT role_id
                FROM role_resource_permissions
                WHERE resource_type = :resource_type AND resource_id = :resource_id
                AND permission = :permission
            """
            )

            result = await session.execute(
                query,
                {
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "permission": permission.value,
                },
            )
            rows = result.fetchall()
            return [row[0] for row in rows]

    async def get_inherited_role_permissions(
        self, role_ids: List[UUID], child_type: ResourceType, child_id: str
    ) -> List[RoleResourcePermission]:
        """
        Get inherited role permissions from parent resources.

        Joins role_resource_permissions with permission_hierarchy to find permissions
        granted to roles on parent resources that should be inherited by child resources.

        Args:
            role_ids: List of role IDs to check permissions for
            child_type: Resource type of the child resource
            child_id: Resource ID of the child resource

        Returns:
            List of RoleResourcePermission objects inherited from parent resources
        """
        if not role_ids:
            return []

        async with get_db_session() as session:
            # Build parameterized query for role_ids
            role_params = {
                f"role_id_{i}": role_id for i, role_id in enumerate(role_ids)
            }
            role_placeholders = ", ".join(
                [f":role_id_{i}" for i in range(len(role_ids))]
            )

            query = text(
                f"""
                SELECT DISTINCT rrp.id, rrp.role_id, rrp.resource_type, rrp.resource_id,
                       rrp.permission, rrp.granted_by, rrp.granted_at, rrp.created_at, rrp.updated_at
                FROM role_resource_permissions rrp
                JOIN permission_hierarchy ph ON rrp.resource_type = ph.parent_resource_type
                    AND rrp.resource_id = ph.parent_resource_id
                WHERE ph.child_resource_type = :child_type
                AND ph.child_resource_id = :child_id
                AND ph.inherit_permissions = true
                AND rrp.role_id IN ({role_placeholders})
                ORDER BY rrp.created_at DESC
            """
            )

            params = {
                "child_type": child_type.value,
                "child_id": child_id,
                **role_params,
            }

            result = await session.execute(query, params)
            rows = result.fetchall()
            return [RoleResourcePermission(**dict(row._mapping)) for row in rows]


class PermissionHierarchyRepository:
    """Repository for permission hierarchy management."""

    def __init__(self):
        pass

    async def create_hierarchy(
        self,
        parent_type: ResourceType,
        parent_id: str,
        child_type: ResourceType,
        child_id: str,
        inherit: bool = True,
    ) -> PermissionHierarchy:
        """Create a parent-child resource relationship."""
        async with get_db_session() as session:
            query = text(
                """
                INSERT INTO permission_hierarchy
                (parent_resource_type, parent_resource_id, child_resource_type, child_resource_id, inherit_permissions)
                VALUES (:parent_type, :parent_id, :child_type, :child_id, :inherit)
                ON CONFLICT (parent_resource_type, parent_resource_id, child_resource_type, child_resource_id)
                DO UPDATE SET inherit_permissions = :inherit, updated_at = CURRENT_TIMESTAMP
                RETURNING id, parent_resource_type, parent_resource_id, child_resource_type, child_resource_id,
                         inherit_permissions, created_at, updated_at
            """
            )

            result = await session.execute(
                query,
                {
                    "parent_type": parent_type.value,
                    "parent_id": parent_id,
                    "child_type": child_type.value,
                    "child_id": child_id,
                    "inherit": inherit,
                },
            )
            await session.commit()
            row = result.fetchone()
            if not row:
                raise Exception("Failed to create permission hierarchy")
            return PermissionHierarchy(**dict(row._mapping))

    async def get_inherited_permissions(
        self, resource_type: ResourceType, resource_id: str, user_id: UUID
    ) -> List[ResourcePermissionGrant]:
        """Resolve inherited permissions from parent resources."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT DISTINCT rp.id, rp.user_id, rp.resource_type, rp.resource_id, rp.permission,
                       rp.granted_by, rp.granted_at, rp.expires_at, rp.conditions, rp.created_at, rp.updated_at
                FROM resource_permissions rp
                JOIN permission_hierarchy ph ON rp.resource_type = ph.parent_resource_type
                    AND rp.resource_id = ph.parent_resource_id
                WHERE ph.child_resource_type = :resource_type
                AND ph.child_resource_id = :resource_id
                AND ph.inherit_permissions = true
                AND rp.user_id = :user_id
                AND (rp.expires_at IS NULL OR rp.expires_at > :now)
            """
            )

            result = await session.execute(
                query,
                {
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "user_id": user_id,
                    "now": datetime.now(timezone.utc),
                },
            )
            rows = result.fetchall()
            return [ResourcePermissionGrant(**dict(row._mapping)) for row in rows]

    async def get_children(
        self, resource_type: ResourceType, resource_id: str
    ) -> List[PermissionHierarchy]:
        """Get all child resources."""
        async with get_db_session() as session:
            query = text(
                """
                SELECT id, parent_resource_type, parent_resource_id, child_resource_type, child_resource_id,
                       inherit_permissions, created_at, updated_at
                FROM permission_hierarchy
                WHERE parent_resource_type = :resource_type AND parent_resource_id = :resource_id
                ORDER BY created_at DESC
            """
            )

            result = await session.execute(
                query,
                {"resource_type": resource_type.value, "resource_id": resource_id},
            )
            rows = result.fetchall()
            return [PermissionHierarchy(**dict(row._mapping)) for row in rows]
