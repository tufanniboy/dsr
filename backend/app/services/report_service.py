"""
Report generation service.
Handles daily, weekly, monthly, and custom date range report queries.
"""

from typing import Dict, List, Optional
from datetime import date, timedelta
import logging

from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class ReportService:
    """Generates and queries DSR reports."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def get_reports(
        self,
        pump_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        manager: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict:
        """Get paginated DSR reports with filters."""
        query = self.supabase.table("dsr_reports").select(
            "*, users!dsr_reports_uploaded_by_fkey(full_name)",
            count="exact"
        ).is_("deleted_at", "null").order("report_date", desc=True)

        if pump_id:
            query = query.eq("pump_id", pump_id)
        if start_date:
            query = query.gte("report_date", start_date)
        if end_date:
            query = query.lte("report_date", end_date)
        if manager:
            query = query.ilike("manager_name", f"%{manager}%")
        if status:
            query = query.eq("status", status)

        # Pagination
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        result = query.execute()

        return {
            "data": result.data or [],
            "total": result.count or 0,
            "page": page,
            "per_page": per_page,
            "total_pages": ((result.count or 0) + per_page - 1) // per_page,
        }

    def get_report_detail(self, report_id: str) -> Optional[Dict]:
        """Get a single report with all entries, OCR fields, and validation logs."""
        report = self.supabase.table("dsr_reports").select("*").eq(
            "id", report_id
        ).single().execute()

        if not report.data:
            return None

        entries = self.supabase.table("dsr_entries").select("*").eq(
            "report_id", report_id
        ).order("duty_number").execute()

        ocr_fields = self.supabase.table("ocr_fields").select("*").eq(
            "report_id", report_id
        ).execute()

        validation = self.supabase.table("validation_logs").select("*").eq(
            "report_id", report_id
        ).execute()

        return {
            "report": report.data,
            "entries": entries.data or [],
            "ocr_fields": ocr_fields.data or [],
            "validation": validation.data or [],
        }

    def get_daily_summary(self, report_date: str, pump_id: Optional[str] = None) -> Dict:
        """Get summary for a specific date."""
        query = self.supabase.table("dsr_reports").select(
            "*, dsr_entries(*)"
        ).eq("report_date", report_date).is_("deleted_at", "null")

        if pump_id:
            query = query.eq("pump_id", pump_id)

        result = query.execute()
        data = result.data or []

        total_sales = sum(float(r.get("total_sales", 0) or 0) for r in data)
        total_cash = sum(float(r.get("total_cash", 0) or 0) for r in data)
        total_upi = sum(float(r.get("total_upi", 0) or 0) for r in data)
        total_card = sum(float(r.get("total_card", 0) or 0) for r in data)

        return {
            "date": report_date,
            "total_reports": len(data),
            "total_sales": total_sales,
            "total_cash": total_cash,
            "total_upi": total_upi,
            "total_card": total_card,
            "reports": data,
        }

    def get_report_entries_flat(
        self,
        pump_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        manager: Optional[str] = None,
    ) -> List[Dict]:
        """Get flat list of all entries for export."""
        query = self.supabase.table("dsr_reports").select(
            "report_date, manager_name, dsr_entries(*)"
        ).eq("status", "approved").is_("deleted_at", "null")

        if pump_id:
            query = query.eq("pump_id", pump_id)
        if start_date:
            query = query.gte("report_date", start_date)
        if end_date:
            query = query.lte("report_date", end_date)
        if manager:
            query = query.ilike("manager_name", f"%{manager}%")

        result = query.order("report_date", desc=True).execute()
        data = result.data or []

        # Flatten
        flat = []
        for report in data:
            entries = report.get("dsr_entries", [])
            for entry in entries:
                flat.append({
                    "date": report["report_date"],
                    "manager_name": report["manager_name"],
                    **entry
                })

        return flat
