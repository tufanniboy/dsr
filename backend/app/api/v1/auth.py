"""
Authentication endpoints — login, signup, session management.
Uses Supabase Auth for actual authentication.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse
from app.core.supabase import get_supabase_client
from app.core.security import get_current_user, CurrentUser
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Authenticate user with email and password."""
    try:
        from supabase import create_client
        from app.core.config import get_settings
        
        settings = get_settings()
        # Use anon key to create a fresh client so we don't mutate the global service client
        auth_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Sign in with Supabase Auth
        auth_response = auth_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        supabase = get_supabase_client()

        # Get user profile
        user_data = supabase.table("users").select("*").eq(
            "id", str(auth_response.user.id)
        ).single().execute()

        if not user_data.data:
            raise HTTPException(status_code=404, detail="User profile not found")

        if not user_data.data.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is deactivated")

        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user=UserResponse(**user_data.data)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/signup", response_model=UserResponse)
def signup(request: UserCreate):
    """Register a new user (admin only in production)."""
    try:
        supabase = get_supabase_client()

        # Create auth user
        auth_response = supabase.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,
        })

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Failed to create user")

        # Create user profile
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


@router.get("/me", response_model=UserResponse)
def get_profile(user: CurrentUser = Depends(get_current_user)):
    """Get current user profile."""
    supabase = get_supabase_client()
    result = supabase.table("users").select("*").eq("id", user.id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserResponse(**result.data)


@router.post("/logout")
def logout(user: CurrentUser = Depends(get_current_user)):
    """Logout current user."""
    return {"message": "Logged out successfully"}


@router.post("/refresh")
def refresh_token(refresh_token: str):
    """Refresh an expired access token."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.refresh_session(refresh_token)
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
