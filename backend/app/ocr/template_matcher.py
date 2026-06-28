"""
Template-based field extraction for DSR sheets.
Maps predefined coordinate regions to field names and crops each field.
"""

import json
import os
from typing import Dict, Optional, List
import numpy as np
import logging

from app.ocr.preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

# Default template directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")


class TemplateMatcher:
    """
    Handles template-based field extraction from DSR sheets.
    Uses coordinate mapping to crop individual fields from the preprocessed image.
    """

    def __init__(self, preprocessor: Optional[ImagePreprocessor] = None):
        self.preprocessor = preprocessor or ImagePreprocessor()
        self._templates_cache: Dict[str, dict] = {}

    def load_template(self, template_id: str = "dsr_default") -> dict:
        """Load a template definition from JSON file or cache."""
        if template_id in self._templates_cache:
            return self._templates_cache[template_id]

        template_path = os.path.join(TEMPLATES_DIR, f"{template_id}.json")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = json.load(f)

        self._templates_cache[template_id] = template
        logger.info(f"Loaded template: {template_id}")

        return template

    def load_template_from_json(self, coordinates: dict) -> dict:
        """Load template from a JSON dict (from database)."""
        return coordinates

    def extract_fields(self, image: np.ndarray, template: dict) -> Dict[str, np.ndarray]:
        """
        Crop all fields from the image using template coordinates.

        Args:
            image: Preprocessed full-page image
            template: Template dict with field coordinates

        Returns:
            Dict of {field_name: cropped_image_array}
        """
        fields = {}
        image_h, image_w = image.shape[:2]

        # Get template reference dimensions for scaling
        ref_width = template.get("reference_width", image_w)
        ref_height = template.get("reference_height", image_h)

        # Calculate scale factors
        scale_x = image_w / ref_width
        scale_y = image_h / ref_height

        field_defs = template.get("fields", {})

        for field_name, coords in field_defs.items():
            try:
                # Scale coordinates to actual image size
                x = int(coords["x"] * scale_x)
                y = int(coords["y"] * scale_y)
                w = int(coords["width"] * scale_x)
                h = int(coords["height"] * scale_y)

                # Crop the field with padding
                cropped = self.preprocessor.crop_field(image, x, y, w, h, padding=4)

                if cropped.size > 0:
                    fields[field_name] = cropped
                else:
                    logger.warning(f"Empty crop for field: {field_name}")

            except Exception as e:
                logger.error(f"Failed to crop field '{field_name}': {e}")

        logger.info(f"Extracted {len(fields)} fields from template")
        return fields

    def get_field_list(self, template: dict) -> List[str]:
        """Get the list of all field names in a template."""
        return list(template.get("fields", {}).keys())

    @staticmethod
    def get_duty_fields() -> List[str]:
        """Get the standard list of fields within each duty."""
        return [
            "duty_name",
            "start_reading",
            "end_reading",
            "testing",
            "rate",
            "total_amount",
            "card",
            "upi",
            "expenses",
            "credit",
            "total_cash_in_hand",
            "short_amount"
        ]

    @staticmethod
    def parse_field_name(field_name: str) -> dict:
        """
        Parse a template field name into components.
        e.g., 'duty_1_start_reading' → {'duty': 1, 'field': 'start_reading'}
        """
        parts = field_name.split("_", 2)

        if parts[0] == "duty" and len(parts) >= 3:
            try:
                duty_num = int(parts[1])
                field = "_".join(parts[2:])
                return {"duty": duty_num, "field": field}
            except ValueError:
                pass

        # Header fields (manager_name, date, etc.)
        return {"duty": None, "field": field_name}
