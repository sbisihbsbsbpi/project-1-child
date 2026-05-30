"""
CDP (Chrome DevTools Protocol) detection bypass.

Extracted from screenshot_service.py (lines 2174-2240)
Part of Week 4 refactoring.

Provides CDP detection bypass by:
- Removing CDP runtime variables
- Hiding automation flags
- Spoofing navigator properties
- Overriding permissions API

Advanced anti-bots detect CDP usage to identify automation tools.

Sources: GitHub dgtlmoon Feb 2024, ScrapingAnt Sep 2024
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def apply_cdp_detection_bypass(page: Page):
    """
    Apply CDP (Chrome DevTools Protocol) detection bypass.
    
    Hides traces of Chrome DevTools Protocol to prevent detection by
    advanced anti-bot systems that look for CDP usage patterns.
    
    Techniques:
    - Removes CDP runtime variables (cdc_* properties)
    - Overrides navigator.webdriver
    - Hides chrome.runtime
    - Spoofs navigator.plugins with realistic PDF plugins
    - Overrides permissions API
    
    Args:
        page: Playwright page object
        
    Example:
        page = await context.new_page()
        await apply_cdp_detection_bypass(page)
    """
    await page.add_init_script("""
        // ========================================
        // CDP Detection Bypass
        // ========================================
        (function() {
            // Remove CDP runtime variables
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;

            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // Override chrome runtime
            if (window.chrome) {
                Object.defineProperty(window.chrome, 'runtime', {
                    get: () => undefined,
                    configurable: true
                });
            }

            // Hide automation flags
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ],
                configurable: true
            });

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
            );
        })();
    """)
    logger.debug("   🔒 CDP detection bypass applied")


__all__ = ["apply_cdp_detection_bypass"]
