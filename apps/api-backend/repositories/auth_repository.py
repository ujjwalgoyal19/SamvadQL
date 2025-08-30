"""
Authentication repositories for SamvadQL.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.auth import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    Role,
    RoleCreate,
    RoleUpdate,
    UserRole,
    RefreshToken,
    APIToken,
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
            params = {"user_id": user_id, "updated_at": datetime.utcnow()}

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
                SET {', '.join(update_fields)}
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
                    "last_login": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
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
            params = {"role_id": role_id, "updated_at": datetime.utcnow()}

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
                SET {', '.join(update_fields)}
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

            await session.commit()
            return result.rowcount > 0

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
            await session.commit()
            return result.rowcount > 0

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
            await session.commit()
            return result.rowcount

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired refresh tokens."""
        async with get_db_session() as session:
            query = text(
                """
                DELETE FROM refresh_tokens
                WHERE expires_at < :now OR is_revoked = true
            """
            )

            result = await session.execute(query, {"now": datetime.utcnow()})
            await session.commit()
            return result.rowcount


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
                query, {"token": token, "now": datetime.utcnow()}
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
                query, {"token": token, "last_used": datetime.utcnow()}
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
            await session.commit()
            return result.rowcount > 0

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

            result = await session.execute(query, {"now": datetime.utcnow()})
            await session.commit()
            return result.rowcount
