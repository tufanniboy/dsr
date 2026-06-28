"""
Report generation and export endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from typing import Optional
import io
import logging

from app.core.security import require_role, CurrentUser
from app.services.report_service import ReportService
from app.services.export_service import ExportService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/daily")
async def daily_report(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get daily sales summary."""
    service = ReportService()
    effective_pump_id = pump_id or user.pump_id
    return service.get_daily_summary(date, pump_id=effective_pump_id)


@router.get("/weekly")
async def weekly_report(
    end_date: Optional[str] = None,
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get weekly report (last 7 days)."""
    from datetime import date as dt_date, timedelta
    end = end_date or dt_date.today().isoformat()
    start = (dt_date.fromisoformat(end) - timedelta(days=6)).isoformat()

    service = ReportService()
    return service.get_reports(
        pump_id=pump_id or user.pump_id,
        start_date=start,
        end_date=end,
        status="approved"
    )


@router.get("/monthly")
async def monthly_report(
    year: int = Query(...),
    month: int = Query(...),
    pump_id: Optional[str] = None,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get monthly report."""
    from datetime import date as dt_date
    import calendar

    start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end = f"{year}-{month:02d}-{last_day}"

    service = ReportService()
    return service.get_reports(
        pump_id=pump_id or user.pump_id,
        start_date=start,
        end_date=end,
        status="approved"
    )


@router.get("/custom")
async def custom_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    pump_id: Optional[str] = None,
    manager: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Get custom date range report."""
    service = ReportService()
    return service.get_reports(
        pump_id=pump_id or user.pump_id,
        start_date=start_date,
        end_date=end_date,
        manager=manager,
        status=status,
        page=page,
        per_page=per_page,
    )


@router.get("/export/{format}")
async def export_report(
    format: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    pump_id: Optional[str] = None,
    manager: Optional[str] = None,
    user: CurrentUser = Depends(require_role("manager", "super_admin"))
):
    """Export report as Excel, PDF, or CSV."""
    service = ReportService()
    export_service = ExportService()

    data = service.get_report_entries_flat(
        pump_id=pump_id or user.pump_id,
        start_date=start_date,
        end_date=end_date,
        manager=manager,
    )

    title = f"DSR Report {start_date} to {end_date}"

    if format == "excel":
        content = export_service.export_excel(data, title)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=dsr_report_{start_date}_{end_date}.xlsx"}
        )
    elif format == "pdf":
        content = export_service.export_pdf(data, title)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=dsr_report_{start_date}_{end_date}.pdf"}
        )
    elif format == "csv":
        content = export_service.export_csv(data)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=dsr_report_{start_date}_{end_date}.csv"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use: excel, pdf, csv")
