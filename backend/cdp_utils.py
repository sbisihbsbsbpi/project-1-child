"""
CDP Utilities
Helper functions for working with CDP connections efficiently
"""

from playwright.async_api import Browser, Page
import asyncio


async def get_or_navigate_to_page(browser: Browser, url: str, wait_for_load: bool = True) -> Page:
    """
    Get existing page with URL or navigate to it
    Uses existing tabs instead of creating new ones
    
    Args:
        browser: Connected browser instance
        url: Target URL
        wait_for_load: Whether to wait for page load
        
    Returns:
        Page object ready to use
    """
    context = browser.contexts[0]
    pages = context.pages
    
    # Try to find existing page with this URL
    for page in pages:
        if url in page.url:
            print(f"✅ Using existing tab: {page.url}")
            if wait_for_load:
                await asyncio.sleep(0.5)  # Small delay to ensure stability
            return page
    
    # Use first available page instead of creating new one
    if pages:
        page = pages[0]
        print(f"📄 Reusing tab (was: {page.url})")
        print(f"🌐 Navigating to: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        if wait_for_load:
            await asyncio.sleep(2)
        return page
    
    # Only create new page if absolutely necessary
    print("⚠️  No existing tabs, creating new one")
    page = await context.new_page()
    await page.goto(url, wait_until='domcontentloaded', timeout=15000)
    if wait_for_load:
        await asyncio.sleep(2)
    return page


async def get_active_page(browser: Browser) -> Page:
    """
    Get the currently active page from CDP
    
    Args:
        browser: Connected browser instance
        
    Returns:
        Active page object
    """
    context = browser.contexts[0]
    pages = context.pages
    
    if not pages:
        raise Exception("No pages available in browser")
    
    # Return the first page (usually the active one)
    return pages[0]


async def inject_script(page: Page, script: str) -> any:
    """
    Inject and execute JavaScript in the page
    
    Args:
        page: Page object
        script: JavaScript code to execute
        
    Returns:
        Result of script execution
    """
    return await page.evaluate(script)


async def wait_for_element(page: Page, selector: str, timeout: int = 5000):
    """
    Wait for element to appear
    
    Args:
        page: Page object
        selector: CSS selector
        timeout: Timeout in milliseconds
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return True
    except:
        return False


def print_cdp_info(browser: Browser):
    """
    Print CDP connection info
    
    Args:
        browser: Connected browser instance
    """
    context = browser.contexts[0]
    pages = context.pages
    
    print(f"📡 CDP Connection Info:")
    print(f"   Contexts: {len(browser.contexts)}")
    print(f"   Open Tabs: {len(pages)}")
    
    if pages:
        print(f"   Active Tabs:")
        for i, page in enumerate(pages):
            print(f"     {i+1}. {page.url}")
