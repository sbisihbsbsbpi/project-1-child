"""
Browser and stealth configuration constants.

Extracted from screenshot_service.py (lines 77-120)
Part of Week 2 refactoring.
"""

# ========================================
# 🎯 9 STEALTH SOLUTIONS - USER AGENTS
# ========================================
# Solution #2: Randomize User-Agent Strings
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# ========================================
# 🎯 9 STEALTH SOLUTIONS - VIEWPORTS
# ========================================
# Solution #6: Adjust Viewport Size and Device Emulation
VIEWPORTS = [
    # Desktop viewports
    {"width": 1920, "height": 1080, "device_type": "desktop"},  # Full HD
    {"width": 1366, "height": 768, "device_type": "desktop"},  # Laptop
    {"width": 1536, "height": 864, "device_type": "desktop"},  # HD+
    {"width": 1440, "height": 900, "device_type": "desktop"},  # MacBook
    {"width": 2560, "height": 1440, "device_type": "desktop"},  # 2K
    # Mobile viewports
    {"width": 375, "height": 667, "device_type": "mobile"},  # iPhone 8
    {"width": 414, "height": 896, "device_type": "mobile"},  # iPhone 11
    {"width": 390, "height": 844, "device_type": "mobile"},  # iPhone 12/13
    {"width": 412, "height": 915, "device_type": "mobile"},  # Pixel 5
    # Tablet viewports
    {"width": 768, "height": 1024, "device_type": "tablet"},  # iPad
    {"width": 820, "height": 1180, "device_type": "tablet"},  # iPad Air
]

__all__ = ["USER_AGENTS", "VIEWPORTS"]
