"""Auth API routes — register, login, refresh, profile, invite."""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import (
    InviteRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    UserProfile,
)
from src.auth.dependencies import get_current_user, require_role
from src.auth.jwt import create_access_token, create_refresh_token, decode_token
from src.auth.password import hash_password, verify_password
from src.config.database import get_db
from src.core.audit import log_action
from src.db.models.tenant import Tenant
from src.db.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _slugify(name: str) -> str:
    """Convert company name to URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug[:100] or "tenant"


def _build_profile(user: User, tenant_name: str = "", plan: str = "free") -> UserProfile:
    return UserProfile(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=str(user.tenant_id),
        tenant_name=tenant_name,
        departments=user.departments or [],
        access_levels=user.access_levels or [],
        plan=plan,
    )


def _build_token_data(user: User) -> dict:
    return {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role,
    }


# --------------------------------------------------------------------------
# POST /api/auth/register
# --------------------------------------------------------------------------

@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new tenant with the first admin user."""
    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email da duoc su dung",
        )

    # Create tenant
    slug = _slugify(req.company_name)
    # Ensure slug uniqueness
    slug_check = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if slug_check.scalar_one_or_none():
        slug = f"{slug}-{str(hash(req.email))[-4:]}"

    tenant = Tenant(name=req.company_name, slug=slug)
    db.add(tenant)
    await db.flush()

    # Create admin user
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role="admin",
        departments=[],
        access_levels=["public", "internal", "confidential"],
    )
    db.add(user)
    await db.flush()

    await log_action(
        db, tenant_id=tenant.id, user_id=user.id,
        action="create", resource_type="user", resource_id=user.id,
    )

    access_token = create_access_token(_build_token_data(user))
    refresh_token = create_refresh_token(str(user.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_build_profile(user, tenant.name, tenant.plan),
    )


# --------------------------------------------------------------------------
# POST /api/auth/login
# --------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate with email and password."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoac mat khau khong dung",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tai khoan da bi vo hieu hoa",
        )

    # Get tenant name
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        action="login", resource_type="user", resource_id=user.id,
    )

    access_token = create_access_token(_build_token_data(user))
    refresh_token = create_refresh_token(str(user.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_build_profile(user, tenant.name if tenant else "", tenant.plan if tenant else "free"),
    )


# --------------------------------------------------------------------------
# POST /api/auth/refresh
# --------------------------------------------------------------------------

@router.post("/refresh")
async def refresh(
    req: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange a refresh token for a new access token."""
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token khong hop le")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token het han hoac khong hop le")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Nguoi dung khong ton tai")

    new_access = create_access_token(_build_token_data(user))
    return {"access_token": new_access, "token_type": "bearer"}


# --------------------------------------------------------------------------
# GET /api/auth/me
# --------------------------------------------------------------------------

@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return the current user's profile."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return _build_profile(current_user, tenant.name if tenant else "", tenant.plan if tenant else "free")


# --------------------------------------------------------------------------
# POST /api/auth/invite
# --------------------------------------------------------------------------

@router.post("/invite", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def invite_user(
    req: InviteRequest,
    admin: Annotated[User, Depends(require_role(["admin"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin-only: create a new user within the same tenant."""
    # Check duplicate
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email da duoc su dung")

    # Generate a temporary password (user should change it)
    import secrets
    temp_password = secrets.token_urlsafe(12)

    user = User(
        tenant_id=admin.tenant_id,
        email=req.email,
        hashed_password=hash_password(temp_password),
        full_name=req.full_name,
        role=req.role,
        departments=req.departments,
        access_levels=["public"],
    )
    db.add(user)
    await db.flush()

    await log_action(
        db, tenant_id=admin.tenant_id, user_id=admin.id,
        action="create", resource_type="user", resource_id=user.id,
        details={"invited_email": req.email, "role": req.role},
    )

    # Get tenant name for profile
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == admin.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    return _build_profile(user, tenant.name if tenant else "", tenant.plan if tenant else "free")
