"""
OCR orchestration service — coordinates the full OCR pipeline:
1. Image preprocessing
2. Template-based field extraction
3. PaddleOCR on each field
4. Confidence evaluation
5. Gemini fallback for low-confidence fields
6. Validation
"""

import time
import uuid
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging

from app.ocr.preprocessor import ImagePreprocessor
from app.ocr.engine import OCREngine
from app.ocr.template_matcher import TemplateMatcher
from app.ocr.confidence import ConfidenceEngine
from app.services.gemini_service import get_gemini_service
from app.services.validation_service import ValidationEngine
from app.core.supabase import get_supabase_client, get_storage

logger = logging.getLogger(__name__)


class OCRService:
    """
    Full OCR pipeline orchestrator.
    """

    def __init__(self, ocr_engine: Optional[OCREngine] = None):
        self.preprocessor = ImagePreprocessor()
        self.template_matcher = TemplateMatcher(self.preprocessor)
        self.confidence_engine = ConfidenceEngine()
        self.validation_engine = ValidationEngine()
        self.ocr_engine = ocr_engine

    def _get_ocr_engine(self) -> OCREngine:
        """Get OCR engine (lazy init if not provided)."""
        if self.ocr_engine is None:
            from app.main import get_ocr_engine
            self.ocr_engine = get_ocr_engine()
        return self.ocr_engine

    async def process_dsr_image(
        self,
        image_bytes: bytes,
        report_id: str,
        pump_id: str,
        template_id: str = "dsr_default",
        template_json: Optional[dict] = None
    ) -> Dict:
        """
        Run the complete OCR pipeline on a DSR image.

        Steps:
        1. Preprocess image (detect, correct, enhance)
        2. Load template coordinates
        3. Crop individual fields
        4. Run PaddleOCR on each field
        5. Evaluate confidence
        6. Send low-confidence fields to Gemini
        7. Run validation
        8. Store results

        Returns:
            Complete OCR results with fields, confidence, and validation
        """
        pipeline_start = time.time()
        supabase = get_supabase_client()

        # Create OCR log entry
        ocr_log_id = str(uuid.uuid4())
        supabase.table("ocr_logs").insert({
            "id": ocr_log_id,
            "report_id": report_id,
            "status": "processing"
        }).execute()

        try:
            # ── Step 1-6: Image Preprocessing ──
            preprocess_start = time.time()
            processed_image, metadata = self.preprocessor.process(image_bytes)
            preprocess_ms = int((time.time() - preprocess_start) * 1000)

            # Save processed image
            storage = get_storage()
            processed_bytes = self.preprocessor.encode_to_bytes(processed_image)
            processed_path = f"{pump_id}/{report_id}/processed.jpg"
            try:
                processed_url = storage.upload_image(processed_path, processed_bytes)
            except Exception:
                processed_url = ""

            # ── Step 7-9: Template Field Extraction ──
            if template_json:
                template = self.template_matcher.load_template_from_json(template_json)
            else:
                template = self.template_matcher.load_template(template_id)

            field_images = self.template_matcher.extract_fields(processed_image, template)

            # ── Step 10-11: PaddleOCR on Each Field ──
            ocr_start = time.time()
            engine = self._get_ocr_engine()
            ocr_results = engine.ocr_fields(field_images)
            ocr_ms = int((time.time() - ocr_start) * 1000)

            # Clean numeric fields
            for field_name, result in ocr_results.items():
                parsed = TemplateMatcher.parse_field_name(field_name)
                if parsed["field"] not in ("duty_name", "manager_name", "date"):
                    result["text"] = OCREngine.clean_numeric(result["text"])

            # ── Step 11-12: Confidence Evaluation & Gemini Fallback ──
            evaluation = self.confidence_engine.evaluate_results(ocr_results)
            gemini_calls = 0

            if evaluation["gemini_needed"]:
                gemini_service = get_gemini_service()
                if gemini_service.is_available():
                    low_conf_images = {
                        name: field_images[name]
                        for name in evaluation["gemini_needed"]
                        if name in field_images
                    }
                    gemini_results = gemini_service.read_fields_batch(low_conf_images)
                    gemini_calls = len(gemini_results)

                    # Merge Gemini results
                    for field_name, gemini_result in gemini_results.items():
                        if gemini_result["success"] and gemini_result["text"]:
                            # Store both original and Gemini values
                            ocr_results[field_name]["gemini_value"] = gemini_result["text"]
                            ocr_results[field_name]["gemini_used"] = True
                            # Use Gemini value as final
                            parsed = TemplateMatcher.parse_field_name(field_name)
                            if parsed["field"] not in ("duty_name", "manager_name", "date"):
                                ocr_results[field_name]["final_text"] = OCREngine.clean_numeric(gemini_result["text"])
                            else:
                                ocr_results[field_name]["final_text"] = gemini_result["text"]

            # Set final text for all fields
            for field_name, result in ocr_results.items():
                if "final_text" not in result:
                    result["final_text"] = result["text"]
                    result["gemini_used"] = False
                    result["gemini_value"] = None

            # ── Step 13: Parse into structured entries ──
            report_data, entries = self._parse_ocr_to_entries(ocr_results, report_id)

            # ── Step 14: Validation ──
            validation_start = time.time()
            report_data["pump_id"] = pump_id
            report_data["id"] = report_id
            validation_results = self.validation_engine.validate_report(report_data, entries)
            validation_ms = int((time.time() - validation_start) * 1000)

            # ── Store OCR field results ──
            ocr_field_records = []
            for field_name, result in ocr_results.items():
                parsed = TemplateMatcher.parse_field_name(field_name)
                ocr_field_records.append({
                    "id": str(uuid.uuid4()),
                    "ocr_log_id": ocr_log_id,
                    "report_id": report_id,
                    "field_name": field_name,
                    "duty_number": parsed.get("duty"),
                    "ocr_value": result["text"],
                    "ocr_confidence": result["confidence"],
                    "confidence_level": evaluation["field_levels"].get(field_name, "low"),
                    "gemini_value": result.get("gemini_value"),
                    "gemini_used": result.get("gemini_used", False),
                    "final_value": result.get("final_text", result["text"]),
                })

            if ocr_field_records:
                supabase.table("ocr_fields").insert(ocr_field_records).execute()

            # ── Store validation results ──
            if validation_results:
                val_records = [{
                    "id": str(uuid.uuid4()),
                    "report_id": report_id,
                    **v.to_dict()
                } for v in validation_results]
                supabase.table("validation_logs").insert(val_records).execute()

            # ── Update OCR log ──
            total_ms = int((time.time() - pipeline_start) * 1000)
            supabase.table("ocr_logs").update({
                "status": "completed",
                "completed_at": "now()",
                "processing_time_ms": total_ms,
                "total_fields": evaluation["total_fields"],
                "high_confidence_count": evaluation["high_confidence"],
                "medium_confidence_count": evaluation["medium_confidence"],
                "low_confidence_count": evaluation["low_confidence"],
                "gemini_calls": gemini_calls,
                "average_confidence": evaluation["average_confidence"],
                "image_preprocessing_ms": preprocess_ms,
                "ocr_extraction_ms": ocr_ms,
                "validation_ms": validation_ms,
            }).eq("id", ocr_log_id).execute()

            # ── Update report with processed image URL ──
            supabase.table("dsr_reports").update({
                "processed_image_url": processed_url,
                "status": "pending_review",
                "manager_name": report_data.get("manager_name", ""),
            }).eq("id", report_id).execute()

            # Format for UI
            ui_fields = self.confidence_engine.format_for_ui(ocr_results)

            return {
                "report_id": report_id,
                "ocr_log_id": ocr_log_id,
                "status": "completed",
                "report_data": report_data,
                "entries": entries,
                "fields": ui_fields,
                "evaluation": evaluation,
                "validation": [v.to_dict() for v in validation_results],
                "processing_time_ms": total_ms,
                "gemini_calls": gemini_calls,
                "processed_image_url": processed_url,
            }

        except Exception as e:
            logger.error(f"OCR pipeline failed: {e}", exc_info=True)

            # Update OCR log with error
            supabase.table("ocr_logs").update({
                "status": "failed",
                "error_message": str(e),
                "completed_at": "now()",
            }).eq("id", ocr_log_id).execute()

            supabase.table("dsr_reports").update({
                "status": "draft",
            }).eq("id", report_id).execute()

            raise

    def _parse_ocr_to_entries(self, ocr_results: Dict, report_id: str) -> Tuple[dict, List[dict]]:
        """
        Parse flat OCR results into structured report data and duty entries.
        """
        report_data = {
            "manager_name": "",
            "report_date": "",
        }

        entries = {}

        for field_name, result in ocr_results.items():
            text = result.get("final_text", result.get("text", ""))
            parsed = TemplateMatcher.parse_field_name(field_name)

            if parsed["duty"] is None:
                # Header field
                if parsed["field"] == "manager_name":
                    report_data["manager_name"] = text
                elif parsed["field"] == "date":
                    report_data["report_date"] = text
            else:
                # Duty field
                duty_num = parsed["duty"]
                if duty_num not in entries:
                    entries[duty_num] = {
                        "report_id": report_id,
                        "duty_number": duty_num,
                        "duty_name": "",
                        "start_reading": None,
                        "end_reading": None,
                        "testing": 0,
                        "rate": None,
                        "total_amount": None,
                        "card": 0,
                        "upi": 0,
                        "expenses": 0,
                        "credit": 0,
                        "total_cash_in_hand": 0,
                        "short_amount": 0,
                    }

                field = parsed["field"]
                if field == "duty_name":
                    entries[duty_num]["duty_name"] = text
                elif field in entries[duty_num]:
                    try:
                        entries[duty_num][field] = float(text) if text else None
                    except (ValueError, TypeError):
                        entries[duty_num][field] = None

        # Convert to sorted list
        entries_list = [entries[k] for k in sorted(entries.keys())]

        return report_data, entries_list
