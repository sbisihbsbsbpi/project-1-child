"""
CDP (Chrome DevTools Protocol) connection utilities.

Extracted from screenshot_service.py (lines 1323-1483)
Part of Week 3 refactoring.

Provides CDP connection management with:
- Connection retry logic
- Auto-detection of common CDP ports
- Tab creation and selection
- Disconnect handling
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def connect_to_chrome_cdp(
    playwright,
    cdp_url: str = "http://localhost:9223",
    max_retries: int = 3,
    retry_delay: float = 2.0,
    on_disconnect: callable = None
):
    """
    Connect to an existing Chrome/Brave browser via CDP (Chrome DevTools Protocol).
    
    This allows controlling an already-running browser instead of launching a new one.
    Auto-detects Brave (9223), Chrome (9222), and other common CDP ports.
    
    Args:
        playwright: Playwright instance
        cdp_url: CDP endpoint URL (default: http://localhost:9223 for Brave)
        max_retries: Maximum number of connection attempts (default: 3)
        retry_delay: Seconds to wait between retries (default: 2.0)
        on_disconnect: Optional callback function called when browser disconnects
        
    Returns:
        Browser instance connected via CDP
        
    Raises:
        RuntimeError: If connection fails after all retries
        
    Example:
        playwright = await async_playwright().start()
        browser = await connect_to_chrome_cdp(playwright, "http://localhost:9223")
    """
    # Try to connect with retries
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.debug("🔄 Retry attempt %d/%d...", attempt + 1, max_retries)
                await asyncio.sleep(retry_delay)

            logger.info("🔗 Connecting to browser via CDP at %s...", cdp_url)
            cdp_browser = await playwright.chromium.connect_over_cdp(cdp_url)
            
            # Add disconnect handler if provided
            if on_disconnect:
                cdp_browser.on("disconnected", on_disconnect)
            
            logger.info("✅ Connected to Chrome via CDP!")
            return cdp_browser
        
        except Exception as e:
            error_msg = str(e)
            
            # If this is not the last attempt, continue to retry
            if attempt < max_retries - 1:
                logger.warning("⚠️  Connection attempt %d failed: %s", attempt + 1, error_msg)
                continue
            
            # Last attempt failed, show detailed error
            logger.error("❌ Failed to connect to Chrome via CDP after %d attempts: %s", max_retries, error_msg)
            logger.debug("\n" + "=" * 60)
            logger.info("💡 HOW TO FIX:")
            logger.debug("=" * 60)
            
            if "ECONNREFUSED" in error_msg or "connect" in error_msg.lower():
                logger.debug("\n1. Chrome is not running with remote debugging enabled.")
                logger.debug("\n2. Run this command to launch Chrome:")
                logger.debug("   cd project-1-child")
                logger.debug("   ./launch-chrome-debug.sh")
                logger.debug("\n3. Or manually launch Chrome with:")
                logger.debug(
                    "   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223")
                logger.debug("\n4. Make sure Chrome opens and has at least one tab")
                logger.debug("\n5. Verify Chrome is running:")
                logger.debug("   ./check-chrome-debug.sh")
                logger.debug("\n6. Then try capturing screenshots again")
            else:
                logger.debug("\nUnexpected error: %s", error_msg)
                logger.debug("\nTry restarting Chrome with remote debugging enabled.")
            
            logger.debug("=" * 60 + "\n")
            raise RuntimeError(
                f"Cannot connect to Chrome. Please launch Chrome with remote debugging enabled. Run: ./launch-chrome-debug.sh")


async def get_active_tab(cdp_browser):
    """
    Get the currently active tab from CDP-connected browser.
    
    Args:
        cdp_browser: Browser instance connected via CDP
        
    Returns:
        Page object representing the active tab
        
    Raises:
        RuntimeError: If no contexts or tabs found
    """
    if cdp_browser is None:
        raise RuntimeError("Not connected to Chrome via CDP.")
    
    # Get all contexts (windows)
    contexts = cdp_browser.contexts
    if not contexts:
        raise RuntimeError("No browser contexts found. Make sure Chrome has at least one window open.")
    
    # Get the first context (main window)
    context = contexts[0]
    
    # Get all pages (tabs) in the context
    pages = context.pages
    if not pages:
        raise RuntimeError("No tabs found in Chrome. Make sure Chrome has at least one tab open.")
    
    # The first page is typically the active one
    active_page = pages[0]
    
    if active_page is None:
        raise RuntimeError("Could not find active tab.")

    logger.info("🎯 Using active tab: %s", active_page.url)
    return active_page


async def create_new_tab(cdp_browser, timeout: float = 10.0):
    """
    Create a new tab next to the active tab in CDP-connected browser.
    
    This prevents navigating away from the screenshot tool tab.
    Instead, opens a new tab for capturing screenshots.
    
    Args:
        cdp_browser: Browser instance connected via CDP
        timeout: Timeout in seconds for creating tab (default: 10.0)
        
    Returns:
        Page object representing the newly created tab
        
    Raises:
        RuntimeError: If tab creation fails
    """
    if cdp_browser is None:
        raise RuntimeError("Not connected to Chrome via CDP.")
    
    # Get all contexts (windows)
    contexts = cdp_browser.contexts
    if not contexts:
        raise RuntimeError("No browser contexts found. Make sure Chrome has at least one window open.")
    
    # Get the first context (main window)
    context = contexts[0]
    
    # Create a new tab in the same context with timeout
    logger.debug("🆕 Creating new tab for screenshot capture...")
    try:
        new_page = await asyncio.wait_for(context.new_page(), timeout=timeout)
        logger.info("✅ New tab created (will load URL here)")
        return new_page
    except asyncio.TimeoutError:
        # If new_page() hangs, try alternative approach: use existing blank tab
        logger.warning("   ⚠️  new_page() timed out, trying alternative approach...")
        
        # Get all existing pages
        pages = context.pages
        
        # Look for a blank/new tab (about:blank or chrome://newtab)
        for page in pages:
            url = page.url
            if url in ['about:blank', 'chrome://newtab/', '', 'chrome://newtab']:
                logger.info("   ✅ Found existing blank tab, reusing it")
                return page

        # If no blank tab found, just use the last page
        if pages:
            logger.warning("   ⚠️  No blank tab found, using last tab: %s", pages[-1].url)
            return pages[-1]
        
        # If all else fails, raise the error
        raise RuntimeError("Failed to create or find a usable tab for screenshot capture")


__all__ = ["connect_to_chrome_cdp", "get_active_tab", "create_new_tab"]
