"""
Gemini AI fallback service.
Only called for low-confidence OCR fields — never the full sheet.
"""

import google.generativeai as genai
from PIL import Image
import io
import numpy as np
import cv2
from typing import Dict, Optional, List
import logging
import time

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Handles Gemini API calls for handwriting recognition fallback.
    Only processes individual field images, never the entire DSR sheet.
    """

    # The exact prompt — no explanations, just the value
    FIELD_PROMPT = (
        "Read the handwritten value in this image and return only the exact text. "
        "No explanations. No formatting. No additional text. "
        "Return only the detected value."
    )

    NUMERIC_PROMPT = (
        "Read the handwritten number in this image and return only the numeric value. "
        "No explanations. No formatting. No additional text. "
        "Return only the number. Include decimals if present."
    )

    def __init__(self):
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured. AI fallback disabled.")
            self.model = None
            return

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("Gemini AI service initialized")

    def is_available(self) -> bool:
        """Check if Gemini service is configured and available."""
        return self.model is not None

    def read_field(self, field_image: np.ndarray, is_numeric: bool = True) -> Dict:
        """
        Send a single field image to Gemini for handwriting recognition.

        Args:
            field_image: Cropped field image as numpy array
            is_numeric: If True, use numeric-specific prompt

        Returns:
            {"text": str, "confidence": float, "success": bool}
        """
        if not self.is_available():
            return {"text": "", "confidence": 0.0, "success": False, "error": "Gemini not configured"}

        try:
            start_time = time.time()

            # Convert numpy array to PIL Image
            if len(field_image.shape) == 2:
                # Grayscale
                pil_image = Image.fromarray(field_image)
            else:
                # BGR to RGB
                rgb = cv2.cvtColor(field_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb)

            # Select prompt
            prompt = self.NUMERIC_PROMPT if is_numeric else self.FIELD_PROMPT

            # Call Gemini
            response = self.model.generate_content([prompt, pil_image])

            elapsed_ms = int((time.time() - start_time) * 1000)

            if response and response.text:
                text = response.text.strip()
                logger.info(f"Gemini returned: '{text}' ({elapsed_ms}ms)")
                return {
                    "text": text,
                    "confidence": 0.90,  # Gemini results get a base confidence
                    "success": True,
                    "elapsed_ms": elapsed_ms
                }
            else:
                return {"text": "", "confidence": 0.0, "success": False, "error": "Empty response"}

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {"text": "", "confidence": 0.0, "success": False, "error": str(e)}

    def read_fields_batch(self, fields: Dict[str, np.ndarray],
                          numeric_fields: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Process multiple low-confidence fields through Gemini.

        Args:
            fields: Dict of {field_name: cropped_image}
            numeric_fields: List of field names that should be treated as numeric

        Returns:
            Dict of {field_name: {"text": str, "confidence": float, "success": bool}}
        """
        if not self.is_available():
            return {name: {"text": "", "confidence": 0.0, "success": False} for name in fields}

        if numeric_fields is None:
            # All DSR fields except duty_name and manager_name are numeric
            numeric_fields = []

        results = {}
        for field_name, field_image in fields.items():
            is_numeric = field_name not in ["manager_name", "date"] and "duty_name" not in field_name
            result = self.read_field(field_image, is_numeric=is_numeric)
            results[field_name] = result

            # Rate limiting — 100ms between calls
            time.sleep(0.1)

        return results


# Singleton
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
