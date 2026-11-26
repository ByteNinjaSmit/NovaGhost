"""
NovaGhost — Perceptual Hashing & Zero-Latency Cache Engine.
Computes 128-bit perceptual image hashes (dHash + aHash) and serves cached results
in <10ms for identical or near-identical question captures.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class PerceptualHashCache:
    """Zero-latency perceptual image cache with Hamming distance matching."""

    def __init__(self, cache_file: Optional[Path] = None, max_entries: int = 500, max_distance: int = 3):
        self.cache_file = cache_file or (Path.home() / ".novaghost" / "cache" / "image_cache.json")
        self.max_entries = max_entries
        self.max_distance = max_distance
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
        except Exception as e:
            logger.debug(f"Could not load perceptual cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save perceptual cache: {e}")

    @classmethod
    def compute_dhash(cls, image: Image.Image, hash_size: int = 8) -> int:
        """
        Computes Difference Hash (dHash) by comparing gradient between adjacent horizontal pixels.
        Returns integer hash representation.
        """
        # Resize to (width+1, height) grayscale
        resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
        pixels = list(resized.getdata())
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                idx = row * (hash_size + 1) + col
                diff.append(pixels[idx] > pixels[idx + 1])

        # Convert boolean list to integer
        hash_val = 0
        for bit in diff:
            hash_val = (hash_val << 1) | (1 if bit else 0)
        return hash_val

    @classmethod
    def compute_ahash(cls, image: Image.Image, hash_size: int = 8) -> int:
        """
        Computes Average Hash (aHash) by comparing pixels to mean luminance.
        """
        resized = image.convert("L").resize((hash_size, hash_size), Image.Resampling.BILINEAR)
        pixels = list(resized.getdata())
        avg = sum(pixels) / len(pixels) if pixels else 0
        hash_val = 0
        for p in pixels:
            hash_val = (hash_val << 1) | (1 if p > avg else 0)
        return hash_val

    @classmethod
    def compute_combined_hash(cls, image: Image.Image) -> str:
        """Computes combined hash incorporating dHash, aHash, and mean luminance."""
        d = cls.compute_dhash(image)
        a = cls.compute_ahash(image)
        resized = image.convert("L").resize((8, 8), Image.Resampling.BILINEAR)
        mean_val = int(sum(resized.getdata()) / 64)
        return f"{mean_val:02x}{d:016x}{a:016x}"

    @classmethod
    def hamming_distance(cls, hash1_hex: str, hash2_hex: str) -> int:
        """Computes Hamming distance between two hexadecimal hashes."""
        try:
            int1 = int(hash1_hex, 16)
            int2 = int(hash2_hex, 16)
            xor_val = int1 ^ int2
            # bit_count is standard in Python 3.10+
            return xor_val.bit_count()
        except Exception:
            return 999

    def lookup(self, image: Image.Image) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Checks if an image (or near-identical match within Hamming distance) exists in cache.
        Returns (formatted_text, answer_dict) or None.
        """
        if not self._cache or image is None:
            return None

        query_hash = self.compute_combined_hash(image)

        # 1. Exact match
        if query_hash in self._cache:
            entry = self._cache[query_hash]
            entry["last_accessed"] = time.time()
            return entry["formatted_text"], entry.get("structured_data", {})

        # 2. Near-match within max_distance
        best_match = None
        min_dist = self.max_distance + 1

        for cached_hash, entry in self._cache.items():
            dist = self.hamming_distance(query_hash, cached_hash)
            if dist <= self.max_distance and dist < min_dist:
                min_dist = dist
                best_match = entry

        if best_match:
            best_match["last_accessed"] = time.time()
            logger.info(f"Perceptual cache hit (Hamming distance: {min_dist})")
            return best_match["formatted_text"], best_match.get("structured_data", {})

        return None

    def store(self, image: Image.Image, formatted_text: str, structured_data: Optional[Dict[str, Any]] = None) -> None:
        """Stores image result in cache."""
        if image is None or not formatted_text:
            return

        img_hash = self.compute_combined_hash(image)

        # Prune oldest if exceeds max_entries
        if len(self._cache) >= self.max_entries:
            oldest_key = min(self._cache, key=lambda k: self._cache[k].get("last_accessed", 0))
            del self._cache[oldest_key]

        self._cache[img_hash] = {
            "formatted_text": formatted_text,
            "structured_data": structured_data or {},
            "timestamp": time.time(),
            "last_accessed": time.time()
        }
        self._save_cache()

    def clear(self) -> None:
        self._cache.clear()
        self._save_cache()


_global_cache_singleton: Optional[PerceptualHashCache] = None

def get_perceptual_cache() -> PerceptualHashCache:
    global _global_cache_singleton
    if _global_cache_singleton is None:
        _global_cache_singleton = PerceptualHashCache()
    return _global_cache_singleton
