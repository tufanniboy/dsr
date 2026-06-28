"""
Analytics aggregation service.
Computes KPIs, trends, and comparison data for the dashboard and analytics page.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
import logging

from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Aggregates data for dashboard KPIs, charts, and analytics."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def get_dashboard_kpis(self, pump_id: Optional[str] = None) -> Dict:
        """Get all KPI values for the dashboard cards."""
        today = date.today().isoformat()
        month_start = date.today().replace(day=1).isoformat()

        # Base query
        def build_query(date_filter: str = None, date_field: str = "report_date"):
            q = self.supabase.table("dsr_reports").select(
                "total_sales, total_cash, total_upi, total_card, total_credit, total_expenses, status"
            ).eq("status", "approved").is_("deleted_at", "null")
            if pump_id:
                q = q.eq("pump_id", pump_id)
            if date_filter:
                q = q.eq(date_field, date_filter)
            return q

        # Today's data
        today_result = build_query(today).execute()
        today_data = today_result.data or []
        today_sales = sum(float(r.get("total_sales", 0) or 0) for r in today_data)
        today_cash = sum(float(r.get("total_cash", 0) or 0) for r in today_data)
        today_upi = sum(float(r.get("total_upi", 0) or 0) for r in today_data)
        today_card = sum(float(r.get("total_card", 0) or 0) for r in today_data)
        today_credit = sum(float(r.get("total_credit", 0) or 0) for r in today_data)
        today_expenses = sum(float(r.get("total_expenses", 0) or 0) for r in today_data)

        # Monthly data
        monthly_q = self.supabase.table("dsr_reports").select(
            "total_sales, total_cash, total_upi, total_card, total_credit, total_expenses"
        ).eq("status", "approved").is_("deleted_at", "null").gte("report_date", month_start)
        if pump_id:
            monthly_q = monthly_q.eq("pump_id", pump_id)
        monthly_result = monthly_q.execute()
        monthly_data = monthly_result.data or []
        monthly_sales = sum(float(r.get("total_sales", 0) or 0) for r in monthly_data)

        # Pending approvals
        pending_q = self.supabase.table("dsr_reports").select(
            "id", count="exact"
        ).eq("status", "pending_review").is_("deleted_at", "null")
        if pump_id:
            pending_q = pending_q.eq("pump_id", pump_id)
        pending_result = pending_q.execute()
        pending_count = pending_result.count or 0

        # Rejected reports this month
        rejected_q = self.supabase.table("dsr_reports").select(
            "id", count="exact"
        ).eq("status", "rejected").is_("deleted_at", "null").gte("report_date", month_start)
        if pump_id:
            rejected_q = rejected_q.eq("pump_id", pump_id)
        rejected_result = rejected_q.execute()
        rejected_count = rejected_result.count or 0

        # Total reports this month
        total_q = self.supabase.table("dsr_reports").select(
            "id", count="exact"
        ).is_("deleted_at", "null").gte("report_date", month_start)
        if pump_id:
            total_q = total_q.eq("pump_id", pump_id)
        total_result = total_q.execute()
        total_reports = total_result.count or 0

        net_revenue = today_sales - today_expenses

        return {
            "today_sales": today_sales,
            "monthly_sales": monthly_sales,
            "cash_collection": today_cash,
            "upi_collection": today_upi,
            "card_collection": today_card,
            "credit_collection": today_credit,
            "expenses": today_expenses,
            "net_revenue": net_revenue,
            "total_reports": total_reports,
            "pending_approvals": pending_count,
            "rejected_reports": rejected_count,
        }

    def get_sales_trend(self, days: int = 7, pump_id: Optional[str] = None) -> List[Dict]:
        """Get daily sales for the last N days."""
        start_date = (date.today() - timedelta(days=days - 1)).isoformat()

        q = self.supabase.table("dsr_reports").select(
            "report_date, total_sales"
        ).eq("status", "approved").is_("deleted_at", "null").gte("report_date", start_date).order("report_date")

        if pump_id:
            q = q.eq("pump_id", pump_id)

        result = q.execute()
        data = result.data or []

        # Group by date
        by_date = {}
        for row in data:
            d = row["report_date"]
            by_date[d] = by_date.get(d, 0) + float(row.get("total_sales", 0) or 0)

        # Fill in missing dates with 0
        trend = []
        for i in range(days):
            d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
            trend.append({
                "date": d,
                "sales": by_date.get(d, 0)
            })

        return trend

    def get_revenue_breakdown(self, start_date: str, end_date: str,
                               pump_id: Optional[str] = None) -> Dict:
        """Get revenue breakdown by payment method for a date range."""
        q = self.supabase.table("dsr_reports").select(
            "total_sales, total_cash, total_upi, total_card, total_credit, total_expenses"
        ).eq("status", "approved").is_("deleted_at", "null").gte(
            "report_date", start_date
        ).lte("report_date", end_date)

        if pump_id:
            q = q.eq("pump_id", pump_id)

        result = q.execute()
        data = result.data or []

        totals = {
            "total_sales": 0, "cash": 0, "upi": 0,
            "card": 0, "credit": 0, "expenses": 0
        }

        for row in data:
            totals["total_sales"] += float(row.get("total_sales", 0) or 0)
            totals["cash"] += float(row.get("total_cash", 0) or 0)
            totals["upi"] += float(row.get("total_upi", 0) or 0)
            totals["card"] += float(row.get("total_card", 0) or 0)
            totals["credit"] += float(row.get("total_credit", 0) or 0)
            totals["expenses"] += float(row.get("total_expenses", 0) or 0)

        return totals

    def get_manager_performance(self, start_date: str, end_date: str,
                                 pump_id: Optional[str] = None) -> List[Dict]:
        """Get performance metrics per manager."""
        q = self.supabase.table("dsr_reports").select(
            "manager_name, total_sales, status"
        ).is_("deleted_at", "null").gte("report_date", start_date).lte("report_date", end_date)

        if pump_id:
            q = q.eq("pump_id", pump_id)

        result = q.execute()
        data = result.data or []

        by_manager = {}
        for row in data:
            name = row.get("manager_name", "Unknown")
            if name not in by_manager:
                by_manager[name] = {"name": name, "total_sales": 0, "reports": 0, "approved": 0}
            by_manager[name]["total_sales"] += float(row.get("total_sales", 0) or 0)
            by_manager[name]["reports"] += 1
            if row.get("status") == "approved":
                by_manager[name]["approved"] += 1

        return sorted(by_manager.values(), key=lambda x: x["total_sales"], reverse=True)

    def get_monthly_revenue(self, year: int, pump_id: Optional[str] = None) -> List[Dict]:
        """Get monthly revenue for a given year."""
        start = f"{year}-01-01"
        end = f"{year}-12-31"

        q = self.supabase.table("dsr_reports").select(
            "report_date, total_sales"
        ).eq("status", "approved").is_("deleted_at", "null").gte(
            "report_date", start
        ).lte("report_date", end)

        if pump_id:
            q = q.eq("pump_id", pump_id)

        result = q.execute()
        data = result.data or []

        by_month = {i: 0 for i in range(1, 13)}
        for row in data:
            month = int(row["report_date"].split("-")[1])
            by_month[month] += float(row.get("total_sales", 0) or 0)

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        return [{"month": months[i - 1], "sales": by_month[i]} for i in range(1, 13)]
