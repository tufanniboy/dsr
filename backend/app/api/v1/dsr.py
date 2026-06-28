"""
DSR report endpoints — upload, review, approve, reject.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from typing import Optional
import uuid
import logging

from app.core.security import get_current_user, require_role, CurrentUser
from app.core.supabase import get_supabase_client, get_storage
from app.core.config import get_settings
from app.models.schemas import DSRReportUpdate, DSRApproveRequest, DSRRejectRequest
from app.services.ocr_service import OCRService
from app.services.notification_service import NotificationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_dsr(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pump_id: str = Form(...),
    template_id: Optional[str] = Form(None),
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Upload a DSR image and start OCR processing."""
    settings = get_settings()

    # Validate file
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    # Read file
    image_bytes = await file.read()

    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Create report record
    supabase = get_supabase_client()
    report_id = str(uuid.uuid4())

    # Upload original image
    storage = get_storage()
    original_path = f"{pump_id}/{report_id}/original.jpg"
    try:
        original_url = storage.upload_image(original_path, image_bytes, file.content_type)
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        original_url = ""

    # Create DSR report
    report = {
        "id": report_id,
        "pump_id": pump_id,
        "status": "processing",
        "original_image_url": original_url,
        "uploaded_by": user.id,
        "report_date": "1970-01-01",  # Will be updated after OCR
    }
    supabase.table("dsr_reports").insert(report).execute()

    # Process OCR in background
    async def run_ocr():
        try:
            ocr_service = OCRService()
            result = await ocr_service.process_dsr_image(
                image_bytes=image_bytes,
                report_id=report_id,
                pump_id=pump_id,
                template_id=template_id or "dsr_default"
            )

            # Store entries
            entries = result.get("entries", [])
            if entries:
                for entry in entries:
                    entry["id"] = str(uuid.uuid4())
                    entry["report_id"] = report_id
                supabase.table("dsr_entries").insert(entries).execute()

            # Update report with parsed date and totals
            report_data = result.get("report_data", {})
            total_sales = sum(float(e.get("total_amount", 0) or 0) for e in entries)
            total_cash = sum(float(e.get("total_cash_in_hand", 0) or 0) for e in entries)
            total_upi = sum(float(e.get("upi", 0) or 0) for e in entries)
            total_card = sum(float(e.get("card", 0) or 0) for e in entries)
            total_credit = sum(float(e.get("credit", 0) or 0) for e in entries)
            total_expenses = sum(float(e.get("expenses", 0) or 0) for e in entries)

            update_data = {
                "manager_name": report_data.get("manager_name", ""),
                "total_sales": total_sales,
                "total_cash": total_cash,
                "total_upi": total_upi,
                "total_card": total_card,
                "total_credit": total_credit,
                "total_expenses": total_expenses,
                "status": "pending_review",
            }

            # Parse and set date
            date_str = report_data.get("report_date", "")
            if date_str:
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
                    try:
                        from datetime import datetime
                        parsed = datetime.strptime(date_str, fmt)
                        update_data["report_date"] = parsed.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue

            supabase.table("dsr_reports").update(update_data).eq("id", report_id).execute()

            # Notify managers
            try:
                notif = NotificationService()
                managers = supabase.table("users").select("id").eq(
                    "pump_id", pump_id
                ).in_("role", ["manager", "super_admin"]).execute()
                manager_ids = [m["id"] for m in (managers.data or [])]
                if manager_ids:
                    notif.notify_pending_approval(
                        report_id, manager_ids,
                        update_data.get("report_date", ""),
                        user.full_name
                    )
            except Exception as e:
                logger.warning(f"Failed to send notifications: {e}")

        except Exception as e:
            logger.error(f"OCR processing failed for report {report_id}: {e}", exc_info=True)
            supabase.table("dsr_reports").update({
                "status": "draft"
            }).eq("id", report_id).execute()

            # Notify user of failure
            try:
                notif = NotificationService()
                notif.notify_ocr_failure(user.id, report_id, str(e))
            except Exception:
                pass

    background_tasks.add_task(run_ocr)

    return {
        "report_id": report_id,
        "status": "processing",
        "message": "DSR image uploaded. OCR processing started."
    }


