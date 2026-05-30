"""
Browser management modules.

Provides browser lifecycle management, CDP connections, and tab tracking.
"""

from .tab_registry import TabRegistry
from .camoufox_config import generate_camoufox_config
from .cdp_connector import connect_to_chrome_cdp, get_active_tab, create_new_tab

__all__ = [
    "TabRegistry",
    "generate_camoufox_config",
    "connect_to_chrome_cdp",
    "get_active_tab",
    "create_new_tab",
]