"""
Permission management API routes for SamvadQL.
Admin endpoints for managing resource-level permissions (ABAC).

Resource ID Convention:
----------------------
Resource IDs follow a consistent format based on resource type:
- Database: "database_id" (e.g., "postgres_main")
- Table: "database_id:table_name" (e.g., "postgres_main:users")
- Column: "database_id:table_name:column_name" (e.g., "postgres_main:users:email")
- Query: UUID string (e.g., "123e4567-e89b-12d3-a456-426614174000")
- API: endpoint path (e.g., "/api/v1/query/submit")

Use the helper functions in `utils.resource_ids` for formatting and parsing:
- format_table_resource_id(database_id, table_name)
- parse_table_resource_id(resource_id)
- format_column_resource_id(database_id, table_name, column_name)
- parse_column_resource_id(resource_id)
- validate_resource_id(resource_id, expected_type)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from api.dependencies import get_current_superuser, get_current_active_user
from models.auth import (
    User,
    ResourceType,
    ResourcePermission,
    ResourcePermissionCreate,
    ResourcePermissionResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
)
from repositories.auth_repository import (
    ResourcePermissionRepository,
    RoleResourcePermissionRepository,
    PermissionHierarchyRepository,
    RoleRepository,
)
from services.auth_service import auth_service

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])

resource_perm_repo = ResourcePermissionRepository()
role_perm_repo = RoleResourcePermissionRepository()
hierarchy_repo = PermissionHierarchyRepository()
role_repo = RoleRepository()


# Request/Response Models

class GrantPermissionRequest(BaseModel):
    resource_type: ResourceType
    resource_id: str = Field(..., min_length=1, max_length=255)
    permission: ResourcePermission
    expires_at: Optional[datetime] = None


class RevokePermissionRequest(BaseModel):
    resource_type: ResourceType
    resource_id: str = Field(..., min_length=1, max_length=255)
    permission: ResourcePermission


class BulkGrantRequest(BaseModel):
    permissions: List[GrantPermissionRequest]


class BulkRevokeRequest(BaseModel):
    permissions: List[RevokePermissionRequest]


class HierarchyRequest(BaseModel):
    parent_resource_type: ResourceType
    parent_resource_id: str = Field(..., min_length=1, max_length=255)
    child_resource_type: ResourceType
    child_resource_id: str = Field(..., min_length=1, max_length=255)
    inherit_permissions: bool = True


class ResourcePermissionList(BaseModel):
    user_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    permissions: List[ResourcePermissionResponse]


# User Permission Endpoints

@router.post("/users/{user_id}/grant", status_code=status.HTTP_201_CREATED)
async def grant_user_permission(
    user_id: UUID,
    request: GrantPermissionRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Grant a resource permission to a user (admin only)."""
    try:
        permission = await resource_perm_repo.grant_permission(
            user_id=user_id,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            permission=request.permission,
            granted_by=current_user.id,
            expires_at=request.expires_at,
        )
        return {
            "success": True,
            "message": f"Permission '{request.permission.value}' granted to user {user_id} on {request.resource_type.value} '{request.resource_id}'",
            "permission": ResourcePermissionResponse(**permission.dict()),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant permission: {str(e)}",
        )


@router.delete("/users/{user_id}/revoke")
async def revoke_user_permission(
    user_id: UUID,
    request: RevokePermissionRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Revoke a resource permission from a user (admin only)."""
    success = await resource_perm_repo.revoke_permission(
        user_id=user_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        permission=request.permission,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found or already revoked",
        )

    return {
        "success": True,
        "message": f"Permission '{request.permission.value}' revoked from user {user_id} on {request.resource_type.value} '{request.resource_id}'",
    }


@router.get("/users/{user_id}", response_model=ResourcePermissionList)
async def get_user_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
):
    """Get all resource permissions for a user (admin only)."""
    permissions = await resource_perm_repo.get_all_user_permissions(user_id)

    return {
        "user_id": user_id,
        "permissions": [ResourcePermissionResponse(**p.dict()) for p in permissions],
    }


@router.post("/users/{user_id}/check", response_model=PermissionCheckResponse)
async def check_user_permission(
    user_id: UUID,
    request: PermissionCheckRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Check if a user has a specific permission."""
    # Users can check their own permissions, admins can check any user
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check your own permissions",
        )

    # Get user roles
    user_roles = await role_repo.get_user_roles(user_id)

    # Check permission
    has_permission = await auth_service.check_resource_permission(
        user_id=user_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        required_permission=request.permission,
        roles=user_roles,
        is_superuser=current_user.is_superuser if user_id == current_user.id else False,
    )

    # Determine how permission was granted
    granted_through = None
    reason = None

    if has_permission:
        # Check if direct permission
        direct = await resource_perm_repo.check_permission(
            user_id, request.resource_type, request.resource_id, request.permission
        )
        if direct:
            granted_through = "direct"
            reason = "User has direct permission grant"
        else:
            # Check roles
            for role in user_roles:
                role_perms = await role_perm_repo.get_role_resource_permissions(role.id)
                if any(
                    p.resource_type == request.resource_type
                    and p.resource_id == request.resource_id
                    and p.permission == request.permission
                    for p in role_perms
                ):
                    granted_through = "role"
                    reason = f"Permission inherited from role '{role.name}'"
                    break

            if not granted_through:
                granted_through = "inherited"
                reason = "Permission inherited from parent resource"
    else:
        reason = "Permission not granted"

    return PermissionCheckResponse(
        has_permission=has_permission,
        permission=request.permission,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        reason=reason,
        granted_through=granted_through,
    )


# Role Permission Endpoints

