"""
Notification service — creates and manages user notifications.
"""

from typing import Optional, List
import uuid
import logging

from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class NotificationService:
    """Manages notification creation, retrieval, and status updates."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def create(self, user_id: str, type: str, title: str, message: str,
               data: Optional[dict] = None) -> dict:
        """Create a new notification."""
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": type,
            "title": title,
            "message": message,
            "data": data,
        }
        result = self.supabase.table("notifications").insert(record).execute()
        return result.data[0] if result.data else record

    def get_unread(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get unread notifications for a user."""
        result = self.supabase.table("notifications").select("*").eq(
            "user_id", user_id
        ).eq("is_read", False).order("created_at", desc=True).limit(limit).execute()
        return result.data or []

    def get_all(self, user_id: str, page: int = 1, per_page: int = 20) -> dict:
        """Get all notifications with pagination."""
        offset = (page - 1) * per_page
        result = self.supabase.table("notifications").select(
            "*", count="exact"
        ).eq("user_id", user_id).order(
            "created_at", desc=True
        ).range(offset, offset + per_page - 1).execute()

        return {
            "data": result.data or [],
            "total": result.count or 0,
            "unread": len([n for n in (result.data or []) if not n.get("is_read")]),
        }

    def mark_read(self, notification_id: str, user_id: str) -> None:
        """Mark a notification as read."""
        self.supabase.table("notifications").update({
            "is_read": True,
            "read_at": "now()"
        }).eq("id", notification_id).eq("user_id", user_id).execute()

    def mark_all_read(self, user_id: str) -> None:
        """Mark all notifications as read for a user."""
        self.supabase.table("notifications").update({
            "is_read": True,
            "read_at": "now()"
        }).eq("user_id", user_id).eq("is_read", False).execute()

    def notify_pending_approval(self, report_id: str, manager_ids: List[str],
                                 report_date: str, uploaded_by_name: str) -> None:
        """Notify managers of a pending DSR approval."""
        for manager_id in manager_ids:
            self.create(
                user_id=manager_id,
                type="pending_approval",
                title="New DSR Pending Approval",
                message=f"DSR for {report_date} uploaded by {uploaded_by_name} is ready for review.",
                data={"report_id": report_id}
            )

    def notify_approval_complete(self, user_id: str, report_date: str, approved_by: str) -> None:
        """Notify the uploader that their DSR was approved."""
        self.create(
            user_id=user_id,
            type="approval_complete",
            title="DSR Approved",
            message=f"Your DSR for {report_date} has been approved by {approved_by}.",
        )

    def notify_ocr_failure(self, user_id: str, report_id: str, error: str) -> None:
        """Notify user of OCR processing failure."""
        self.create(
            user_id=user_id,
            type="ocr_failure",
            title="OCR Processing Failed",
            message=f"Failed to process DSR image. Error: {error}",
            data={"report_id": report_id}
        )
