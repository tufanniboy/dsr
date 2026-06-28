"""
Template management endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.core.security import require_role, CurrentUser
from app.models.schemas import TemplateCreate, TemplateUpdate
from app.services.template_service import TemplateService

router = APIRouter()


@router.get("")
async def list_templates(
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("manager", "super_admin"))
):
    """List all templates."""
    service = TemplateService()
    return service.list_templates(pump_id)


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    user: CurrentUser = Depends(require_role("manager", "super_admin"))
):
    """Get a specific template."""
    service = TemplateService()
    result = service.get_template(template_id)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.post("")
async def create_template(
    request: TemplateCreate,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """Create a new template."""
    service = TemplateService()
    return service.create_template(
        name=request.name,
        coordinates=request.coordinates,
        pump_id=request.pump_id,
        version=request.version,
        description=request.description or "",
        created_by=user.id,
        is_default=request.is_default,
    )


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    updates: TemplateUpdate,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """Update a template."""
    service = TemplateService()
    return service.update_template(template_id, updates.model_dump(exclude_none=True))


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    user: CurrentUser = Depends(require_role("super_admin"))
):
    """Delete a template."""
    service = TemplateService()
    service.delete_template(template_id)
    return {"message": "Template deleted"}
