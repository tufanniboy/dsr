"""
PaddleOCR engine wrapper.
Handles OCR initialization, field-level text extraction, and confidence scoring.
"""

from paddleocr import PaddleOCR
from typing import Dict, Optional, Tuple, List
import numpy as np
import logging

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Wrapper around PaddleOCR for field-level text extraction.
    Model is loaded once at startup and reused for all requests.
    """

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        logger.info("Initializing PaddleOCR engine...")
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            use_gpu=use_gpu,
            show_log=False,
            # Optimize for numeric/text fields
            det_db_thresh=0.3,
            det_db_box_thresh=0.5,
            rec_batch_num=6,
        )
        logger.info("PaddleOCR engine initialized successfully")

    def ocr_field(self, field_image: np.ndarray) -> Dict:
        """
        Run OCR on a single cropped field image.

        Returns:
            {
                "text": str,       # Extracted text
                "confidence": float # Confidence score 0-1
            }
        """
        try:
            results = self.ocr.ocr(field_image, cls=True)

            if not results or not results[0]:
                return {"text": "", "confidence": 0.0}

            # Combine all detected text regions in the field
            texts = []
            confidences = []

            for line in results[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, tuple) and len(text_info) >= 2:
                        text = str(text_info[0]).strip()
                        confidence = float(text_info[1])
                        if text:
                            texts.append(text)
                            confidences.append(confidence)

            if not texts:
                return {"text": "", "confidence": 0.0}

            # Join all text parts (for multi-region fields)
            combined_text = " ".join(texts)

            # Average confidence across all regions
            avg_confidence = sum(confidences) / len(confidences)

            return {
                "text": combined_text,
                "confidence": round(avg_confidence, 4)
            }

        except Exception as e:
            logger.error(f"OCR field extraction failed: {e}")
            return {"text": "", "confidence": 0.0}

    def ocr_fields(self, fields: Dict[str, np.ndarray]) -> Dict[str, Dict]:
        """
        Run OCR on multiple cropped field images.

        Args:
            fields: Dict of {field_name: cropped_image}

        Returns:
            Dict of {field_name: {"text": str, "confidence": float}}
        """
        results = {}

        for field_name, field_image in fields.items():
            result = self.ocr_field(field_image)
            results[field_name] = result
            logger.debug(f"Field '{field_name}': text='{result['text']}', confidence={result['confidence']}")

        return results

    def ocr_full_image(self, image: np.ndarray) -> List[Dict]:
        """
        Run OCR on a full image (for debugging/fallback only).
        Returns list of all detected text regions.
        """
        try:
            results = self.ocr.ocr(image, cls=True)

            if not results or not results[0]:
                return []

            detections = []
            for line in results[0]:
                if line and len(line) >= 2:
                    bbox = line[0]
                    text_info = line[1]
                    if isinstance(text_info, tuple) and len(text_info) >= 2:
                        detections.append({
                            "bbox": bbox,
                            "text": str(text_info[0]).strip(),
                            "confidence": float(text_info[1])
                        })

            return detections

        except Exception as e:
            logger.error(f"Full image OCR failed: {e}")
            return []

    @staticmethod
    def clean_numeric(text: str) -> str:
        """
        Clean OCR output that should be a number.
        Handles common OCR misreads (O→0, l→1, etc.)
        """
        if not text:
            return ""

        # Common character substitutions for numeric fields
        replacements = {
            'O': '0', 'o': '0',
            'l': '1', 'I': '1', 'i': '1',
            'S': '5', 's': '5',
            'B': '8',
            'Z': '2', 'z': '2',
            'g': '9', 'q': '9',
            ',': '',
            ' ': '',
            '-': '',
        }

        cleaned = ""
        for char in text.strip():
            if char.isdigit() or char == '.':
                cleaned += char
            elif char in replacements:
                cleaned += replacements[char]

        return cleaned
