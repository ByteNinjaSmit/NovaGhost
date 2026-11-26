"""
NovaGhost — Advanced Screenshot Processing & Option Position Detection Pipeline.
Performs non-destructive image enhancement, boundary detection, layout analysis,
and precise horizontal/vertical/grid option localization using OpenCV and PIL.
"""

import io
import math
import logging
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# Check OpenCV availability safely
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logger.warning("OpenCV/NumPy not available — running screenshot processor in PIL fallback mode.")





class ScreenshotProcessor:
    """Non-destructive image analyzer and preprocessor for visual intelligence."""

    @classmethod
    def enhance_image(cls, image: Image.Image) -> Image.Image:
        """
        Enhances contrast and sharpness non-destructively to maximize readability
        of small text, intricate diagrams, and fine non-verbal geometric shapes.
        """
        if image is None:
            return image

        enhanced = image.copy()
        # Ensure RGB mode
        if enhanced.mode != "RGB":
            enhanced = enhanced.convert("RGB")

        # Upscale if low-resolution (e.g. width < 600 or height < 300)
        w, h = enhanced.size
        if w < 600 or h < 300:
            scale = max(2.0, 800.0 / max(w, 1))
            new_w = int(w * scale)
            new_h = int(h * scale)
            enhanced = enhanced.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Contrast enhancement
        enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = enhancer.enhance(1.2)

        # Sharpness enhancement
        sharpener = ImageEnhance.Sharpness(enhanced)
        enhanced = sharpener.enhance(1.3)

        return enhanced

    @classmethod
    def assess_image_quality(cls, image: Image.Image) -> Dict[str, Any]:
        """
        Analyzes image for potential issues: blur, extreme low resolution, or cutoff.
        """
        quality = {
            "width": image.width if image else 0,
            "height": image.height if image else 0,
            "is_low_res": False,
            "is_blurry": False,
            "is_clear": True,
            "aspect_ratio": 1.0,
            "warning": None
        }
        if image is None:
            quality["is_clear"] = False
            quality["warning"] = "Image is null"
            return quality

        w, h = image.size
        quality["aspect_ratio"] = round(w / max(h, 1), 2)

        if w < 200 or h < 100:
            quality["is_low_res"] = True
            quality["is_clear"] = False
            quality["warning"] = f"Image resolution ({w}x{h}) is too low to guarantee accuracy"

        # Check blur using Laplacian variance if OpenCV available
        if HAS_OPENCV:
            try:
                np_img = np.array(image.convert("L"))
                variance = cv2.Laplacian(np_img, cv2.CV_64F).var()
                quality["blur_variance"] = round(variance, 2)
                if variance < 20.0 and (w > 300 and h > 200):
                    quality["is_blurry"] = True
                    quality["warning"] = "Image appears severely blurred or out of focus"
            except Exception as e:
                logger.debug(f"Blur calculation skipped: {e}")

        return quality

    @classmethod
    def detect_layout_and_options(
        cls,
        image: Image.Image
    ) -> Dict[str, Any]:
        """
        Detects option regions and spatial layout (horizontal, vertical, or 2x2/3x3 grid).
        Returns layout metadata and bounding boxes.
        """
        w, h = image.size
        result: Dict[str, Any] = {
            "layout": "horizontal",      # 'horizontal', 'vertical', 'grid'
            "grid_rows": 1,
            "grid_cols": 4,
            "detected_options": [],      # List of (x1, y1, x2, y2)
            "confidence": 0.8
        }

        if not HAS_OPENCV:
            # Fallback heuristic based on aspect ratio
            if w > h * 2.2:
                result["layout"] = "horizontal"
                result["grid_cols"] = 4
            elif h > w * 1.5:
                result["layout"] = "vertical"
                result["grid_rows"] = 4
                result["grid_cols"] = 1
            else:
                result["layout"] = "grid"
                result["grid_rows"] = 2
                result["grid_cols"] = 2
            return result

        try:
            cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Edge detection to identify candidate option boxes
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            candidate_boxes = []
            min_area = (w * h) * 0.01   # At least 1% of total image
            max_area = (w * h) * 0.45   # At most 45% of total image

            for cnt in contours:
                x, y, bw, bh = cv2.boundingRect(cnt)
                area = bw * bh
                if min_area <= area <= max_area and bw > 30 and bh > 30:
                    candidate_boxes.append((x, y, x + bw, y + bh))

            # Sort candidate boxes if we found between 3 and 12 candidate options
            if 3 <= len(candidate_boxes) <= 12:
                # Determine if predominantly horizontal or vertical
                centers_x = [(box[0] + box[2]) // 2 for box in candidate_boxes]
                centers_y = [(box[1] + box[3]) // 2 for box in candidate_boxes]

                var_x = float(np.var(centers_x))
                var_y = float(np.var(centers_y))

                if len(candidate_boxes) in (4, 9) and abs(var_x - var_y) < (w * h * 0.05):
                    # Likely a 2x2 or 3x3 grid
                    side = int(math.isqrt(len(candidate_boxes)))
                    result["layout"] = "grid"
                    result["grid_rows"] = side
                    result["grid_cols"] = side
                elif var_x > var_y * 1.5:
                    result["layout"] = "horizontal"
                    result["grid_cols"] = len(candidate_boxes)
                    result["grid_rows"] = 1
                else:
                    result["layout"] = "vertical"
                    result["grid_rows"] = len(candidate_boxes)
                    result["grid_cols"] = 1

                # Sort reading-order: top-to-bottom, left-to-right
                candidate_boxes.sort(key=lambda b: (b[1] // (h // max(result["grid_rows"], 1)), b[0]))
                result["detected_options"] = candidate_boxes
            else:
                # Default aspect ratio heuristic
                if w >= h * 1.8:
                    result["layout"] = "horizontal"
                    result["grid_cols"] = 4
                elif h >= w * 1.6:
                    result["layout"] = "vertical"
                    result["grid_rows"] = 4
                    result["grid_cols"] = 1
                else:
                    result["layout"] = "grid"
                    result["grid_rows"] = 2
                    result["grid_cols"] = 2

        except Exception as e:
            logger.debug(f"Option boundary detection exception: {e}")

        return result

    @classmethod
    def crop_option_subimages(
        cls,
        image: Image.Image,
        boxes: List[Tuple[int, int, int, int]]
    ) -> List[Image.Image]:
        """Crops out individual detected option sub-images for detailed verification."""
        crops = []
        for box in boxes:
            try:
                sub = image.crop(box)
                crops.append(sub)
            except Exception as e:
                logger.debug(f"Failed to crop box {box}: {e}")
        return crops
