"""
Template management service.
Handles CRUD for DSR template definitions and coordinate mappings.
"""

from typing import Dict, List, Optional
import uuid
import json
import logging

from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class TemplateService:
    """Manages DSR template definitions."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def create_template(self, name: str, coordinates: dict, pump_id: Optional[str] = None,
                        version: str = "v1", description: str = "", created_by: str = "",
                        is_default: bool = False) -> dict:
        """Create a new template."""
        record = {
            "id": str(uuid.uuid4()),
            "name": name,
            "version": version,
            "description": description,
            "pump_id": pump_id,
            "coordinates": coordinates,
            "is_default": is_default,
            "created_by": created_by,
        }
        result = self.supabase.table("templates").insert(record).execute()
        return result.data[0] if result.data else record

    def get_template(self, template_id: str) -> Optional[dict]:
        """Get a template by ID."""
        result = self.supabase.table("templates").select("*").eq(
            "id", template_id
        ).single().execute()
        return result.data

    def get_default_template(self, pump_id: Optional[str] = None) -> Optional[dict]:
        """Get the default template, optionally for a specific pump."""
        query = self.supabase.table("templates").select("*").eq(
            "is_default", True
        ).eq("is_active", True)

        if pump_id:
            query = query.eq("pump_id", pump_id)

        result = query.limit(1).execute()

        if result.data:
            return result.data[0]

        # Fallback: get any default template
        result = self.supabase.table("templates").select("*").eq(
            "is_default", True
        ).eq("is_active", True).limit(1).execute()

        return result.data[0] if result.data else None

    def list_templates(self, pump_id: Optional[str] = None) -> List[dict]:
        """List all active templates."""
        query = self.supabase.table("templates").select("*").eq(
            "is_active", True
        ).order("created_at", desc=True)

        if pump_id:
            query = query.eq("pump_id", pump_id)

        result = query.execute()
        return result.data or []

    def update_template(self, template_id: str, updates: dict) -> dict:
        """Update a template's properties or coordinates."""
        result = self.supabase.table("templates").update(
            updates
        ).eq("id", template_id).execute()
        return result.data[0] if result.data else {}

    def delete_template(self, template_id: str) -> None:
        """Soft-delete a template."""
        self.supabase.table("templates").update(
            {"is_active": False}
        ).eq("id", template_id).execute()
