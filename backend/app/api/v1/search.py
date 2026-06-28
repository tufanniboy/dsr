"""
Global search endpoint.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.security import require_role, CurrentUser
from app.core.supabase import get_supabase_client

router = APIRouter()


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Optional[str] = Query(None, description="Filter: manager, date, amount, status"),
    page: int = 1,
    per_page: int = 20,
    user: CurrentUser = Depends(require_role("staff", "manager", "super_admin"))
):
    """Global search across DSR reports."""
    supabase = get_supabase_client()

    query = supabase.table("dsr_reports").select(
        "id, report_date, manager_name, status, total_sales, pump_id",
        count="exact"
    ).is_("deleted_at", "null")

    # Apply role filter
    if user.role == "staff":
        query = query.eq("uploaded_by", user.id)
    elif user.pump_id and not user.is_super_admin:
        query = query.eq("pump_id", user.pump_id)

    # Apply search filter
    if type == "manager" or not type:
        query = query.ilike("manager_name", f"%{q}%")
    elif type == "date":
        query = query.eq("report_date", q)
    elif type == "status":
        query = query.eq("status", q.lower())
    elif type == "amount":
        try:
            amount = float(q)
            query = query.gte("total_sales", amount - 100).lte("total_sales", amount + 100)
        except ValueError:
            pass

    offset = (page - 1) * per_page
    result = query.order("report_date", desc=True).range(offset, offset + per_page - 1).execute()

    return {
        "query": q,
        "type": type,
        "data": result.data or [],
        "total": result.count or 0,
        "page": page,
    }
