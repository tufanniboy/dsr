"""
Business rule validation engine for DSR data.
Implements 10 validation rules with error/warning severity levels.
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class ValidationResult:
    """Single validation result."""

    def __init__(self, rule_id: str, rule_name: str, severity: str,
                 field_name: str, message: str, duty_number: Optional[int] = None,
                 expected_value: str = "", actual_value: str = ""):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.severity = severity  # 'error', 'warning', 'info'
        self.field_name = field_name
        self.message = message
        self.duty_number = duty_number
        self.expected_value = expected_value
        self.actual_value = actual_value

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "field_name": self.field_name,
            "message": self.message,
            "duty_number": self.duty_number,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
        }


class ValidationEngine:
    """
    Validates DSR entries against 10 business rules.
    Returns a list of validation results with severity levels.
    """

    def validate_report(self, report_data: dict, entries: List[dict]) -> List[ValidationResult]:
        """
        Run all validation rules on a DSR report.

        Args:
            report_data: {"manager_name": str, "report_date": str, "pump_id": str}
            entries: List of duty entries, each with all field values

        Returns:
            List of ValidationResult
        """
        results = []

        # Header validations
        results.extend(self._rule_5_date_format(report_data))
        results.extend(self._rule_6_required_fields(report_data, entries))
        results.extend(self._rule_10_duplicate_check(report_data))

        # Per-duty validations
        for entry in entries:
            duty_num = entry.get("duty_number", 0)

            # Skip empty duties
            if not self._has_data(entry):
                continue

            results.extend(self._rule_1_reading_order(entry, duty_num))
            results.extend(self._rule_2_testing_positive(entry, duty_num))
            results.extend(self._rule_3_rate_positive(entry, duty_num))
            results.extend(self._rule_4_total_calculation(entry, duty_num))
            results.extend(self._rule_7_no_negatives(entry, duty_num))
            results.extend(self._rule_8_payment_reconciliation(entry, duty_num))
            results.extend(self._rule_9_abnormal_values(entry, duty_num))

        return results

    def _safe_float(self, value, default: float = 0.0) -> float:
        """Safely convert a value to float."""
        if value is None or value == "":
            return default
        try:
            return float(str(value).replace(",", "").strip())
        except (ValueError, TypeError):
            return default

    def _has_data(self, entry: dict) -> bool:
        """Check if a duty entry has any meaningful data."""
        fields = ["start_reading", "end_reading", "total_amount", "rate"]
        return any(entry.get(f) not in (None, "", "0", 0) for f in fields)

    # ── Rule 1: End Reading > Start Reading ──

    def _rule_1_reading_order(self, entry: dict, duty: int) -> List[ValidationResult]:
        start = self._safe_float(entry.get("start_reading"))
        end = self._safe_float(entry.get("end_reading"))

        if start > 0 and end > 0 and end <= start:
            return [ValidationResult(
                rule_id="R1", rule_name="Reading Order",
                severity="error", field_name="end_reading",
                message=f"Duty {duty}: End Reading ({end}) must be greater than Start Reading ({start})",
                duty_number=duty,
                expected_value=f"> {start}", actual_value=str(end)
            )]
        return []

    # ── Rule 2: Testing >= 0 ──

    def _rule_2_testing_positive(self, entry: dict, duty: int) -> List[ValidationResult]:
        testing = self._safe_float(entry.get("testing"))

        if testing < 0:
            return [ValidationResult(
                rule_id="R2", rule_name="Testing Non-Negative",
                severity="error", field_name="testing",
                message=f"Duty {duty}: Testing value ({testing}) cannot be negative",
                duty_number=duty,
                expected_value=">= 0", actual_value=str(testing)
            )]
        return []

    # ── Rule 3: Rate > 0 ──

    def _rule_3_rate_positive(self, entry: dict, duty: int) -> List[ValidationResult]:
        rate = self._safe_float(entry.get("rate"))

        if rate is not None and rate <= 0 and self._has_data(entry):
            return [ValidationResult(
                rule_id="R3", rule_name="Rate Positive",
                severity="error", field_name="rate",
                message=f"Duty {duty}: Rate ({rate}) must be greater than 0",
                duty_number=duty,
                expected_value="> 0", actual_value=str(rate)
            )]
        return []

    # ── Rule 4: Total ≈ (End - Start - Testing) × Rate ──

    def _rule_4_total_calculation(self, entry: dict, duty: int) -> List[ValidationResult]:
        start = self._safe_float(entry.get("start_reading"))
        end = self._safe_float(entry.get("end_reading"))
        testing = self._safe_float(entry.get("testing"))
        rate = self._safe_float(entry.get("rate"))
        total = self._safe_float(entry.get("total_amount"))

        if all(v > 0 for v in [start, end, rate]) and end > start:
            expected = (end - start - testing) * rate
            tolerance = expected * 0.02  # 2% tolerance

            if abs(total - expected) > max(tolerance, 1.0):
                return [ValidationResult(
                    rule_id="R4", rule_name="Total Calculation",
                    severity="warning", field_name="total_amount",
                    message=f"Duty {duty}: Total Amount (₹{total:,.2f}) doesn't match calculated value (₹{expected:,.2f})",
                    duty_number=duty,
                    expected_value=f"≈ ₹{expected:,.2f}", actual_value=f"₹{total:,.2f}"
                )]
        return []

    # ── Rule 5: Date Format ──

    def _rule_5_date_format(self, report: dict) -> List[ValidationResult]:
        date_str = report.get("report_date", "")
        if not date_str:
            return [ValidationResult(
                rule_id="R5", rule_name="Date Format",
                severity="error", field_name="date",
                message="Report date is required"
            )]

        # Try multiple date formats
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"]:
            try:
                parsed = datetime.strptime(str(date_str), fmt)
                # Check if date is reasonable (not in the future, not too old)
                if parsed.date() > datetime.now().date():
                    return [ValidationResult(
                        rule_id="R5", rule_name="Date Format",
                        severity="warning", field_name="date",
                        message="Report date is in the future",
                        actual_value=str(date_str)
                    )]
                return []
            except ValueError:
                continue

        return [ValidationResult(
            rule_id="R5", rule_name="Date Format",
            severity="error", field_name="date",
            message=f"Invalid date format: '{date_str}'. Expected DD/MM/YYYY",
            actual_value=str(date_str)
        )]

    # ── Rule 6: Required Fields ──

    def _rule_6_required_fields(self, report: dict, entries: List[dict]) -> List[ValidationResult]:
        results = []

        if not report.get("manager_name"):
            results.append(ValidationResult(
                rule_id="R6", rule_name="Required Fields",
                severity="error", field_name="manager_name",
                message="Manager Name is required"
            ))

        # Check at least one duty has data
        has_any_data = any(self._has_data(e) for e in entries)
        if not has_any_data:
            results.append(ValidationResult(
                rule_id="R6", rule_name="Required Fields",
                severity="error", field_name="entries",
                message="At least one duty must have data"
            ))

        return results

    # ── Rule 7: No Negative Values ──

    def _rule_7_no_negatives(self, entry: dict, duty: int) -> List[ValidationResult]:
        results = []
        numeric_fields = [
            "start_reading", "end_reading", "testing", "rate",
            "total_amount", "card", "upi", "expenses", "credit",
            "total_cash_in_hand"
        ]

        for field in numeric_fields:
            value = self._safe_float(entry.get(field))
            if value < 0:
                results.append(ValidationResult(
                    rule_id="R7", rule_name="No Negatives",
                    severity="error", field_name=field,
                    message=f"Duty {duty}: {field.replace('_', ' ').title()} cannot be negative ({value})",
                    duty_number=duty,
                    expected_value=">= 0", actual_value=str(value)
                ))

        return results

    # ── Rule 8: Payment Reconciliation ──

    def _rule_8_payment_reconciliation(self, entry: dict, duty: int) -> List[ValidationResult]:
        card = self._safe_float(entry.get("card"))
        upi = self._safe_float(entry.get("upi"))
        cash = self._safe_float(entry.get("total_cash_in_hand"))
        credit = self._safe_float(entry.get("credit"))
        expenses = self._safe_float(entry.get("expenses"))
        total = self._safe_float(entry.get("total_amount"))

        if total > 0:
            payment_sum = card + upi + cash + credit + expenses
            diff = abs(total - payment_sum)

            if diff > 1.0:  # ₹1 tolerance
                return [ValidationResult(
                    rule_id="R8", rule_name="Payment Reconciliation",
                    severity="warning", field_name="payment_split",
                    message=(
                        f"Duty {duty}: Payment total (₹{payment_sum:,.2f}) doesn't match "
                        f"Total Amount (₹{total:,.2f}). Difference: ₹{diff:,.2f}"
                    ),
                    duty_number=duty,
                    expected_value=f"₹{total:,.2f}",
                    actual_value=f"₹{payment_sum:,.2f}"
                )]
        return []

    # ── Rule 9: Abnormal Values ──

    def _rule_9_abnormal_values(self, entry: dict, duty: int) -> List[ValidationResult]:
        results = []

        # Abnormally high total (> ₹10 lakh for a single duty)
        total = self._safe_float(entry.get("total_amount"))
        if total > 1000000:
            results.append(ValidationResult(
                rule_id="R9", rule_name="Abnormal Value",
                severity="warning", field_name="total_amount",
                message=f"Duty {duty}: Unusually high Total Amount (₹{total:,.2f})",
                duty_number=duty, actual_value=f"₹{total:,.2f}"
            ))

        # Rate outside typical range (₹80-₹130)
        rate = self._safe_float(entry.get("rate"))
        if rate > 0 and (rate < 50 or rate > 200):
            results.append(ValidationResult(
                rule_id="R9", rule_name="Abnormal Value",
                severity="warning", field_name="rate",
                message=f"Duty {duty}: Rate (₹{rate}) is outside typical range (₹50-₹200)",
                duty_number=duty, actual_value=f"₹{rate}"
            ))

        return results

    # ── Rule 10: Duplicate Submission ──

    def _rule_10_duplicate_check(self, report: dict) -> List[ValidationResult]:
        try:
            supabase = get_supabase_client()
            pump_id = report.get("pump_id")
            report_date = report.get("report_date")
            report_id = report.get("id")

            if not pump_id or not report_date:
                return []

            query = supabase.table("dsr_reports").select("id").eq(
                "pump_id", pump_id
            ).eq(
                "report_date", str(report_date)
            ).is_("deleted_at", "null")

            # Exclude current report if editing
            if report_id:
                query = query.neq("id", report_id)

            result = query.execute()

            if result.data and len(result.data) > 0:
                return [ValidationResult(
                    rule_id="R10", rule_name="Duplicate Check",
                    severity="error", field_name="report_date",
                    message=f"A DSR report already exists for this date ({report_date}) and pump"
                )]

        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")

        return []
