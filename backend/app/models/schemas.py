"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


# ── Enums ──

class UserRole(str, Enum):
    super_admin = "super_admin"
    manager = "manager"
    staff = "staff"


class DSRStatus(str, Enum):
    processing = "processing"
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


# ── User Schemas ──

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.staff
    phone: Optional[str] = None
    pump_id: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    pump_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    pump_id: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None


# ── Auth Schemas ──

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse


# ── DSR Schemas ──

class DSREntryUpdate(BaseModel):
    duty_number: int
    duty_name: Optional[str] = None
    start_reading: Optional[float] = None
    end_reading: Optional[float] = None
    testing: Optional[float] = 0
    rate: Optional[float] = None
    total_amount: Optional[float] = None
    card: Optional[float] = 0
    upi: Optional[float] = 0
    expenses: Optional[float] = 0
    credit: Optional[float] = 0
    total_cash_in_hand: Optional[float] = 0
    short_amount: Optional[float] = 0


class DSRReportUpdate(BaseModel):
    manager_name: Optional[str] = None
    report_date: Optional[str] = None
    notes: Optional[str] = None
    entries: Optional[List[DSREntryUpdate]] = None


class DSRApproveRequest(BaseModel):
    notes: Optional[str] = None


class DSRRejectRequest(BaseModel):
    reason: str


# ── Report Schemas ──

class ReportQuery(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    manager: Optional[str] = None
    pump_id: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    per_page: int = 20


# ── Analytics Schemas ──

class KPIResponse(BaseModel):
    today_sales: float = 0
    monthly_sales: float = 0
    cash_collection: float = 0
    upi_collection: float = 0
    card_collection: float = 0
    credit_collection: float = 0
    expenses: float = 0
    net_revenue: float = 0
    total_reports: int = 0
    pending_approvals: int = 0
    rejected_reports: int = 0


# ── Template Schemas ──

class TemplateCreate(BaseModel):
    name: str
    version: str = "v1"
    description: Optional[str] = None
    pump_id: Optional[str] = None
    coordinates: Dict[str, Any]
    is_default: bool = False


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


# ── Search Schemas ──

class SearchQuery(BaseModel):
    query: str
    type: Optional[str] = None  # manager, date, amount, pump, status
    page: int = 1
    per_page: int = 20


# ── Notification Schemas ──

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    is_read: bool
    created_at: str
    data: Optional[Dict] = None


# ── OCR Schemas ──

class OCRFieldResult(BaseModel):
    field_name: str
    text: str
    confidence: float
    confidence_percent: int
    level: str
    color: str
    needs_review: bool
    gemini_used: bool = False
    gemini_value: Optional[str] = None


class OCRProcessingResult(BaseModel):
    report_id: str
    ocr_log_id: str
    status: str
    fields: List[OCRFieldResult]
    validation: List[Dict]
    processing_time_ms: int
    gemini_calls: int


# ── Pump Schemas ──

class PumpCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gst_number: Optional[str] = None
    fuel_types: List[str] = ["petrol", "diesel"]


class PumpUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
