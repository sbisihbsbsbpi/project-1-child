"""
Find ALL elements (including hidden ones) in the Nucar logo container.
Check computed styles to see what's hidden by opacity, display, visibility.
"""

import asyncio
from playwright.async_api import async_playwright
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def find_all_elements():
    """Find all elements including hidden ones"""
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        
        logger.info("Connected to browser")
        
        # Navigate to template
        template_id = "667f0befd4964026ee7b6ea2"
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        
        logger.info(f"Opening: {edit_url}")
        await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(10)
        
        # Get ALL elements in container, including hidden ones
        result = await page.evaluate("""
            () => {
                // Find the Nucar logo container
                const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb, .icon-alert1');
                if (!warningIcon) return { error: 'Warning icon not found' };
                
                const container = warningIcon.closest('[class*="SortableItem"]');
                if (!container) return { error: 'Container not found' };
                
                const results = {
                    allElements: [],
                    hiddenElements: [],
                    potentialToolbars: []
                };
                
                // Get ALL descendants
                const allDescendants = container.querySelectorAll('*');
                
                allDescendants.forEach((el, index) => {
                    const computed = getComputedStyle(el);
                    const bounds = el.getBoundingClientRect();
                    
                    const elementInfo = {
                        index: index,
                        tag: el.tagName,
                        id: el.id,
                        className: el.className,
                        ariaLabel: el.getAttribute('aria-label'),
                        title: el.getAttribute('title'),
                        role: el.getAttribute('role'),
                        display: computed.display,
                        visibility: computed.visibility,
                        opacity: computed.opacity,
                        width: bounds.width,
                        height: bounds.height,
                        position: computed.position,
                        zIndex: computed.zIndex,
                        isHidden: computed.display === 'none' || 
                                 computed.visibility === 'hidden' || 
                                 computed.opacity === '0' ||
                                 bounds.width === 0 || 
                                 bounds.height === 0
                    };
                    
                    results.allElements.push(elementInfo);
                    
                    // Collect hidden interactive elements
                    if (elementInfo.isHidden && 
                        (el.tagName === 'BUTTON' || 
                         el.getAttribute('role') === 'button' || 
                         el.getAttribute('aria-label') || 
                         el.className.includes('icon'))) {
                        results.hiddenElements.push(elementInfo);
                    }
                    
                    // Look for toolbar-like elements
                    if (el.className.includes('toolbar') || 
                        el.className.includes('actions') || 
                        el.className.includes('menu')) {
                        results.potentialToolbars.push(elementInfo);
                    }
                });
                
                return results;
            }
        """)
        
        if 'error' in result:
            logger.error(f"Error: {result['error']}")
            return
        
        logger.info("\n" + "="*100)
        logger.info("ALL ELEMENTS IN CONTAINER")
        logger.info("="*100)
        logger.info(f"Total elements: {len(result['allElements'])}")
        logger.info(f"Hidden elements: {len(result['hiddenElements'])}")
        logger.info(f"Potential toolbars: {len(result['potentialToolbars'])}")
        
        logger.info("\n--- HIDDEN INTERACTIVE ELEMENTS ---")
        if result['hiddenElements']:
            for el in result['hiddenElements']:
                logger.info(f"\n  [{el['index']}] {el['tag']}")
                logger.info(f"    aria-label: {el['ariaLabel']}")
                logger.info(f"    title: {el['title']}")
                logger.info(f"    class: {el['className'][:80]}")
                logger.info(f"    display: {el['display']}, visibility: {el['visibility']}, opacity: {el['opacity']}")
                logger.info(f"    size: {el['width']}x{el['height']}")
        else:
            logger.info("  None found")
        
        logger.info("\n--- POTENTIAL TOOLBARS ---")
        if result['potentialToolbars']:
            for el in result['potentialToolbars']:
                logger.info(f"\n  [{el['index']}] {el['tag']}")
                logger.info(f"    class: {el['className'][:80]}")
                logger.info(f"    hidden: {el['isHidden']}")
                logger.info(f"    display: {el['display']}, opacity: {el['opacity']}")
        else:
            logger.info("  None found")
        
        logger.info("\n--- ALL ELEMENTS WITH 'icon' IN CLASS NAME ---")
        icon_elements = [el for el in result['allElements'] if 'icon' in el['className'].lower()]
        for el in icon_elements:
            hidden_marker = " [HIDDEN]" if el['isHidden'] else " [VISIBLE]"
            logger.info(f"  {el['tag']} | aria={el['ariaLabel']} | {el['className'][:60]}{hidden_marker}")
        
        logger.info("\n--- ELEMENTS WITH aria-label ATTRIBUTE ---")
        aria_elements = [el for el in result['allElements'] if el['ariaLabel']]
        for el in aria_elements:
            hidden_marker = " [HIDDEN]" if el['isHidden'] else " [VISIBLE]"
            logger.info(f"  {el['tag']} | aria-label=\"{el['ariaLabel']}\" | {el['className'][:50]}{hidden_marker}")
        
        # Save full results to file
        with open('logo_addition_diagnostics/all_elements_dump.json', 'w') as f:
            json.dump(result, f, indent=2)
        logger.info("\n✅ Full element dump saved to: logo_addition_diagnostics/all_elements_dump.json")
        
        logger.info("\n" + "="*100)

if __name__ == "__main__":
    asyncio.run(find_all_elements())
