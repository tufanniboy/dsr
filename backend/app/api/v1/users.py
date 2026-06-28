"""
User management endpoints (admin only).
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from app.core.security import require_role, CurrentUser
from app.core.supabase import get_supabase_client
from app.models.schemas import UserCreate, UserUpdate, UserResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def list_users(
    pump_id: Optional[str] = None,
    role: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """List all users (admin only)."""
    supabase = get_supabase_client()
    query = supabase.table("users").select("*", count="exact").is_(
        "deleted_at", "null"
    ).order("created_at", desc=True)

    if pump_id:
        query = query.eq("pump_id", pump_id)
    if role:
        query = query.eq("role", role)

    offset = (page - 1) * per_page
    result = query.range(offset, offset + per_page - 1).execute()

    return {
        "data": result.data or [],
        "total": result.count or 0,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """Get a specific user."""
    supabase = get_supabase_client()
    result = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data


@router.post("", response_model=UserResponse)
async def create_user(
    request: UserCreate,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """Create a new user (admin only)."""
    try:
        supabase = get_supabase_client()

        auth_response = supabase.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,
        })

        user_record = {
            "id": str(auth_response.user.id),
            "email": request.email,
            "full_name": request.full_name,
            "role": request.role.value,
            "phone": request.phone,
            "pump_id": request.pump_id,
        }

        result = supabase.table("users").insert(user_record).execute()
        return UserResponse(**result.data[0])

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    updates: UserUpdate,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """Update a user."""
    supabase = get_supabase_client()
    update_data = updates.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    result = supabase.table("users").update(update_data).eq("id", user_id).execute()
    return result.data[0] if result.data else {"message": "Updated"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """Soft-delete a user."""
    supabase = get_supabase_client()
    supabase.table("users").update({"deleted_at": "now()", "is_active": False}).eq("id", user_id).execute()
    return {"message": "User deleted"}
