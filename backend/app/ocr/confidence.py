"""
Confidence scoring engine for OCR results.
Categorizes confidence levels and determines Gemini fallback eligibility.
"""

from typing import Dict, List, Tuple
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class ConfidenceLevel:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceColors:
    HIGH = "#10B981"    # Green
    MEDIUM = "#F59E0B"  # Yellow/Amber
    LOW = "#EF4444"     # Red


class ConfidenceEngine:
    """
    Evaluates OCR confidence scores and determines:
    - Color coding for UI display
    - Whether Gemini fallback is needed
    - Overall report quality score
    """

    def __init__(self):
        settings = get_settings()
        self.high_threshold = settings.OCR_HIGH_CONFIDENCE / 100  # 0.95
        self.low_threshold = settings.OCR_CONFIDENCE_THRESHOLD / 100  # 0.85

    def classify(self, confidence: float) -> str:
        """Classify a confidence score into high/medium/low."""
        if confidence >= self.high_threshold:
            return ConfidenceLevel.HIGH
        elif confidence >= self.low_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def get_color(self, confidence: float) -> str:
        """Get the display color for a confidence score."""
        level = self.classify(confidence)
        return {
            ConfidenceLevel.HIGH: ConfidenceColors.HIGH,
            ConfidenceLevel.MEDIUM: ConfidenceColors.MEDIUM,
            ConfidenceLevel.LOW: ConfidenceColors.LOW,
        }[level]

    def needs_gemini(self, confidence: float) -> bool:
        """Check if a field's confidence is low enough to need Gemini fallback."""
        return confidence < self.low_threshold

    def evaluate_results(self, ocr_results: Dict[str, Dict]) -> Dict:
        """
        Evaluate all OCR results and return summary statistics.

        Args:
            ocr_results: {field_name: {"text": str, "confidence": float}}

        Returns:
            {
                "total_fields": int,
                "high_confidence": int,
                "medium_confidence": int,
                "low_confidence": int,
                "average_confidence": float,
                "gemini_needed": list[str],
                "field_levels": {field_name: "high"|"medium"|"low"}
            }
        """
        total = len(ocr_results)
        high = 0
        medium = 0
        low = 0
        confidences = []
        gemini_needed = []
        field_levels = {}

        for field_name, result in ocr_results.items():
            conf = result.get("confidence", 0.0)
            confidences.append(conf)

            level = self.classify(conf)
            field_levels[field_name] = level

            if level == ConfidenceLevel.HIGH:
                high += 1
            elif level == ConfidenceLevel.MEDIUM:
                medium += 1
            else:
                low += 1
                gemini_needed.append(field_name)

        avg_confidence = sum(confidences) / total if total > 0 else 0.0

        return {
            "total_fields": total,
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low,
            "average_confidence": round(avg_confidence, 4),
            "gemini_needed": gemini_needed,
            "field_levels": field_levels,
        }

    def format_for_ui(self, ocr_results: Dict[str, Dict]) -> List[Dict]:
        """
        Format OCR results with confidence info for the review UI.

        Returns list of:
            {
                "field_name": str,
                "text": str,
                "confidence": float,
                "confidence_percent": int,
                "level": "high"|"medium"|"low",
                "color": str (hex),
                "needs_review": bool
            }
        """
        evaluation = self.evaluate_results(ocr_results)
        formatted = []

        for field_name, result in ocr_results.items():
            conf = result.get("confidence", 0.0)
            level = evaluation["field_levels"][field_name]

            formatted.append({
                "field_name": field_name,
                "text": result.get("text", ""),
                "confidence": conf,
                "confidence_percent": int(conf * 100),
                "level": level,
                "color": self.get_color(conf),
                "needs_review": level != ConfidenceLevel.HIGH,
            })

        # Sort: low confidence first (needs attention)
        formatted.sort(key=lambda x: x["confidence"])

        return formatted
