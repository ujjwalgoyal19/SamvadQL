"""
User repository for SamvadQL.
Handles user CRUD operations and authentication-related queries.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from models.auth import User, UserCreate, UserUpdate
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user management using BaseRepository pattern."""

    def get_table_name(self) -> str:
        """Return the table name for users."""
        return "users"

    def to_dict(self, entity: User) -> Dict[str, Any]:
        """Convert User entity to dictionary for database storage."""
        return {
            "id": str(entity.id),
            "username": entity.username,
            "email": entity.email,
            "hashed_password": entity.hashed_password,
            "full_name": entity.full_name,
            "is_active": entity.is_active,
            "is_superuser": entity.is_superuser,
            "created_at": entity.created_at or datetime.now(timezone.utc),
            "updated_at": entity.updated_at or datetime.now(timezone.utc),
            "last_login": entity.last_login,
        }

    def from_dict(self, data: Dict[str, Any]) -> User:
        """Convert dictionary from database to User entity."""
        # Handle UUID conversion
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])

        # Handle datetime conversion if needed
        for date_field in ["created_at", "updated_at", "last_login"]:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])

        return User(**data)

    # High-level convenience methods wrapping BaseRepository operations

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create a new user with hashed password."""
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid4(),
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_superuser=False,
            created_at=now,
            updated_at=now,
            last_login=None,
        )
        return await self.create(user)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        users = await self.find_by({"username": username}, limit=1)
        return users[0] if users else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        users = await self.find_by({"email": email}, limit=1)
        return users[0] if users else None

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return await self.get_by_id(user_id)

    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        # Convert UserUpdate to dict, excluding None values
        updates = user_data.model_dump(exclude_unset=True, exclude_none=True)

        if not updates:
            return await self.get_user_by_id(user_id)

        return await self.update(user_id, updates)

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        await self.update(user_id, {"last_login": datetime.now(timezone.utc)})

    async def list_users(
        self, skip: int = 0, limit: int = 100, order_by: str = "username"
    ) -> List[User]:
        """List users with pagination."""
        return await self.get_all(limit=limit, offset=skip, order_by=order_by)

    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """Deactivate a user (soft delete)."""
        return await self.update(user_id, {"is_active": False})

    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """Activate a user."""
        return await self.update(user_id, {"is_active": True})

    async def count_users(self, active_only: bool = False) -> int:
        """Count total users, optionally filtering by active status."""
        if active_only:
            return await self.count(where_clause="is_active = $1", params=[True])
        return await self.count()

    async def search_users(self, search_term: str, limit: int = 100) -> List[User]:
        """Search users by username, email, or full name."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE
                username ILIKE $1 OR
                email ILIKE $1 OR
                full_name ILIKE $1
            ORDER BY username
            LIMIT $2
        """

        search_pattern = f"%{search_term}%"
        results = await self.execute_raw_query(
            query, params=[search_pattern, limit], fetch_one=False
        )

        return [self.from_dict(row) for row in results] if results else []