@router.post("/roles/{role_id}/grant", status_code=status.HTTP_201_CREATED)
async def grant_role_permission(
    role_id: UUID,
    request: GrantPermissionRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Grant a resource permission to a role (admin only)."""
    try:
        permission = await role_perm_repo.grant_role_permission(
            role_id=role_id,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            permission=request.permission,
            granted_by=current_user.id,
        )
        return {
            "success": True,
            "message": f"Permission '{request.permission.value}' granted to role {role_id} on {request.resource_type.value} '{request.resource_id}'",
            "permission": permission,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant permission: {str(e)}",
        )


@router.delete("/roles/{role_id}/revoke")
async def revoke_role_permission(
    role_id: UUID,
    request: RevokePermissionRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Revoke a resource permission from a role (admin only)."""
    success = await role_perm_repo.revoke_role_permission(
        role_id=role_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        permission=request.permission,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found or already revoked",
        )

    return {
        "success": True,
        "message": f"Permission '{request.permission.value}' revoked from role {role_id}",
    }


@router.get("/roles/{role_id}")
async def get_role_permissions(
    role_id: UUID,
    current_user: User = Depends(get_current_superuser),
):
    """Get all resource permissions for a role (admin only)."""
    permissions = await role_perm_repo.get_role_resource_permissions(role_id)

    return {
        "role_id": role_id,
        "permissions": permissions,
    }


# Resource Permission Endpoints

@router.get("/resources/{resource_type}/{resource_id}")
async def get_resource_permissions(
    resource_type: ResourceType,
    resource_id: str,
    current_user: User = Depends(get_current_superuser),
):
    """List all users/roles with permissions on a specific resource (admin only)."""
    # Get all users with permissions on this resource
    users_with_perms = {}
    for perm in ResourcePermission:
        user_ids = await resource_perm_repo.list_users_with_permission(
            resource_type, resource_id, perm
        )
        if user_ids:
            users_with_perms[perm.value] = user_ids

    # Get all roles with permissions on this resource
    roles_with_perms = {}
    for perm in ResourcePermission:
        role_ids = await role_perm_repo.list_roles_with_permission(
            resource_type, resource_id, perm
        )
        if role_ids:
            roles_with_perms[perm.value] = role_ids

    return {
        "resource_type": resource_type.value,
        "resource_id": resource_id,
        "user_permissions": users_with_perms,
        "role_permissions": roles_with_perms,
    }


# Permission Hierarchy Endpoints

@router.post("/hierarchy", status_code=status.HTTP_201_CREATED)
async def create_permission_hierarchy(
    request: HierarchyRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Create a parent-child resource relationship for permission inheritance (admin only)."""
    try:
        hierarchy = await hierarchy_repo.create_hierarchy(
            parent_type=request.parent_resource_type,
            parent_id=request.parent_resource_id,
            child_type=request.child_resource_type,
            child_id=request.child_resource_id,
            inherit=request.inherit_permissions,
        )
        return {
            "success": True,
            "message": "Permission hierarchy created",
            "hierarchy": hierarchy,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create hierarchy: {str(e)}",
        )


@router.get("/hierarchy/{resource_type}/{resource_id}")
async def get_permission_hierarchy(
    resource_type: ResourceType,
    resource_id: str,
    current_user: User = Depends(get_current_superuser),
):
    """Get permission hierarchy for a resource (admin only)."""
    children = await hierarchy_repo.get_children(resource_type, resource_id)

    return {
        "resource_type": resource_type.value,
        "resource_id": resource_id,
        "children": children,
    }


# Bulk Operations

@router.post("/bulk-grant", status_code=status.HTTP_201_CREATED)
async def bulk_grant_permissions(
    user_id: UUID,
    request: BulkGrantRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Grant multiple permissions at once (admin only)."""
    results = []
    errors = []

    for perm_request in request.permissions:
        try:
            permission = await resource_perm_repo.grant_permission(
                user_id=user_id,
                resource_type=perm_request.resource_type,
                resource_id=perm_request.resource_id,
                permission=perm_request.permission,
                granted_by=current_user.id,
                expires_at=perm_request.expires_at,
            )
            results.append(ResourcePermissionResponse(**permission.dict()))
        except Exception as e:
            errors.append({
                "resource_type": perm_request.resource_type.value,
                "resource_id": perm_request.resource_id,
                "permission": perm_request.permission.value,
                "error": str(e),
            })

    return {
        "success": len(errors) == 0,
        "granted": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


@router.post("/bulk-revoke")
async def bulk_revoke_permissions(
    user_id: UUID,
    request: BulkRevokeRequest,
    current_user: User = Depends(get_current_superuser),
):
    """Revoke multiple permissions at once (admin only)."""
    results = []
    errors = []

    for perm_request in request.permissions:
        try:
            success = await resource_perm_repo.revoke_permission(
                user_id=user_id,
                resource_type=perm_request.resource_type,
                resource_id=perm_request.resource_id,
                permission=perm_request.permission,
            )
            if success:
                results.append({
                    "resource_type": perm_request.resource_type.value,
                    "resource_id": perm_request.resource_id,
                    "permission": perm_request.permission.value,
                })
            else:
                errors.append({
                    "resource_type": perm_request.resource_type.value,
                    "resource_id": perm_request.resource_id,
                    "permission": perm_request.permission.value,
                    "error": "Permission not found",
                })
        except Exception as e:
            errors.append({
                "resource_type": perm_request.resource_type.value,
                "resource_id": perm_request.resource_id,
                "permission": perm_request.permission.value,
                "error": str(e),
            })

    return {
        "success": len(errors) == 0,
        "revoked": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
