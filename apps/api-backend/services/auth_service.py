"""
Authentication service for SamvadQL.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from core.config import settings
from models.auth import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    Role,
    TokenData,
    Token,
    RefreshToken,
    APIToken,
    Permission,
)


class AuthService:
    """Authentication and authorization service."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)

    def create_access_token(
        self,
        user: User,
        permissions: List[str],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode = {
            "sub": str(user.id),
            "username": user.username,
            "permissions": permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid4()),
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, user_id: UUID) -> str:
        """Create a refresh token."""
        expire = datetime.utcnow() + timedelta(days=30)  # Refresh tokens last 30 days

        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid4()),
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                return None

            user_id = UUID(user_id_str)
            username: str = payload.get("username")
            permissions: List[str] = payload.get("permissions", [])
            exp_timestamp: int = payload.get("exp")
            iat_timestamp: int = payload.get("iat")
            jti: str = payload.get("jti")

            if not all([username, exp_timestamp, iat_timestamp, jti]):
                return None

            exp = datetime.fromtimestamp(exp_timestamp)
            iat = datetime.fromtimestamp(iat_timestamp)

            # Check if token is expired
            if datetime.utcnow() > exp:
                return None

            return TokenData(
                user_id=user_id,
                username=username,
                permissions=permissions,
                exp=exp,
                iat=iat,
                jti=jti,
            )

        except (JWTError, ValueError, KeyError):
            return None

    def verify_refresh_token(self, token: str) -> Optional[UUID]:
        """Verify a refresh token and return user ID."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id_str: str = payload.get("sub")
            token_type: str = payload.get("type")
            exp_timestamp: int = payload.get("exp")

            if not all([user_id_str, token_type, exp_timestamp]):
                return None

            if token_type != "refresh":
                return None

            user_id = UUID(user_id_str)
            exp = datetime.fromtimestamp(exp_timestamp)

            # Check if token is expired
            if datetime.utcnow() > exp:
                return None

            return user_id

        except (JWTError, ValueError, KeyError):
            return None

    def create_api_token(self, length: int = 32) -> str:
        """Create a secure API token."""
        return secrets.token_urlsafe(length)

    def hash_api_token(self, token: str) -> str:
        """Hash an API token for storage."""
        return self.pwd_context.hash(token)

    def verify_api_token(self, token: str, hashed_token: str) -> bool:
        """Verify an API token against its hash."""
        return self.pwd_context.verify(token, hashed_token)

    def has_permission(
        self, user_permissions: List[str], required_permission: str
    ) -> bool:
        """Check if user has a specific permission."""
        # Superuser has all permissions
        if Permission.ADMIN_ALL.value in user_permissions:
            return True

        # Check for exact permission match
        if required_permission in user_permissions:
            return True

        # Check for wildcard permissions
        permission_parts = required_permission.split(":")
        if len(permission_parts) == 2:
            resource, action = permission_parts
            wildcard_permission = f"{resource}:*"
            if wildcard_permission in user_permissions:
                return True

        return False

    def has_any_permission(
        self, user_permissions: List[str], required_permissions: List[str]
    ) -> bool:
        """Check if user has any of the required permissions."""
        return any(
            self.has_permission(user_permissions, perm) for perm in required_permissions
        )

    def has_all_permissions(
        self, user_permissions: List[str], required_permissions: List[str]
    ) -> bool:
        """Check if user has all required permissions."""
        return all(
            self.has_permission(user_permissions, perm) for perm in required_permissions
        )

    def get_user_permissions(self, roles: List[Role]) -> List[str]:
        """Get all permissions for a user based on their roles."""
        permissions = set()

        for role in roles:
            permissions.update(role.permissions)

        return list(permissions)

    def create_tokens(self, user: User, permissions: List[str]) -> Token:
        """Create both access and refresh tokens for a user."""
        access_token = self.create_access_token(user, permissions)
        refresh_token = self.create_refresh_token(user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
        )

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength and return detailed feedback."""
        issues = []
        score = 0

        # Length check
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        else:
            score += 1

        # Character variety checks
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not has_upper:
            issues.append("Password must contain at least one uppercase letter")
        else:
            score += 1

        if not has_lower:
            issues.append("Password must contain at least one lowercase letter")
        else:
            score += 1

        if not has_digit:
            issues.append("Password must contain at least one digit")
        else:
            score += 1

        if has_special:
            score += 1

        # Length bonus
        if len(password) >= 12:
            score += 1

        # Determine strength
        if score <= 2:
            strength = "weak"
        elif score <= 4:
            strength = "medium"
        else:
            strength = "strong"

        return {
            "is_valid": len(issues) == 0,
            "strength": strength,
            "score": score,
            "issues": issues,
        }


# Global auth service instance
auth_service = AuthService()
