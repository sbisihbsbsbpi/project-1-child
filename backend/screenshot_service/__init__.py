"""
Screenshot Service - Modular browser automation and screenshot capture.

This package provides a comprehensive screenshot service with:
- Multiple browser engines (Playwright, Camoufox, CDP)
- Stealth/anti-detection features
- Viewport, full-page, and segmented capture modes
- Authentication and cookie management
- Network tracking and cURL export

Public API (stable during refactoring):
    from screenshot_service import ScreenshotService

Example:
    service = ScreenshotService()
    result = await service.capture("https://example.com")

Refactoring Status: 🟡 In Progress (Week 2)
Target: Modular architecture with ~15 focused modules
See: REFACTOR_GUIDE.md for details
"""

# Week 2 Extractions
from .constants import USER_AGENTS, VIEWPORTS
from .utils import ImageHashCache, to_pascal_case, generate_filename
from .network import create_network_event_handlers, convert_network_events_to_curl

# Week 3 Extractions
from .browser import (
    TabRegistry,
    generate_camoufox_config,
    connect_to_chrome_cdp,
    get_active_tab,
    create_new_tab,
)

# Week 4 Extractions
from .stealth import (
    disable_navigator_webdriver,
    spoof_navigator_properties,
    apply_all_navigator_stealth,
    apply_canvas_webgl_randomization,
    apply_audio_context_randomization,
    apply_cdp_detection_bypass,
    add_random_delay,
    simulate_mouse_movement,
    simulate_scrolling,
    apply_behavioral_randomization,
)

# TODO Week 6: Import main ScreenshotService from core.orchestrator
# TEMPORARY FIX: Import ScreenshotService from the root module file
# This allows `from screenshot_service import ScreenshotService` to work
# since the package (directory) takes precedence over the module (file)
import sys
from pathlib import Path

# Import from screenshot_service.py file (not the package)
_module_dir = Path(__file__).parent.parent
_module_file = _module_dir / "screenshot_service.py"
if _module_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_screenshot_service_module", str(_module_file))
    if spec and spec.loader:
        _ss_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_ss_module)
        ScreenshotService = _ss_module.ScreenshotService
    else:
        ScreenshotService = None  # type: ignore
else:
    ScreenshotService = None  # type: ignore

__version__ = "2.0.0-refactor"
__all__ = [
    # Main Service
    "ScreenshotService",
    # Constants
    "USER_AGENTS",
    "VIEWPORTS",
    # Browser
    "TabRegistry",
    "generate_camoufox_config",
    "connect_to_chrome_cdp",
    "get_active_tab",
    "create_new_tab",
    # Stealth
    "disable_navigator_webdriver",
    "spoof_navigator_properties",
    "apply_all_navigator_stealth",
    "apply_canvas_webgl_randomization",
    "apply_audio_context_randomization",
    "apply_cdp_detection_bypass",
    "add_random_delay",
    "simulate_mouse_movement",
    "simulate_scrolling",
    "apply_behavioral_randomization",
    # Utils
    "ImageHashCache",
    "to_pascal_case",
    "generate_filename",
    # Network
    "create_network_event_handlers",
    "convert_network_events_to_curl",
]
