"""
OpenCV image preprocessing pipeline for DSR sheet scanning.
Handles document detection, perspective correction, and image enhancement.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Complete image preprocessing pipeline:
    1. Document boundary detection
    2. Perspective correction (four-point transform)
    3. Image enhancement (brightness, contrast, noise, sharpening)
    """

    def __init__(self):
        self.target_width = 2480   # A4 at 300 DPI width
        self.target_height = 3508  # A4 at 300 DPI height

    def process(self, image_bytes: bytes) -> Tuple[np.ndarray, dict]:
        """
        Run the full preprocessing pipeline on raw image bytes.
        Returns (processed_image, metadata).
        """
        # Decode image from bytes
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image")

        metadata = {
            "original_width": image.shape[1],
            "original_height": image.shape[0],
            "steps": []
        }

        # Step 1: Resize if too large (preserve aspect ratio)
        image = self._resize_if_needed(image)
        metadata["steps"].append("resize")

        # Step 2: Detect document boundaries
        corners = self._detect_document(image)
        metadata["steps"].append("detect_boundaries")

        # Step 3: Perspective correction
        if corners is not None:
            image = self._perspective_transform(image, corners)
            metadata["perspective_corrected"] = True
            metadata["steps"].append("perspective_correction")
        else:
            metadata["perspective_corrected"] = False
            logger.warning("Could not detect document boundaries, skipping perspective correction")

        # Step 4: Enhance image
        image = self._enhance_image(image)
        metadata["steps"].append("enhancement")

        metadata["final_width"] = image.shape[1]
        metadata["final_height"] = image.shape[0]

        return image, metadata

    def _resize_if_needed(self, image: np.ndarray, max_dim: int = 4000) -> np.ndarray:
        """Resize image if any dimension exceeds max_dim."""
        h, w = image.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return image

    def _detect_document(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect the DSR sheet boundaries using edge detection and contour analysis.
        Returns the 4 corner points or None if not found.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate to close gaps in edges
        kernel = np.ones((5, 5), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)
        edges = cv2.erode(edges, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Sort by area, get the largest
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for contour in contours[:5]:
            # Approximate the contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            # If we found a quadrilateral
            if len(approx) == 4:
                # Check if it's large enough (at least 20% of image area)
                area = cv2.contourArea(approx)
                image_area = image.shape[0] * image.shape[1]
                if area > image_area * 0.2:
                    return approx.reshape(4, 2)

        return None

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points as: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype="float32")

        # Sum of coordinates: smallest = top-left, largest = bottom-right
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # Difference: smallest = top-right, largest = bottom-left
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _perspective_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Apply four-point perspective transform to get a top-down view."""
        rect = self._order_points(pts.astype("float32"))
        (tl, tr, br, bl) = rect

        # Compute the width of the new image
        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_width = max(int(width_a), int(width_b))

        # Compute the height of the new image
        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_height = max(int(height_a), int(height_b))

        # Destination points
        dst = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype="float32")

        # Compute perspective transform matrix and apply
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (max_width, max_height))

        return warped

    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply image enhancements for better OCR accuracy:
        - Brightness correction via CLAHE
        - Contrast enhancement
        - Noise reduction
        - Sharpening
        """
        # Convert to LAB for better brightness handling
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # Merge back
        lab = cv2.merge([l, a, b])
        image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Noise reduction
        image = cv2.fastNlMeansDenoisingColored(image, None, 6, 6, 7, 21)

        # Sharpening with unsharp mask
        gaussian = cv2.GaussianBlur(image, (0, 0), 3)
        image = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)

        return image

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale for OCR."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def crop_field(self, image: np.ndarray, x: int, y: int, width: int, height: int,
                   padding: int = 5) -> np.ndarray:
        """
        Crop a specific field region from the image.
        Adds padding to capture edge characters.
        """
        h, w = image.shape[:2]

        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(w, x + width + padding)
        y2 = min(h, y + height + padding)

        cropped = image[y1:y2, x1:x2]

        # Enhance the cropped field for better OCR
        cropped = self._enhance_field(cropped)

        return cropped

    def _enhance_field(self, field_image: np.ndarray) -> np.ndarray:
        """Additional enhancement for individual field crops."""
        # Convert to grayscale if needed
        if len(field_image.shape) == 3:
            gray = cv2.cvtColor(field_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = field_image.copy()

        # Adaptive thresholding for clean black-on-white
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # Slight dilation to make handwriting bolder
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)

        return binary

    def encode_to_bytes(self, image: np.ndarray, format: str = ".jpg") -> bytes:
        """Encode numpy image back to bytes."""
        success, buffer = cv2.imencode(format, image)
        if not success:
            raise ValueError("Failed to encode image")
        return buffer.tobytes()
