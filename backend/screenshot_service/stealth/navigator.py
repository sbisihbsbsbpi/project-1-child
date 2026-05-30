"""
Navigator property spoofing for stealth mode.

Extracted from screenshot_service.py (lines 861-873, 1263-1284)
Part of Week 4 refactoring.

Provides navigator.webdriver disabling and property spoofing to prevent
automation detection.

Solution #1 from the 9 Stealth Solutions framework.
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def disable_navigator_webdriver(page: Page):
    """
    Disable the navigator.webdriver flag.
    
    This is the most obvious automation indicator and is checked by
    nearly all bot detection systems.
    
    Args:
        page: Playwright page object
        
    Example:
        page = await context.new_page()
        await disable_navigator_webdriver(page)
    """
    await page.add_init_script("""
        // Override navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
    """)
    logger.debug("   🔒 navigator.webdriver disabled")


async def spoof_navigator_properties(page: Page):
    """
    Spoof additional navigator properties for enhanced stealth.
    
    Overrides chrome object and permissions API to appear more like
    a real browser.
    
    Args:
        page: Playwright page object
        
    Example:
        page = await context.new_page()
        await spoof_navigator_properties(page)
    """
    await page.add_init_script("""
        // Override chrome property
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)
    logger.debug("   🔒 Navigator properties spoofed")


async def apply_all_navigator_stealth(page: Page):
    """
    Apply all navigator stealth techniques.
    
    Convenience function that applies:
    - navigator.webdriver disabling
    - Navigator property spoofing
    
    Args:
        page: Playwright page object
        
    Example:
        page = await context.new_page()
        await apply_all_navigator_stealth(page)
    """
    await disable_navigator_webdriver(page)
    await spoof_navigator_properties(page)
    logger.debug("   ✅ All navigator stealth techniques applied")


__all__ = [
    "disable_navigator_webdriver",
    "spoof_navigator_properties",
    "apply_all_navigator_stealth",
]
