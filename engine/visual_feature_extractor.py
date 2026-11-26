"""
NovaGhost — OpenCV Visual Feature Extraction Engine.
Extracts geometric vertices, polygon approximations, fill ratios, symmetry,
and orientation angles from non-verbal figures and option boxes.
"""

import math
import logging
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class VisualFeatureExtractor:
    """Extracts deterministic geometric and structural visual features from images."""

    @classmethod
    def extract_contour_features(cls, image: Image.Image, option_boxes: Optional[List[Tuple[int, int, int, int]]] = None) -> Dict[str, Any]:
        """
        Extracts structural features from the image or specific option sub-regions.
        Returns a dictionary of visual facts and a prompt-ready summary.
        """
        if not HAS_OPENCV or image is None:
            return {"available": False, "summary": "OpenCV not available for contour extraction."}

        try:
            cv_img = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Binarization
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            results = {
                "available": True,
                "overall_dark_ratio": round(float(np.count_nonzero(thresh) / thresh.size), 3),
                "options_features": [],
                "summary": ""
            }

            if option_boxes:
                for i, box in enumerate(option_boxes):
                    x1, y1, x2, y2 = box
                    crop = thresh[max(0, y1):min(thresh.shape[0], y2), max(0, x1):min(thresh.shape[1], x2)]
                    if crop.size == 0:
                        continue
                    feat = cls._analyze_subregion(crop, f"Option {i+1}")
                    results["options_features"].append(feat)
            else:
                # Find prominent external contours in the image
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contours = sorted(contours, key=cv2.contourArea, reverse=True)[:8]
                for i, cnt in enumerate(contours):
                    if cv2.contourArea(cnt) > (thresh.size * 0.005):
                        feat = cls._analyze_contour(cnt, thresh, f"Shape {i+1}")
                        results["options_features"].append(feat)

            # Generate prompt-ready summary
            summary_lines = []
            for f in results["options_features"]:
                summary_lines.append(
                    f"{f['label']}: {f['shape_type']} ({f['vertices']} vertices), "
                    f"Fill: {f['fill_percentage']}%, Orientation: {f['orientation_deg']}°, "
                    f"V-Symmetry: {f['v_symmetry']}"
                )
            results["summary"] = "; ".join(summary_lines)
            return results

        except Exception as e:
            logger.debug(f"Visual feature extraction error: {e}")
            return {"available": False, "summary": f"Feature extraction skipped: {e}"}

    @classmethod
    def _analyze_subregion(cls, sub_img: np.ndarray, label: str) -> Dict[str, Any]:
        h, w = sub_img.shape
        total_pixels = max(1, h * w)
        dark_pixels = np.count_nonzero(sub_img)
        fill_pct = round((dark_pixels / total_pixels) * 100, 1)

        # Symmetry test
        v_sym = cls._calc_vertical_symmetry(sub_img)
        h_sym = cls._calc_horizontal_symmetry(sub_img)

        # Contours within subregion
        contours, _ = cv2.findContours(sub_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            peri = cv2.arcLength(largest, True)
            approx = cv2.approxPolyDP(largest, 0.04 * peri, True)
            vertices = len(approx)
            shape_type = cls._classify_vertices(vertices, largest)
            orient = cls._calc_orientation(largest)
        else:
            vertices = 0
            shape_type = "Unknown"
            orient = 0.0

        return {
            "label": label,
            "shape_type": shape_type,
            "vertices": vertices,
            "fill_percentage": fill_pct,
            "orientation_deg": orient,
            "v_symmetry": "High" if v_sym > 0.85 else ("Medium" if v_sym > 0.65 else "Low"),
            "h_symmetry": "High" if h_sym > 0.85 else ("Medium" if h_sym > 0.65 else "Low")
        }

    @classmethod
    def _analyze_contour(cls, cnt: np.ndarray, base_img: np.ndarray, label: str) -> Dict[str, Any]:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        vertices = len(approx)
        shape_type = cls._classify_vertices(vertices, cnt)
        orient = cls._calc_orientation(cnt)

        # Calculate bounding fill
        x, y, w, h = cv2.boundingRect(cnt)
        crop = base_img[y:y+h, x:x+w]
        fill_pct = round((np.count_nonzero(crop) / max(1, crop.size)) * 100, 1)

        return {
            "label": label,
            "shape_type": shape_type,
            "vertices": vertices,
            "fill_percentage": fill_pct,
            "orientation_deg": orient,
            "v_symmetry": "N/A",
            "h_symmetry": "N/A"
        }

    @classmethod
    def _classify_vertices(cls, v: int, cnt: np.ndarray) -> str:
        if v == 3:
            return "Triangle"
        if v == 4:
            # Check aspect ratio for square vs rectangle
            x, y, w, h = cv2.boundingRect(cnt)
            ratio = float(w) / max(h, 1)
            return "Square" if 0.9 <= ratio <= 1.1 else "Rectangle"
        if v == 5:
            return "Pentagon"
        if v == 6:
            return "Hexagon"
        if v > 6:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            if perimeter > 0:
                circularity = (4 * math.pi * area) / (perimeter * perimeter)
                if circularity > 0.75:
                    return "Circle"
            return f"{v}-gon"
        return "Complex"

    @classmethod
    def _calc_orientation(cls, cnt: np.ndarray) -> float:
        """Calculates primary orientation angle (0° to 180°) using second-order moments."""
        m = cv2.moments(cnt)
        if m["mu20"] == m["mu02"]:
            return 0.0
        theta = 0.5 * math.atan2(2 * m["mu11"], m["mu20"] - m["mu02"])
        deg = round(math.degrees(theta), 1)
        return deg if deg >= 0 else deg + 180

    @classmethod
    def _calc_vertical_symmetry(cls, img: np.ndarray) -> float:
        """Compares left half with horizontally flipped right half."""
        h, w = img.shape
        mid = w // 2
        if mid < 2:
            return 1.0
        left = img[:, :mid]
        right = img[:, -mid:]
        right_flipped = cv2.flip(right, 1)
        overlap = np.count_nonzero(left == right_flipped)
        return float(overlap / max(1, left.size))

    @classmethod
    def _calc_horizontal_symmetry(cls, img: np.ndarray) -> float:
        """Compares top half with vertically flipped bottom half."""
        h, w = img.shape
        mid = h // 2
        if mid < 2:
            return 1.0
        top = img[:mid, :]
        bottom = img[-mid:, :]
        bottom_flipped = cv2.flip(bottom, 0)
        overlap = np.count_nonzero(top == bottom_flipped)
        return float(overlap / max(1, top.size))
