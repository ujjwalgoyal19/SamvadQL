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
    ResourceType,
    ResourcePermission,
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
        resource_permissions: Optional[Dict[str, List[Dict[str, Any]]]] = None,
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

        # Add resource permissions to token if provided (be mindful of token size)
        if resource_permissions:
            to_encode["resource_permissions"] = resource_permissions

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
            resource_permissions: Optional[Dict[str, List[Dict[str, Any]]]] = payload.get("resource_permissions")
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
                resource_permissions=resource_permissions,
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

    def create_tokens(self, user: User, permissions: List[str], resource_permissions: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Token:
        """Create both access and refresh tokens for a user."""
        access_token = self.create_access_token(user, permissions, resource_permissions)
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

    # ABAC (Attribute-Based Access Control) Methods

    async def check_resource_permission(
        self,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: str,
        required_permission: ResourcePermission,
        roles: List[Role],
        is_superuser: bool = False,
    ) -> bool:
        """
        Comprehensive permission check considering:
        - Superuser status
        - Direct user resource permissions
        - Role-based resource permissions
        - Inherited permissions from parent resources (user-level)
        - Inherited permissions from parent resources (role-level)
        - Conditional permissions
        """
        from repositories.auth_repository import (
            ResourcePermissionRepository,
            RoleResourcePermissionRepository,
            PermissionHierarchyRepository,
        )

        # Superusers have all permissions
        if is_superuser:
            return True

        resource_perm_repo = ResourcePermissionRepository()
        role_perm_repo = RoleResourcePermissionRepository()
        hierarchy_repo = PermissionHierarchyRepository()

        # Check direct user permissions
        has_direct = await resource_perm_repo.check_permission(
            user_id, resource_type, resource_id, required_permission
        )
        if has_direct:
            return True

        # Check role-based permissions (direct on resource)
        for role in roles:
            role_perms = await role_perm_repo.get_role_resource_permissions(role.id)
            for perm in role_perms:
                if (
                    perm.resource_type == resource_type
                    and perm.resource_id == resource_id
                    and perm.permission == required_permission
                ):
                    return True

        # Check inherited permissions from parent resources (user-level)
        inherited_perms = await hierarchy_repo.get_inherited_permissions(
            resource_type, resource_id, user_id
        )
        for perm in inherited_perms:
            if perm.permission == required_permission:
                # TODO: Evaluate conditions if present
                return True

        # Check inherited permissions from parent resources (role-level)
        if roles:
            role_ids = [role.id for role in roles]
            inherited_role_perms = await role_perm_repo.get_inherited_role_permissions(
                role_ids, resource_type, resource_id
            )
            for perm in inherited_role_perms:
                if perm.permission == required_permission:
                    return True

        return False

    async def get_user_resource_permissions(
        self, user_id: UUID, roles: List[Role]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate all resource permissions for a user from:
        - Direct user grants
        - Role-based grants
        - Inherited permissions (via permission hierarchy)
        Returns structured permission map by resource type.
        """
        from repositories.auth_repository import (
            ResourcePermissionRepository,
            RoleResourcePermissionRepository,
            PermissionHierarchyRepository,
        )

        resource_perm_repo = ResourcePermissionRepository()
        role_perm_repo = RoleResourcePermissionRepository()
        hierarchy_repo = PermissionHierarchyRepository()

        # Get direct user permissions
        user_perms = await resource_perm_repo.get_all_user_permissions(user_id)

        # Get role-based permissions
        role_perms = []
        for role in roles:
            role_perms.extend(await role_perm_repo.get_role_resource_permissions(role.id))

        # Organize by resource type
        permissions_map: Dict[str, List[Dict[str, Any]]] = {
            "databases": [],
            "tables": [],
            "columns": [],
            "queries": [],
            "apis": [],
        }

        # Process user permissions
        for perm in user_perms:
            resource_key = f"{perm.resource_type.value}s"
            if resource_key not in permissions_map:
                permissions_map[resource_key] = []

            # Check if resource already in map
            existing = next(
                (p for p in permissions_map[resource_key] if p["id"] == perm.resource_id),
                None,
            )
            if existing:
                if perm.permission.value not in existing["permissions"]:
                    existing["permissions"].append(perm.permission.value)
            else:
                permissions_map[resource_key].append(
                    {"id": perm.resource_id, "permissions": [perm.permission.value]}
                )

        # Process role permissions
        for perm in role_perms:
            resource_key = f"{perm.resource_type.value}s"
            if resource_key not in permissions_map:
                permissions_map[resource_key] = []

            existing = next(
                (p for p in permissions_map[resource_key] if p["id"] == perm.resource_id),
                None,
            )
            if existing:
                if perm.permission.value not in existing["permissions"]:
                    existing["permissions"].append(perm.permission.value)
            else:
                permissions_map[resource_key].append(
                    {"id": perm.resource_id, "permissions": [perm.permission.value]}
                )

        # Process inherited permissions for each resource type
        # Check each resource in the map for inherited permissions from parent resources
        for resource_type_str, resources in permissions_map.items():
            # Convert resource type string back to enum (e.g., "tables" -> ResourceType.TABLE)
            if not resources:
                continue

            # Map plural keys to ResourceType enum
            resource_type_mapping = {
                "databases": ResourceType.DATABASE,
                "tables": ResourceType.TABLE,
                "columns": ResourceType.COLUMN,
                "queries": ResourceType.QUERY,
                "apis": ResourceType.API,
            }

            resource_type_enum = resource_type_mapping.get(resource_type_str)
            if not resource_type_enum:
                continue

            # For each resource of this type, check for inherited permissions
            for resource in list(resources):  # Use list() to avoid modification during iteration
                resource_id = resource["id"]

                try:
                    inherited_perms = await hierarchy_repo.get_inherited_permissions(
                        resource_type=resource_type_enum,
                        resource_id=resource_id,
                        user_id=user_id,
                    )

                    # Merge inherited permissions into existing resource permissions
                    for inherited_perm in inherited_perms:
                        if inherited_perm.permission.value not in resource["permissions"]:
                            resource["permissions"].append(inherited_perm.permission.value)

                except Exception as e:
                    # Log error but continue processing other resources
                    # Don't let inheritance failures break the entire permission map
                    pass

        return permissions_map

    async def resolve_permission_hierarchy(
        self, resource_type: ResourceType, resource_id: str, user_id: UUID, roles: List[Role]
    ) -> List[str]:
        """
        Resolve permissions considering hierarchy (e.g., database permission implies table permissions).
        Returns list of effective permissions.
        """
        from repositories.auth_repository import PermissionHierarchyRepository

        hierarchy_repo = PermissionHierarchyRepository()

        # Get inherited permissions
        inherited = await hierarchy_repo.get_inherited_permissions(resource_type, resource_id, user_id)

        return [perm.permission.value for perm in inherited]

    async def validate_resource_access(
        self,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: str,
        permission: ResourcePermission,
        roles: List[Role],
        is_superuser: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate and log access attempts.
        Returns detailed validation result.
        """
        has_access = await self.check_resource_permission(
            user_id, resource_type, resource_id, permission, roles, is_superuser
        )

        return {
            "has_access": has_access,
            "user_id": str(user_id),
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "permission": permission.value,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global auth service instance
auth_service = AuthService()
