"""
API v1 aggregate router — combines all route modules.
"""

from fastapi import APIRouter
from app.api.v1 import auth, dsr, reports, analytics, users, templates, search, notifications

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(dsr.router, prefix="/dsr", tags=["DSR Reports"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_v1_router.include_router(search.router, prefix="/search", tags=["Search"])
api_v1_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
