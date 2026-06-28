"""
API dependency injection helpers.
"""

from fastapi import Depends
from app.core.security import get_current_user, require_role, CurrentUser
from app.core.supabase import get_supabase_client, get_storage


async def get_db():
    """Get Supabase database client."""
    return get_supabase_client()


async def get_file_storage():
    """Get Supabase storage client."""
    return get_storage()
