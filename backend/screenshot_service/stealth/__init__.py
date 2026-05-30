"""
Stealth and anti-detection modules.

Provides comprehensive bot detection evasion techniques including:
- Navigator property spoofing
- Canvas/WebGL fingerprint randomization
- Audio context randomization
- CDP detection bypass
- Behavioral simulation
"""

from .navigator import (
    disable_navigator_webdriver,
    spoof_navigator_properties,
    apply_all_navigator_stealth,
)
from .canvas_webgl import apply_canvas_webgl_randomization
from .audio_context import apply_audio_context_randomization
from .cdp_bypass import apply_cdp_detection_bypass
from .behavioral import (
    add_random_delay,
    simulate_mouse_movement,
    simulate_scrolling,
    apply_behavioral_randomization,
)

__all__ = [
    # Navigator
    "disable_navigator_webdriver",
    "spoof_navigator_properties",
    "apply_all_navigator_stealth",
    # Canvas/WebGL
    "apply_canvas_webgl_randomization",
    # Audio
    "apply_audio_context_randomization",
    # CDP
    "apply_cdp_detection_bypass",
    # Behavioral
    "add_random_delay",
    "simulate_mouse_movement",
    "simulate_scrolling",
    "apply_behavioral_randomization",
]
