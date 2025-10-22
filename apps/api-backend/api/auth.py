"""Authentication API routes for SamvadQL."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import text

from services.auth_service import auth_service
from repositories.auth_repository import (
    UserRepository,
    UserRoleRepository,
    RoleRepository,
)
from models.auth import UserCreate, LoginRequest, UserResponse, Token
from core.db.connection import get_db_session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

user_repo = UserRepository()
role_repo = RoleRepository()
user_role_repo = UserRoleRepository()


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    resource_permissions: Optional[dict] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """Create a new user account."""
    existing = await user_repo.get_user_by_username(request.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    existing_email = await user_repo.get_user_by_email(request.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = auth_service.get_password_hash(request.password)
    user = await user_repo.create_user(
        UserCreate(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        ),
        hashed_password=hashed,
    )

    role = await role_repo.get_role_by_name("viewer")
    if role:
        await user_role_repo.assign_role_to_user(user.id, role.id)
        roles = [role]
    else:
        roles = []

    permissions = auth_service.get_user_permissions(roles)
    resource_permissions = await auth_service.get_user_resource_permissions(user.id, roles)

    tokens: Token = auth_service.create_tokens(user, permissions, resource_permissions)
    response_user = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        roles=[r.name for r in roles],
        permissions=permissions,
        resource_permissions=resource_permissions,
    )
    return AuthResponse(
        user=response_user,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
        expires_in=tokens.expires_in,
        resource_permissions=resource_permissions,
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Authenticate user and return tokens."""
    user = await user_repo.get_user_by_username(request.username)
    if not user and "@" in request.username:
        user = await user_repo.get_user_by_email(request.username)
    if not user or not auth_service.verify_password(
        request.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    await user_repo.update_last_login(user.id)
    roles = await user_role_repo.get_user_roles(user.id)
    permissions = auth_service.get_user_permissions(roles)
    resource_permissions = await auth_service.get_user_resource_permissions(user.id, roles)

    tokens = auth_service.create_tokens(user, permissions, resource_permissions)
    response_user = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        roles=[r.name for r in roles],
        permissions=permissions,
        resource_permissions=resource_permissions,
    )
    return AuthResponse(
        user=response_user,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
        expires_in=tokens.expires_in,
        resource_permissions=resource_permissions,
    )


@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest):
    """Initiate password reset by generating a reset token (dev mode returns token)."""
    user = await user_repo.get_user_by_email(request.email)
    if not user:
        return {"message": "If the email exists, a reset link has been sent."}

    token_plain = auth_service.create_api_token(32)
    token_hash = auth_service.hash_api_token(token_plain)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    async with get_db_session() as session:
        await session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash VARCHAR(255) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        )
        await session.execute(
            text(
                """
                INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
                VALUES (:user_id, :token_hash, :expires_at)
                """
            ),
            {"user_id": user.id, "token_hash": token_hash, "expires_at": expires_at},
        )
        await session.commit()

    return {"message": "Password reset initiated", "reset_token": token_plain}


@router.post("/reset-password", response_model=dict)
async def reset_password(request: ResetPasswordRequest):
    """Complete password reset using token."""
    async with get_db_session() as session:
        result = await session.execute(
            text(
                """
                SELECT id, user_id, token_hash, expires_at, used_at FROM password_reset_tokens
                WHERE used_at IS NULL AND expires_at > NOW()
                ORDER BY created_at DESC
                """
            )
        )
        rows = result.fetchall()
        matched_row = None
        for row in rows:
            if auth_service.verify_api_token(request.token, row.token_hash):
                matched_row = row
                break
        if not matched_row:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        new_hash = auth_service.get_password_hash(request.new_password)
        await session.execute(
            text(
                """
                UPDATE users SET hashed_password = :hp, updated_at = NOW() WHERE id = :uid
                """
            ),
            {"hp": new_hash, "uid": matched_row.user_id},
        )
        await session.execute(
            text(
                """
                UPDATE password_reset_tokens SET used_at = NOW() WHERE id = :id
                """
            ),
            {"id": matched_row.id},
        )
        await session.commit()

    return {"message": "Password reset successful"}
