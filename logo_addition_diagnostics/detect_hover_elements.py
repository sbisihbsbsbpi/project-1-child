"""
Diagnostic script to detect elements that appear when hovering over the Nucar logo.
Uses MutationObserver and computed style checks to find hidden toolbar icons.
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def detect_hover_elements():
    """Detect what elements appear when hovering over the Nucar logo"""
    
    async with async_playwright() as p:
        # Connect to existing browser
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        logger.info("Connected to browser")
        logger.info(f"Current URL: {page.url}")
        
        # Navigate to the Service History Recap PDF template
        template_id = "667f0befd4964026ee7b6ea2"
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        
        logger.info(f"Opening template: {edit_url}")
        await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(10)  # Wait for warning icons to render
        
        # Setup mutation observer and hover detection
        result = await page.evaluate("""
            async () => {
                const results = {
                    beforeHover: [],
                    afterHover: [],
                    mutations: [],
                    newElements: []
                };
                
                // Helper function to check visibility
                function isVisible(el) {
                    const s = getComputedStyle(el);
                    return s.display !== 'none' 
                        && s.visibility !== 'hidden' 
                        && s.opacity !== '0'
                        && el.offsetWidth > 0
                        && el.offsetHeight > 0;
                }
                
                // Find the Nucar logo with warning
                const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb, .icon-alert1, [class*="errorWarningIconsWithPopover_warningIcon"]');
                if (!warningIcon) {
                    return { error: 'Warning icon not found' };
                }
                
                const container = warningIcon.closest('[class*="SortableItem"]') || warningIcon.closest('[data-logo-to-replace]');
                if (!container) {
                    return { error: 'Container not found' };
                }
                
                // Get all interactive elements BEFORE hover
                const allBefore = container.querySelectorAll('button, [role="button"], [aria-label], [class*="icon-"], a, [tabindex]');
                allBefore.forEach(el => {
                    const visible = isVisible(el);
                    results.beforeHover.push({
                        tag: el.tagName,
                        ariaLabel: el.getAttribute('aria-label'),
                        className: el.className.substring(0, 60),
                        visible: visible,
                        display: getComputedStyle(el).display,
                        opacity: getComputedStyle(el).opacity,
                        visibility: getComputedStyle(el).visibility
                    });
                });
                
                // Setup MutationObserver to watch for DOM/style changes
                const mutationLog = [];
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach(mutation => {
                        if (mutation.type === 'attributes' && (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
                            mutationLog.push({
                                type: 'attribute',
                                element: mutation.target.tagName,
                                attribute: mutation.attributeName,
                                className: mutation.target.className?.substring(0, 60),
                                ariaLabel: mutation.target.getAttribute?.('aria-label')
                            });
                        } else if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                            mutation.addedNodes.forEach(node => {
                                if (node.nodeType === 1) {  // Element node
                                    mutationLog.push({
                                        type: 'added',
                                        element: node.tagName,
                                        className: node.className?.substring(0, 60),
                                        ariaLabel: node.getAttribute?.('aria-label')
                                    });
                                }
                            });
                        }
                    });
                });
                
                // Observe the container and body for changes
                observer.observe(container, { 
                    attributes: true, 
                    childList: true, 
                    subtree: true,
                    attributeFilter: ['style', 'class']
                });
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
                
                // Hover over the logo image
                const img = container.querySelector('img');
                if (img) {
                    const event = new MouseEvent('mouseenter', { bubbles: true });
                    img.dispatchEvent(event);
                    container.dispatchEvent(event);
                }
                
                // Wait for changes to settle
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Get all interactive elements AFTER hover
                const allAfter = container.querySelectorAll('button, [role="button"], [aria-label], [class*="icon-"], a, [tabindex]');
                allAfter.forEach(el => {
                    const visible = isVisible(el);
                    results.afterHover.push({
                        tag: el.tagName,
                        ariaLabel: el.getAttribute('aria-label'),
                        className: el.className.substring(0, 60),
                        visible: visible,
                        display: getComputedStyle(el).display,
                        opacity: getComputedStyle(el).opacity,
                        visibility: getComputedStyle(el).visibility
                    });
                });
                
                observer.disconnect();
                results.mutations = mutationLog;
                
                // Find NEW elements that appeared
                const beforeCount = results.beforeHover.length;
                const afterCount = results.afterHover.length;
                if (afterCount > beforeCount) {
                    results.newElements = results.afterHover.slice(beforeCount);
                }
                
                return results;
            }
        """)
        
        # Analyze results
        logger.info("\n" + "="*80)
        logger.info("HOVER DETECTION RESULTS")
        logger.info("="*80)
        
        if 'error' in result:
            logger.error(f"Error: {result['error']}")
            return
        
        logger.info(f"\nElements BEFORE hover: {len(result['beforeHover'])}")
        logger.info(f"Elements AFTER hover: {len(result['afterHover'])}")
        logger.info(f"Mutations detected: {len(result['mutations'])}")
        logger.info(f"New elements appeared: {len(result['newElements'])}")
        
        logger.info("\n--- BEFORE HOVER (visible only) ---")
        for i, el in enumerate(result['beforeHover'], 1):
            if el['visible']:
                logger.info(f"{i}. {el['tag']} | aria-label={el['ariaLabel']} | class={el['className']}")
        
        logger.info("\n--- MUTATIONS DURING HOVER ---")
        for mutation in result['mutations']:
            logger.info(f"  {mutation}")
        
        logger.info("\n--- NEW ELEMENTS AFTER HOVER ---")
        for el in result['newElements']:
            logger.info(f"  {el['tag']} | visible={el['visible']} | aria-label={el['ariaLabel']} | class={el['className']}")
        
        logger.info("\n--- AFTER HOVER (visible only) ---")
        for i, el in enumerate(result['afterHover'], 1):
            if el['visible']:
                logger.info(f"{i}. {el['tag']} | aria-label={el['ariaLabel']} | class={el['className']}")
        
        logger.info("\n" + "="*80)
        logger.info("Keep the browser open for manual inspection")
        logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(detect_hover_elements())
