"""
Tests for Perceptual Hash Cache Engine.
"""

import unittest
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from engine.perceptual_cache import PerceptualHashCache


class TestPerceptualCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_file = Path(self.temp_dir.name) / "test_cache.json"
        self.cache = PerceptualHashCache(cache_file=self.cache_file, max_entries=10, max_distance=3)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_hash_computation(self):
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        dhash = PerceptualHashCache.compute_dhash(img)
        ahash = PerceptualHashCache.compute_ahash(img)
        comb = PerceptualHashCache.compute_combined_hash(img)
        self.assertIsInstance(dhash, int)
        self.assertIsInstance(ahash, int)
        self.assertEqual(len(comb), 34)

    def test_cache_store_and_exact_lookup(self):
        img = Image.new("RGB", (120, 80), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Sample Q", fill=(0, 0, 0))

        # Store
        self.cache.store(img, "CORRECT OPTION: B\n\nFULL ANSWER: 45.75", {"option_label": "B"})

        # Lookup
        hit = self.cache.lookup(img)
        self.assertIsNotNone(hit)
        text, data = hit
        self.assertIn("CORRECT OPTION: B", text)
        self.assertEqual(data.get("option_label"), "B")

    def test_cache_near_match(self):
        img1 = Image.new("RGB", (120, 80), color=(200, 200, 200))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([20, 20, 60, 60], fill=(0, 0, 0))

        # img2 is slightly perturbed (1 extra small pixel)
        img2 = img1.copy()
        img2.putpixel((1, 1), (198, 198, 198))

        self.cache.store(img1, "CORRECT OPTION: C\n\nFULL ANSWER: 125", {"option_label": "C"})
        hit = self.cache.lookup(img2)
        self.assertIsNotNone(hit)
        text, _ = hit
        self.assertIn("CORRECT OPTION: C", text)

    def test_cache_miss(self):
        img_white = Image.new("RGB", (100, 100), color=(255, 255, 255))
        img_black = Image.new("RGB", (100, 100), color=(0, 0, 0))

        self.cache.store(img_white, "ANSWER WHITE")
        hit = self.cache.lookup(img_black)
        self.assertIsNone(hit)


if __name__ == "__main__":
    unittest.main()
