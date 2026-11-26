"""
Tests for OpenCV Visual Feature Extractor on geometric shapes.
"""

import unittest
from PIL import Image, ImageDraw
from engine.visual_feature_extractor import VisualFeatureExtractor, HAS_OPENCV


class TestVisualFeatureExtractor(unittest.TestCase):
    def test_extract_contour_features_triangle(self):
        if not HAS_OPENCV:
            self.skipTest("OpenCV not available")

        # Create image with black triangle on white background
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.polygon([(100, 30), (30, 160), (170, 160)], fill=(0, 0, 0))

        feats = VisualFeatureExtractor.extract_contour_features(img)
        self.assertTrue(feats["available"])
        self.assertGreater(len(feats["options_features"]), 0)

        first_shape = feats["options_features"][0]
        self.assertEqual(first_shape["shape_type"], "Triangle")
        self.assertEqual(first_shape["vertices"], 3)
        self.assertGreater(first_shape["fill_percentage"], 5.0)

    def test_extract_contour_features_rectangle(self):
        if not HAS_OPENCV:
            self.skipTest("OpenCV not available")

        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([40, 60, 160, 120], fill=(0, 0, 0))

        feats = VisualFeatureExtractor.extract_contour_features(img)
        self.assertTrue(feats["available"])
        self.assertGreater(len(feats["options_features"]), 0)

        first_shape = feats["options_features"][0]
        self.assertIn(first_shape["shape_type"], ["Rectangle", "Square"])
        self.assertEqual(first_shape["vertices"], 4)

    def test_subregion_symmetry_analysis(self):
        if not HAS_OPENCV:
            self.skipTest("OpenCV not available")

        # Perfectly symmetric vertical shape
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([30, 20, 70, 80], fill=(0, 0, 0))

        box = [(0, 0, 100, 100)]
        feats = VisualFeatureExtractor.extract_contour_features(img, option_boxes=box)
        first_opt = feats["options_features"][0]
        self.assertEqual(first_opt["v_symmetry"], "High")


if __name__ == "__main__":
    unittest.main()