@router.get("")
async def list_reports(
    pump_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    manager: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """List DSR reports with filters and pagination."""
    from app.services.report_service import ReportService
    service = ReportService()

    # Staff can only see their own reports
    if user.role == "staff":
        supabase = get_supabase_client()
        result = supabase.table("dsr_reports").select(
            "*", count="exact"
        ).eq("uploaded_by", user.id).is_("deleted_at", "null").order(
            "report_date", desc=True
        ).range((page - 1) * per_page, page * per_page - 1).execute()

        return {
            "data": result.data or [],
            "total": result.count or 0,
            "page": page,
            "per_page": per_page,
        }

    # Managers/admins see pump reports
    effective_pump_id = pump_id or user.pump_id
    return service.get_reports(
        pump_id=effective_pump_id if not user.is_super_admin else pump_id,
        start_date=start_date,
        end_date=end_date,
        manager=manager,
        status=status,
        page=page,
        per_page=per_page,
    )


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get a DSR report with all entries and OCR data."""
    from app.services.report_service import ReportService
    service = ReportService()

    result = service.get_report_detail(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    # Staff can only view own reports
    if user.role == "staff" and result["report"].get("uploaded_by") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return result


@router.put("/{report_id}")
async def update_report(
    report_id: str,
    updates: DSRReportUpdate,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Update DSR report fields (during review)."""
    supabase = get_supabase_client()

    # Update report metadata
    report_updates = {}
    if updates.manager_name is not None:
        report_updates["manager_name"] = updates.manager_name
    if updates.report_date is not None:
        report_updates["report_date"] = updates.report_date
    if updates.notes is not None:
        report_updates["notes"] = updates.notes

    if report_updates:
        supabase.table("dsr_reports").update(report_updates).eq("id", report_id).execute()

    # Update entries
    if updates.entries:
        for entry in updates.entries:
            entry_data = entry.model_dump(exclude_none=True)
            duty_num = entry_data.pop("duty_number")

            supabase.table("dsr_entries").update(entry_data).eq(
                "report_id", report_id
            ).eq("duty_number", duty_num).execute()

        # Recalculate totals
        entries_result = supabase.table("dsr_entries").select("*").eq(
            "report_id", report_id
        ).execute()
        entries = entries_result.data or []

        supabase.table("dsr_reports").update({
            "total_sales": sum(float(e.get("total_amount", 0) or 0) for e in entries),
            "total_cash": sum(float(e.get("total_cash_in_hand", 0) or 0) for e in entries),
            "total_upi": sum(float(e.get("upi", 0) or 0) for e in entries),
            "total_card": sum(float(e.get("card", 0) or 0) for e in entries),
            "total_credit": sum(float(e.get("credit", 0) or 0) for e in entries),
            "total_expenses": sum(float(e.get("expenses", 0) or 0) for e in entries),
        }).eq("id", report_id).execute()

    # Audit log
    supabase.table("audit_logs").insert({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "action": "update",
        "entity_type": "dsr_report",
        "entity_id": report_id,
        "new_values": updates.model_dump(exclude_none=True),
    }).execute()

    return {"message": "Report updated successfully"}


@router.post("/{report_id}/approve")
async def approve_report(
    report_id: str,
    request: DSRApproveRequest,
    user: CurrentUser = Depends(require_role("manager", "super_admin"))
):
    """Approve a DSR report."""
    supabase = get_supabase_client()

    # Verify report exists and is pending
    report = supabase.table("dsr_reports").select("*").eq("id", report_id).single().execute()
    if not report.data:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.data["status"] != "pending_review":
        raise HTTPException(status_code=400, detail="Report is not pending review")

    supabase.table("dsr_reports").update({
        "status": "approved",
        "reviewed_by": user.id,
        "approved_at": "now()",
        "notes": request.notes,
    }).eq("id", report_id).execute()

    # Audit log
    supabase.table("audit_logs").insert({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "action": "approve",
        "entity_type": "dsr_report",
        "entity_id": report_id,
    }).execute()

    # Notify uploader
    try:
        notif = NotificationService()
        notif.notify_approval_complete(
            report.data["uploaded_by"],
            report.data["report_date"],
            user.full_name
        )
    except Exception:
        pass

    return {"message": "Report approved successfully"}


@router.post("/{report_id}/reject")
async def reject_report(
    report_id: str,
    request: DSRRejectRequest,
    user: CurrentUser = Depends(require_role("manager", "super_admin"))
):
    """Reject a DSR report with a reason."""
    supabase = get_supabase_client()

    supabase.table("dsr_reports").update({
        "status": "rejected",
        "reviewed_by": user.id,
        "rejected_at": "now()",
        "rejection_reason": request.reason,
    }).eq("id", report_id).execute()

    # Audit log
    supabase.table("audit_logs").insert({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "action": "reject",
        "entity_type": "dsr_report",
        "entity_id": report_id,
        "new_values": {"reason": request.reason},
    }).execute()

    return {"message": "Report rejected"}


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user: CurrentUser = Depends(require_role("manager", "super_admin"))
):
    """Soft delete a DSR report."""
    supabase = get_supabase_client()

    supabase.table("dsr_reports").update({
        "deleted_at": "now()"
    }).eq("id", report_id).execute()

    return {"message": "Report deleted"}
