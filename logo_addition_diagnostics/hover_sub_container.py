"""
Hover over the SUB-CONTAINER (middle layer between SortableItem and img)
to trigger the toolbar with "Change Image" icon.
"""

import asyncio
from playwright.async_api import async_playwright
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def hover_sub_container():
    """Hover over the sub-container to trigger toolbar"""
    
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
        
        logger.info("\n" + "="*100)
        logger.info("Finding the SUB-CONTAINER (templates_Image_imageComponent)")
        logger.info("="*100)
        
        # Find and hover the sub-container
        result = await page.evaluate("""
            () => {
                const warningIcon = document.querySelector('.icon-alert1, [class*="warningIcon"]');
                if (!warningIcon) return { error: 'Warning icon not found' };
                
                // Find the sub-container (imageComponent div)
                const imageComponent = warningIcon.closest('[class*="imageComponent"]');
                if (!imageComponent) return { error: 'imageComponent not found' };
                
                const bounds = imageComponent.getBoundingClientRect();
                
                return {
                    success: true,
                    className: imageComponent.className,
                    role: imageComponent.getAttribute('role'),
                    bounds: {
                        x: Math.round(bounds.x),
                        y: Math.round(bounds.y),
                        width: Math.round(bounds.width),
                        height: Math.round(bounds.height)
                    }
                };
            }
        """)
        
        if not result.get('success'):
            logger.error(f"Error: {result.get('error')}")
            return
        
        logger.info(f"✅ Found sub-container")
        logger.info(f"   Class: {result['className']}")
        logger.info(f"   Role: {result['role']}")
        logger.info(f"   Position: ({result['bounds']['x']}, {result['bounds']['y']})")
        logger.info(f"   Size: {result['bounds']['width']}x{result['bounds']['height']}")
        
        logger.info("\n" + "="*100)
        logger.info("Hovering over SUB-CONTAINER...")
        logger.info("="*100)
        
        # Hover using Playwright
        sub_container = await page.query_selector('[class*="imageComponent"]')
        if sub_container:
            await sub_container.hover(force=True)
            logger.info("✅ Hovered!")
            await asyncio.sleep(3)
            
            logger.info("\n" + "="*100)
            logger.info("Searching for toolbar and 'Change Image' icon...")
            logger.info("="*100)
            
            # Search for toolbar
            toolbar_result = await page.evaluate("""
                () => {
                    const results = {
                        changeImageElements: [],
                        toolbarIcons: [],
                        allVisibleIcons: []
                    };
                    
                    // Search for "Change Image" in title or text
                    [...document.querySelectorAll('*')].forEach(el => {
                        const title = el.getAttribute('title') || '';
                        const text = el.textContent || '';
                        if (title.includes('Change Image') || text.includes('Change Image')) {
                            const bounds = el.getBoundingClientRect();
                            if (bounds.width > 0) {
                                results.changeImageElements.push({
                                    tag: el.tagName,
                                    className: el.className,
                                    title: el.getAttribute('title'),
                                    ariaLabel: el.getAttribute('aria-label'),
                                    x: Math.round(bounds.x),
                                    y: Math.round(bounds.y)
                                });
                            }
                        }
                    });
                    
                    // Get all currently visible icons
                    [...document.querySelectorAll('[class*="icon"]')].forEach(el => {
                        const bounds = el.getBoundingClientRect();
                        if (bounds.width > 0 && bounds.height > 0 && 
                            bounds.y >= 0 && bounds.y < window.innerHeight) {
                            results.allVisibleIcons.push({
                                tag: el.tagName,
                                className: [...el.classList].join(' '),
                                ariaLabel: el.getAttribute('aria-label'),
                                title: el.getAttribute('title'),
                                x: Math.round(bounds.x),
                                y: Math.round(bounds.y)
                            });
                        }
                    });
                    
                    return results;
                }
            """)
            
            logger.info(f"\n🎯 Found {len(toolbar_result['changeImageElements'])} 'Change Image' elements!")
            for i, el in enumerate(toolbar_result['changeImageElements'], 1):
                logger.info(f"\n{i}. {el['tag']} at ({el['x']}, {el['y']})")
                logger.info(f"   title: '{el['title']}'")
                logger.info(f"   aria-label: '{el['ariaLabel']}'")
                logger.info(f"   class: {el['className'][:80]}")
            
            logger.info(f"\n📊 Total visible icons: {len(toolbar_result['allVisibleIcons'])}")
            
            # Save results
            with open('logo_addition_diagnostics/sub_container_hover_results.json', 'w') as f:
                json.dump(toolbar_result, f, indent=2)
            
            logger.info("\n✅ Results saved to: logo_addition_diagnostics/sub_container_hover_results.json")
        
        logger.info("\n" + "="*100)

if __name__ == "__main__":
    asyncio.run(hover_sub_container())
