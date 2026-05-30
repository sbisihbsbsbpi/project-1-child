"""
Camoufox browser configuration generator.

Extracted from screenshot_service.py (lines 992-1145)
Part of Week 3 refactoring.

Provides advanced fingerprint configuration for Camoufox browser with:
- Screen and window properties
- Canvas anti-fingerprinting
- Audio context spoofing
- Navigator properties
- Realistic cursor movement settings
"""

import random
import logging

logger = logging.getLogger(__name__)


def generate_camoufox_config(use_stealth: bool = False) -> dict:
    """
    Generate comprehensive Camoufox configuration for maximum stealth.
    
    Camoufox can fully spoof all properties at C++ source level (undetectable).
    
    Args:
        use_stealth: Enable extra stealth features (slower cursor, more history)
        
    Returns:
        Dictionary of Camoufox configuration options
        
    Example:
        config = generate_camoufox_config(use_stealth=True)
        browser = await AsyncCamoufox(config=config, ...)
    """
    # Common screen resolutions with realistic distribution
    screen_configs = [
        {'width': 1920, 'height': 1080, 'dpr': 1.0, 'name': 'Full HD'},  # 22% market share
        {'width': 1920, 'height': 1080, 'dpr': 1.0, 'name': 'Full HD'},  # Duplicate for higher probability
        {'width': 1366, 'height': 768, 'dpr': 1.0, 'name': 'Laptop HD'},  # 15% market share
        {'width': 2560, 'height': 1440, 'dpr': 1.0, 'name': '2K/QHD'},  # 8% market share
        {'width': 1920, 'height': 1080, 'dpr': 2.0, 'name': 'Retina FHD'},  # MacBook Pro
        {'width': 1536, 'height': 864, 'dpr': 1.0, 'name': 'Laptop HD+'},  # 4% market share
    ]
    screen_config = random.choice(screen_configs)
    screen_width = screen_config['width']
    screen_height = screen_config['height']
    device_pixel_ratio = screen_config['dpr']
    
    # Calculate window dimensions (outer = inner + browser chrome)
    # Windows: +16px scrollbar width, +85px chrome height (title bar + toolbar)
    inner_width = screen_width
    inner_height = screen_height
    outer_width = inner_width + 16  # Scrollbar width
    outer_height = inner_height + 85  # Title bar + toolbar + status bar
    
    # Available screen area (subtract taskbar)
    # Windows taskbar: typically 40-60px
    avail_height = screen_height - random.randint(40, 60)
    
    config = {
        # ========================================
        # SCREEN PROPERTIES (Priority 1: CRITICAL)
        # ========================================
        'screen.width': screen_width,
        'screen.height': screen_height,
        'screen.availWidth': screen_width,  # Usually matches width
        'screen.availHeight': avail_height,  # Screen height - taskbar
        'screen.colorDepth': 24,  # True Color (16.7M colors) - most common
        'screen.pixelDepth': 24,  # Must match colorDepth (synonymous)
        
        # ========================================
        # WINDOW PROPERTIES (Priority 1: CRITICAL)
        # ========================================
        'window.innerWidth': inner_width,  # Viewport width
        'window.innerHeight': inner_height,  # Viewport height
        'window.outerWidth': outer_width,  # Browser window width (inner + scrollbar)
        'window.outerHeight': outer_height,  # Browser window height (inner + chrome)
        'window.devicePixelRatio': device_pixel_ratio,  # Physical pixels per CSS pixel
        
        # Window position (Priority 2: MEDIUM)
        # Randomize to avoid "always maximized" pattern
        'window.screenX': random.choice([0, 0, 0, random.randint(10, 100)]),  # 75% maximized
        'window.screenY': random.choice([0, 0, 0, random.randint(10, 100)]),  # 75% maximized
        
        # Browsing history (Priority 2: MEDIUM)
        # Randomize to simulate realistic browsing session
        'window.history.length': random.randint(1, 10),  # 1 = direct, 10 = browsing session
        
        # ========================================
        # CANVAS ANTI-FINGERPRINTING (Priority 2: MEDIUM)
        # ========================================
        # Camoufox uses patched Skia rendering engine (NOT JavaScript noise injection)
        # This modifies anti-aliasing at C++ level to mimic real hardware differences
        'canvas:aaOffset': random.randint(1, 3),  # Offset pixel transparency (1-3 is subtle)
        'canvas:aaCapOffset': True,  # Clamp alpha to 0-255 (prevent wrap-around)
        
        # ========================================
        # GEOLOCATION & TIMEZONE (Priority 2: MEDIUM)
        # ========================================
        'geolocation:latitude': 40.7128,  # New York City latitude
        'geolocation:longitude': -74.0060,  # New York City longitude
        'timezone': 'America/New_York',  # TZ timezone (affects Date() and Intl API)
        
        # ========================================
        # LOCALE/INTL (Priority 2: MEDIUM)
        # ========================================
        'locale:language': 'en',  # Language code (ISO 639-1)
        'locale:region': 'US',  # Region code (ISO 3166-1 alpha-2)
        
        # ========================================
        # HTTP HEADERS (Priority 2: MEDIUM)
        # ========================================
        'headers.Accept-Language': 'en-US,en;q=0.9',  # Match locale (en-US)
        'headers.Accept-Encoding': 'gzip, deflate, br',  # Standard Firefox encoding
        
        # ========================================
        # AUDIOCONTEXT (Priority 2: MEDIUM)
        # ========================================
        'AudioContext:sampleRate': random.choice([44100, 48000]),  # 44.1 kHz (CD) or 48 kHz (most common)
        'AudioContext:outputLatency': round(random.uniform(0.01, 0.02), 3),  # 10-20ms (typical range)
        'AudioContext:maxChannelCount': 2,  # Stereo (standard for desktop)
        
        # ========================================
        # MISCELLANEOUS (Priority 1: CRITICAL)
        # ========================================
        'pdfViewerEnabled': True,  # ✅ CRITICAL - All modern browsers have PDF viewer
        
        # ========================================
        # NAVIGATOR PROPERTIES
        # ========================================
        'navigator.hardwareConcurrency': random.randint(4, 16),  # Randomize CPU cores
        'navigator.maxTouchPoints': 0,  # Desktop = 0, mobile = 5-10
        'navigator.doNotTrack': random.choice(['1', 'unspecified']),  # Randomize DNT (must be string)
        'navigator.globalPrivacyControl': random.choice([True, False]),  # Randomize GPC
        
        # ========================================
        # CURSOR MOVEMENT (C++ implementation)
        # ========================================
        'humanize:maxTime': 2.5 if use_stealth else 1.5,  # Max time for cursor movement
        'humanize:minTime': 0.5 if use_stealth else 0.3,  # Min time for cursor movement
    }
    
    # Log configuration details
    logger.info("   🖥️  Screen: %dx%d (%s), DPR=%s, colorDepth=%s",
                screen_width, screen_height, screen_config['name'],
                device_pixel_ratio, config['screen.colorDepth'])
    logger.info("   🪟 Window: inner=%dx%d, outer=%dx%d, pos=(%d, %d)",
                inner_width, inner_height, outer_width, outer_height,
                config['window.screenX'], config['window.screenY'])
    logger.info("   🎨 Canvas: aaOffset=%s, aaCapOffset=%s (Skia-level anti-aliasing)",
                config['canvas:aaOffset'], config['canvas:aaCapOffset'])
    logger.info("   🌍 Location: %s-%s, timezone=%s, geo=(%s, %s)",
                config['locale:language'], config['locale:region'],
                config['timezone'],
                config['geolocation:latitude'], config['geolocation:longitude'])
    
    return config


__all__ = ["generate_camoufox_config"]
