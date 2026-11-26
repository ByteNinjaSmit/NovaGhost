"""
Tests for screenshot processor, image enhancement, and layout assessment.
"""

import unittest
from PIL import Image, ImageDraw
from engine.screenshot_processor import ScreenshotProcessor


class TestScreenshotProcessor(unittest.TestCase):
    def test_assess_image_quality_normal(self):
        # Create normal test image
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "Test Question Text", fill=(0, 0, 0))

        quality = ScreenshotProcessor.assess_image_quality(img)
        self.assertTrue(quality["is_clear"])
        self.assertFalse(quality["is_low_res"])
        self.assertIsNone(quality["warning"])

    def test_assess_image_quality_low_res(self):
        # Extremely small image
        img = Image.new("RGB", (150, 80), color=(255, 255, 255))
        quality = ScreenshotProcessor.assess_image_quality(img)
        self.assertFalse(quality["is_clear"])
        self.assertTrue(quality["is_low_res"])
        self.assertIsNotNone(quality["warning"])

    def test_enhance_image(self):
        img = Image.new("RGB", (400, 200), color=(200, 200, 200))
        enhanced = ScreenshotProcessor.enhance_image(img)
        self.assertIsNotNone(enhanced)
        # Should upscale low dimensions to at least 800 width
        self.assertGreaterEqual(enhanced.width, 800)

    def test_detect_layout_horizontal(self):
        # Create wide aspect ratio image
        img = Image.new("RGB", (1200, 300), color=(255, 255, 255))
        res = ScreenshotProcessor.detect_layout_and_options(img)
        self.assertIn("layout", res)
        self.assertEqual(res["layout"], "horizontal")

    def test_detect_layout_vertical(self):
        # Create tall aspect ratio image
        img = Image.new("RGB", (300, 900), color=(255, 255, 255))
        res = ScreenshotProcessor.detect_layout_and_options(img)
        self.assertEqual(res["layout"], "vertical")


if __name__ == "__main__":
    unittest.main()
