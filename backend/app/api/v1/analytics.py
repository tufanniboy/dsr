"""
Analytics endpoints — KPIs, trends, breakdowns.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date, timedelta

from app.core.security import require_role, CurrentUser
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/kpi")
async def get_kpis(
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get dashboard KPI values."""
    service = AnalyticsService()
    return service.get_dashboard_kpis(pump_id=pump_id or user.pump_id)


@router.get("/sales-trend")
async def sales_trend(
    days: int = Query(7, ge=1, le=90),
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get daily sales trend for the last N days."""
    service = AnalyticsService()
    return service.get_sales_trend(days=days, pump_id=pump_id or user.pump_id)


@router.get("/revenue")
async def revenue_breakdown(
    start_date: str = Query(...),
    end_date: str = Query(...),
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get revenue breakdown by payment method."""
    service = AnalyticsService()
    return service.get_revenue_breakdown(start_date, end_date, pump_id=pump_id or user.pump_id)


@router.get("/payment-split")
async def payment_split(
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get today's payment method split."""
    today = date.today().isoformat()
    service = AnalyticsService()
    return service.get_revenue_breakdown(today, today, pump_id=pump_id or user.pump_id)


@router.get("/manager-performance")
async def manager_performance(
    start_date: str = Query(...),
    end_date: str = Query(...),
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("manager", "super_admin"))
):
    """Get per-manager performance metrics."""
    service = AnalyticsService()
    return service.get_manager_performance(start_date, end_date, pump_id=pump_id or user.pump_id)


@router.get("/monthly-revenue")
async def monthly_revenue(
    year: int = Query(...),
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get monthly revenue for a given year."""
    service = AnalyticsService()
    return service.get_monthly_revenue(year, pump_id=pump_id or user.pump_id)
