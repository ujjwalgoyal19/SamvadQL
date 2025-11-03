"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Callable

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.auth import User, ResourceType, ResourcePermission, Permission
from services.auth_service import auth_service
from repositories.auth_repository import (
    UserRepository,
    UserRoleRepository,
)

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Extract and validate JWT token, return current user.
    Raises HTTP 401 if token is invalid or user not found.
    """
    token = credentials.credentials
    token_data = auth_service.verify_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository()
    user = await user_repo.get_user_by_id(token_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def require_permission(permission: str) -> Callable:
    """
    Factory function that returns a dependency to check if user has a specific permission.
    """

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # Get user roles
        role_repo = UserRoleRepository()
        user_roles = await role_repo.get_user_roles(current_user.id)

        # Get permissions from roles
        permissions = auth_service.get_user_permissions(user_roles)

        # Check if user has the required permission or is superuser
        if (
            current_user.is_superuser
            or permission in permissions
            or Permission.ADMIN_ALL.value in permissions
        ):
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission} required",
        )

    return permission_checker


def require_any_permission(*required_permissions: str) -> Callable:
    """
    Factory function to check if user has any of the specified permissions.
    """

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        role_repo = UserRoleRepository()
        user_roles = await role_repo.get_user_roles(current_user.id)
        permissions = auth_service.get_user_permissions(user_roles)

        if current_user.is_superuser or Permission.ADMIN_ALL.value in permissions:
            return current_user

        if any(perm in permissions for perm in required_permissions):
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: one of {required_permissions} required",
        )

    return permission_checker


def require_all_permissions(*required_permissions: str) -> Callable:
    """
    Factory function to check if user has all specified permissions.
    """

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        role_repo = UserRoleRepository()
        user_roles = await role_repo.get_user_roles(current_user.id)
        permissions = auth_service.get_user_permissions(user_roles)

        if current_user.is_superuser or Permission.ADMIN_ALL.value in permissions:
            return current_user

        if all(perm in permissions for perm in required_permissions):
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: all of {required_permissions} required",
        )

    return permission_checker


def require_resource_permission(
    resource_type: ResourceType,
    permission: ResourcePermission,
    resource_id_param: str = "resource_id",
) -> Callable:
    """
    Factory function that returns a dependency to check resource-level permissions.
    Extracts resource_id from path parameters or request body.
    """

    async def resource_permission_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # Try to get resource_id from path parameters
        resource_id = request.path_params.get(resource_id_param)

        # If not in path params, try to get from query params
        if not resource_id:
            resource_id = request.query_params.get(resource_id_param)

        # If still not found, try to get from request body (for POST/PUT requests)
        if not resource_id:
            try:
                body = await request.json()
                resource_id = body.get(resource_id_param)
            except Exception:
                pass

        if not resource_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resource ID not found in request (looking for '{resource_id_param}')",
            )

        # Get user roles
        role_repo = UserRoleRepository()
        user_roles = await role_repo.get_user_roles(current_user.id)

        # Check resource permission
        has_permission = await auth_service.check_resource_permission(
            user_id=current_user.id,
            resource_type=resource_type,
            resource_id=str(resource_id),
            required_permission=permission,
            roles=user_roles,
            is_superuser=current_user.is_superuser,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} access to {resource_type.value} '{resource_id}' required",
            )

        return current_user

    return resource_permission_checker


def require_database_access(
    permission: ResourcePermission = ResourcePermission.READ,
) -> Callable:
    """Specific dependency for database access."""
    return require_resource_permission(ResourceType.DATABASE, permission, "database_id")


def require_table_access(
    permission: ResourcePermission = ResourcePermission.READ,
) -> Callable:
    """Specific dependency for table access."""
    return require_resource_permission(ResourceType.TABLE, permission, "table_id")


async def get_user_permissions(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get all permissions for a user (role-based + resource-based).
    Returns a dictionary with permissions.
    """
    role_repo = UserRoleRepository()
    user_roles = await role_repo.get_user_roles(current_user.id)

    # Get role-based permissions
    role_permissions = auth_service.get_user_permissions(user_roles)

    # Get resource-based permissions
    resource_permissions = await auth_service.get_user_resource_permissions(
        current_user.id, user_roles
    )

    return {
        "role_permissions": role_permissions,
        "resource_permissions": resource_permissions,
    }


async def check_resource_access(
    user: User,
    resource_type: str,
    resource_id: str,
    permission: str,
) -> bool:
    """
    Check if user can access a resource.
    Helper function for manual permission checks.
    """
    try:
        res_type = ResourceType(resource_type)
        res_perm = ResourcePermission(permission)
    except ValueError:
        return False

    role_repo = UserRoleRepository()
    user_roles = await role_repo.get_user_roles(user.id)

    return await auth_service.check_resource_permission(
        user_id=user.id,
        resource_type=res_type,
        resource_id=resource_id,
        required_permission=res_perm,
        roles=user_roles,
        is_superuser=user.is_superuser,
    )
