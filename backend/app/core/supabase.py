"""
Supabase client singleton for backend operations.
Uses service role key for full database access.
"""

from functools import lru_cache
import re
from supabase import create_client, Client
import supabase._sync.client

# Monkey-patch strict JWT validation in supabase-py 2.31.0
original_match = supabase._sync.client.re.match

def custom_match(pattern, string, flags=0):
    if pattern == r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$":
        return True
    return original_match(pattern, string, flags)

supabase._sync.client.re.match = custom_match

from app.core.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Get Supabase client with service role key (full access)."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


@lru_cache()
def get_supabase_anon_client() -> Client:
    """Get Supabase client with anon key (RLS enforced)."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class SupabaseStorage:
    """Helper for Supabase Storage operations."""

    BUCKET_NAME = "dsr-images"

    def __init__(self):
        self.client = get_supabase_client()

    def upload_image(self, file_path: str, file_bytes: bytes, content_type: str = "image/jpeg") -> str:
        """Upload an image to Supabase Storage and return the public URL."""
        self.client.storage.from_(self.BUCKET_NAME).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )
        return self.get_public_url(file_path)

    def get_public_url(self, file_path: str) -> str:
        """Get the public URL for a stored file."""
        return self.client.storage.from_(self.BUCKET_NAME).get_public_url(file_path)

    def download_image(self, file_path: str) -> bytes:
        """Download an image from storage."""
        return self.client.storage.from_(self.BUCKET_NAME).download(file_path)

    def delete_image(self, file_path: str) -> None:
        """Delete an image from storage."""
        self.client.storage.from_(self.BUCKET_NAME).remove([file_path])


def get_storage() -> SupabaseStorage:
    """Get storage helper instance."""
    return SupabaseStorage()
