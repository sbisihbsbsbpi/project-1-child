"""
Quality Checker for Screenshots
Detects blank pages, errors, and quality issues
"""

from PIL import Image
import os
from typing import Dict, List


class QualityChecker:
    def __init__(self):
        self.min_file_size = 5000  # 5KB minimum
        self.min_brightness = 10  # Minimum average brightness
        self.max_brightness = 250  # Maximum average brightness (detect blank white pages)

    async def check(self, screenshot_path: str) -> Dict:
        """
        Check screenshot quality
        
        Returns:
            {
                "passed": bool,
                "score": float (0-100),
                "issues": List[str]
            }
        """
        issues = []
        score = 100.0

        # Check if file exists
        if not os.path.exists(screenshot_path):
            return {
                "passed": False,
                "score": 0.0,
                "issues": ["File does not exist"]
            }

        # Check file size
        file_size = os.path.getsize(screenshot_path)
        if file_size < self.min_file_size:
            issues.append(f"File too small ({file_size} bytes)")
            score -= 30

        try:
            # Open image
            img = Image.open(screenshot_path)

            # Check dimensions
            width, height = img.size
            if width < 100 or height < 100:
                issues.append(f"Image too small ({width}x{height})")
                score -= 30

            # Check brightness (detect blank pages)
            brightness = self._calculate_brightness(img)

            if brightness < self.min_brightness:
                issues.append(f"Image too dark (brightness: {brightness:.1f})")
                score -= 25

            if brightness > self.max_brightness:
                issues.append(f"Image too bright/blank (brightness: {brightness:.1f})")
                score -= 40

            # Check for mostly single color (blank page detection)
            if self._is_mostly_single_color(img):
                issues.append("Image appears to be blank or single color")
                score -= 35

        except Exception as e:
            issues.append(f"Error analyzing image: {str(e)}")
            score = 0.0

        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, score))

        return {
            "passed": score >= 60.0,  # Only check score, not issues
            "score": score,
            "issues": issues
        }

    def _calculate_brightness(self, img: Image) -> float:
        """Calculate average brightness of image"""
        # Convert to grayscale
        grayscale = img.convert('L')

        # Calculate average pixel value
        pixels = list(grayscale.getdata())
        avg_brightness = sum(pixels) / len(pixels)

        return avg_brightness

    def _is_mostly_single_color(self, img: Image, threshold: float = 0.95) -> bool:
        """Check if image is mostly a single color"""
        # Resize to small size for faster processing
        small_img = img.resize((50, 50))

        # Get colors
        colors = small_img.getcolors(maxcolors=2500)

        if not colors:
            return False

        # Sort by frequency
        colors.sort(reverse=True, key=lambda x: x[0])

        # Check if most common color dominates
        total_pixels = 50 * 50
        most_common_count = colors[0][0]

        return (most_common_count / total_pixels) > threshold
