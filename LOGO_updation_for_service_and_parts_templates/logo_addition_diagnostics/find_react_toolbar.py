"""
Search for React/Emotion toolbar elements that appear on hover.
Look for portals, overlays, and dynamically rendered toolbars.
"""

import asyncio
from playwright.async_api import async_playwright
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def find_react_toolbar():
    """Find React/Emotion toolbar elements"""
    
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
        
        # Search for React/Emotion toolbar elements across the entire page
        result = await page.evaluate("""
            () => {
                const results = {
                    reactRoots: [],
                    emotionStyled: [],
                    toolbarElements: [],
                    iconElements: [],
                    hiddenToolbars: [],
                    changeImageCandidates: []
                };
                
                // Helper to check visibility
                function getVisibilityInfo(el) {
                    const computed = getComputedStyle(el);
                    const bounds = el.getBoundingClientRect();
                    return {
                        display: computed.display,
                        visibility: computed.visibility,
                        opacity: computed.opacity,
                        width: bounds.width,
                        height: bounds.height,
                        position: computed.position,
                        zIndex: computed.zIndex,
                        isVisible: computed.display !== 'none' && 
                                  computed.visibility !== 'hidden' && 
                                  computed.opacity !== '0' &&
                                  bounds.width > 0 && 
                                  bounds.height > 0
                    };
                }
                
                // 1. Find React root elements (portals, overlays)
                const reactRootCandidates = document.querySelectorAll('[data-reactroot], [id*="root"], [class*="portal"], [class*="overlay"]');
                reactRootCandidates.forEach(el => {
                    const vis = getVisibilityInfo(el);
                    results.reactRoots.push({
                        tag: el.tagName,
                        id: el.id,
                        className: el.className.substring(0, 80),
                        ...vis
                    });
                });
                
                // 2. Find Emotion-styled elements (css-* classes)
                const emotionElements = document.querySelectorAll('[class*="css-"]');
                emotionElements.forEach(el => {
                    if (el.className.includes('toolbar') || 
                        el.className.includes('action') || 
                        el.className.includes('menu') ||
                        el.getAttribute('aria-label')?.includes('icon')) {
                        const vis = getVisibilityInfo(el);
                        results.emotionStyled.push({
                            tag: el.tagName,
                            className: el.className.substring(0, 80),
                            ariaLabel: el.getAttribute('aria-label'),
                            ...vis
                        });
                    }
                });
                
                // 3. Search for toolbar-like elements ANYWHERE in the page
                const toolbarSelectors = [
                    '[class*="toolbar"]',
                    '[class*="Toolbar"]',
                    '[class*="actions"]',
                    '[class*="Actions"]',
                    '[class*="menu"]',
                    '[class*="Menu"]',
                    '[data-toolbar]',
                    '[role="toolbar"]'
                ];
                
                toolbarSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const vis = getVisibilityInfo(el);
                        results.toolbarElements.push({
                            selector: selector,
                            tag: el.tagName,
                            id: el.id,
                            className: el.className.substring(0, 100),
                            role: el.getAttribute('role'),
                            childCount: el.children.length,
                            ...vis
                        });
                    });
                });
                
                // 4. Find ALL icon elements on the page
                const iconSelectors = [
                    '[class*="icon-"]',
                    '[aria-label*="icon-"]',
                    '[class*="Icon"]'
                ];
                
                iconSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const vis = getVisibilityInfo(el);
                        const ariaLabel = el.getAttribute('aria-label');
                        const className = el.className;
                        
                        // Look for change/switch/replace related icons
                        if (ariaLabel?.includes('switch') || 
                            ariaLabel?.includes('change') || 
                            ariaLabel?.includes('replace') ||
                            className.includes('switch') ||
                            className.includes('change') ||
                            className.includes('replace')) {
                            results.changeImageCandidates.push({
                                tag: el.tagName,
                                ariaLabel: ariaLabel,
                                className: className.substring(0, 80),
                                title: el.getAttribute('title'),
                                ...vis
                            });
                        }
                        
                        results.iconElements.push({
                            tag: el.tagName,
                            ariaLabel: ariaLabel,
                            className: className.substring(0, 60),
                            ...vis
                        });
                    });
                });
                
                // 5. Find hidden toolbars (display:none or opacity:0)
                results.toolbarElements.forEach(toolbar => {
                    if (!toolbar.isVisible) {
                        results.hiddenToolbars.push(toolbar);
                    }
                });
                
                return results;
            }
        """)
        
        logger.info("\n" + "="*100)
        logger.info("REACT/EMOTION TOOLBAR SEARCH")
        logger.info("="*100)
        
        logger.info(f"\nReact roots found: {len(result['reactRoots'])}")
        logger.info(f"Emotion-styled elements: {len(result['emotionStyled'])}")
        logger.info(f"Toolbar elements: {len(result['toolbarElements'])}")
        logger.info(f"Icon elements: {len(result['iconElements'])}")
        logger.info(f"Hidden toolbars: {len(result['hiddenToolbars'])}")
        logger.info(f"'Change Image' candidates: {len(result['changeImageCandidates'])}")
        
        logger.info("\n--- TOOLBAR ELEMENTS ---")
        for toolbar in result['toolbarElements'][:20]:  # Limit to first 20
            vis = "VISIBLE" if toolbar['isVisible'] else "HIDDEN"
            logger.info(f"\n  {toolbar['tag']} [{vis}]")
            logger.info(f"    class: {toolbar['className']}")
            logger.info(f"    children: {toolbar['childCount']}")
            logger.info(f"    display: {toolbar['display']}, opacity: {toolbar['opacity']}")
        
        logger.info("\n--- CHANGE IMAGE CANDIDATES ---")
        if result['changeImageCandidates']:
            for candidate in result['changeImageCandidates']:
                vis = "VISIBLE" if candidate['isVisible'] else "HIDDEN"
                logger.info(f"\n  {candidate['tag']} [{vis}]")
                logger.info(f"    aria-label: {candidate['ariaLabel']}")
                logger.info(f"    title: {candidate['title']}")
                logger.info(f"    class: {candidate['className']}")
        else:
            logger.info("  ❌ NO elements with 'switch', 'change', or 'replace' found!")
        
        logger.info("\n--- HIDDEN TOOLBARS ---")
        for toolbar in result['hiddenToolbars'][:10]:
            logger.info(f"\n  {toolbar['tag']}")
            logger.info(f"    class: {toolbar['className']}")
            logger.info(f"    display: {toolbar['display']}, opacity: {toolbar['opacity']}")
            logger.info(f"    children: {toolbar['childCount']}")
        
        # Save full results
        with open('logo_addition_diagnostics/react_toolbar_dump.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info("\n✅ Full results saved to: logo_addition_diagnostics/react_toolbar_dump.json")
        logger.info("="*100)

if __name__ == "__main__":
    asyncio.run(find_react_toolbar())
