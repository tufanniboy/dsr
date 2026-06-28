"""
Security module — JWT verification and role-based access control.
Verifies Supabase Auth JWT tokens and extracts user info.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, List
from functools import wraps
import httpx

from app.core.config import get_settings
from app.core.supabase import get_supabase_client

security_scheme = HTTPBearer()


class CurrentUser:
    """Represents the authenticated user."""

    def __init__(self, id: str, email: str, role: str, pump_id: Optional[str] = None, full_name: str = ""):
        self.id = id
        self.email = email
        self.role = role
        self.pump_id = pump_id
        self.full_name = full_name

    @property
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    @property
    def is_manager(self) -> bool:
        return self.role in ("manager", "super_admin")

    @property
    def is_staff(self) -> bool:
        return self.role in ("staff", "manager", "super_admin")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> CurrentUser:
    """
    Verify the JWT token from Supabase Auth and return the current user.
    """
    token = credentials.credentials
    settings = get_settings()

    try:
        # Decode JWT using Supabase JWT secret
        # Supabase uses the SUPABASE_URL/auth/v1 JWKS endpoint
        # For simplicity, we verify against Supabase by fetching user
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        auth_user = user_response.user

        # Fetch extended user profile from our users table
        result = supabase.table("users").select("*").eq("id", str(auth_user.id)).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="User profile not found")

        user_data = result.data

        if not user_data.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account has been deactivated")

        return CurrentUser(
            id=user_data["id"],
            email=user_data["email"],
            role=user_data["role"],
            pump_id=user_data.get("pump_id"),
            full_name=user_data.get("full_name", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def require_role(*allowed_roles: str):
    """
    Dependency that checks if the current user has one of the allowed roles.

    Usage:
        @router.get("/admin-only")
        async def admin_route(user: CurrentUser = Depends(require_role("super_admin"))):
            ...
    """
    async def role_checker(
        user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}"
            )
        return user

    return role_checker


def require_super_admin():
    """Shortcut for requiring super_admin role."""
    return require_role("super_admin")


def require_manager():
    """Shortcut for requiring manager or super_admin role."""
    return require_role("manager", "super_admin")


def require_staff():
    """Shortcut for requiring any authenticated role."""
    return require_role("staff", "manager", "super_admin")
