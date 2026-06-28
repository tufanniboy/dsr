"""
Notification endpoints.
"""

from fastapi import APIRouter, Depends

from app.core.security import get_current_user, CurrentUser
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("")
async def get_notifications(
    page: int = 1,
    per_page: int = 20,
    user: CurrentUser = Depends(get_current_user)
):
    """Get user notifications."""
    service = NotificationService()
    return service.get_all(user.id, page, per_page)


@router.get("/unread")
async def get_unread(user: CurrentUser = Depends(get_current_user)):
    """Get unread notification count and recent items."""
    service = NotificationService()
    unread = service.get_unread(user.id, limit=10)
    return {"count": len(unread), "notifications": unread}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    user: CurrentUser = Depends(get_current_user)
):
    """Mark a notification as read."""
    service = NotificationService()
    service.mark_read(notification_id, user.id)
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_read(user: CurrentUser = Depends(get_current_user)):
    """Mark all notifications as read."""
    service = NotificationService()
    service.mark_all_read(user.id)
    return {"message": "All notifications marked as read"}
