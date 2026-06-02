"""
Find the outer container (blue outline in screenshot) and hover over it
to trigger the toolbar with "Change Image" icon.
"""

import asyncio
from playwright.async_api import async_playwright
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def hover_outer_container():
    """Hover over the OUTER container to trigger toolbar"""
    
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
        logger.info("STEP 1: Find the outer container (SortableItem)")
        logger.info("="*100)
        
        # Find the outer container
        container_info = await page.evaluate("""
            () => {
                // Find warning icon
                const warningIcon = document.querySelector('.icon-alert1, [class*="warningIcon"]');
                if (!warningIcon) return { error: 'Warning icon not found' };
                
                // Find the SortableItem container (the outer blue-outlined div)
                const sortableItem = warningIcon.closest('[class*="SortableItem"]');
                if (!sortableItem) return { error: 'SortableItem not found' };
                
                const bounds = sortableItem.getBoundingClientRect();
                
                return {
                    success: true,
                    className: sortableItem.className,
                    bounds: {
                        x: Math.round(bounds.x),
                        y: Math.round(bounds.y),
                        width: Math.round(bounds.width),
                        height: Math.round(bounds.height)
                    }
                };
            }
        """)
        
        if not container_info.get('success'):
            logger.error(f"Error: {container_info.get('error')}")
            return
        
        logger.info(f"✅ Found outer container")
        logger.info(f"   Class: {container_info['className'][:100]}")
        logger.info(f"   Position: ({container_info['bounds']['x']}, {container_info['bounds']['y']})")
        logger.info(f"   Size: {container_info['bounds']['width']}x{container_info['bounds']['height']}")
        
        logger.info("\n" + "="*100)
        logger.info("STEP 2: Hover over outer container using Playwright")
        logger.info("="*100)
        
        # Use Playwright's hover on the outer container
        container = await page.query_selector('[class*="SortableItem_element"]')
        if container:
            logger.info("Hovering over outer container...")
            await container.hover(force=True)
            await asyncio.sleep(3)
            
            logger.info("\n" + "="*100)
            logger.info("STEP 3: Search for toolbar and Change Image icon")
            logger.info("="*100)
            
            # Now search for the toolbar
            result = await page.evaluate("""
                () => {
                    const results = {
                        changeImageElements: [],
                        toolbarIcons: [],
                        allIconsNearLogo: []
                    };
                    
                    // Search for "Change Image" text/title
                    [...document.querySelectorAll('*')].forEach(el => {
                        const text = el.innerText || el.textContent || '';
                        const title = el.getAttribute('title') || '';
                        if (text.includes('Change Image') || title.includes('Change Image')) {
                            const bounds = el.getBoundingClientRect();
                            results.changeImageElements.push({
                                tag: el.tagName,
                                className: el.className,
                                title: el.getAttribute('title'),
                                ariaLabel: el.getAttribute('aria-label'),
                                y: Math.round(bounds.y),
                                x: Math.round(bounds.x)
                            });
                        }
                    });
                    
                    // Find all icons in a 200px radius of the logo
                    const warningIcon = document.querySelector('.icon-alert1');
                    if (warningIcon) {
                        const logoBounds = warningIcon.getBoundingClientRect();
                        const logoY = logoBounds.y;
                        const logoX = logoBounds.x;
                        
                        [...document.querySelectorAll('[class*="icon"]')].forEach(el => {
                            const bounds = el.getBoundingClientRect();
                            const distance = Math.sqrt(
                                Math.pow(bounds.x - logoX, 2) + 
                                Math.pow(bounds.y - logoY, 2)
                            );
                            
                            if (distance < 200 && bounds.width > 0) {
                                results.allIconsNearLogo.push({
                                    tag: el.tagName,
                                    className: [...el.classList].join(' '),
                                    ariaLabel: el.getAttribute('aria-label'),
                                    title: el.getAttribute('title'),
                                    distance: Math.round(distance),
                                    x: Math.round(bounds.x),
                                    y: Math.round(bounds.y)
                                });
                            }
                        });
                    }
                    
                    return results;
                }
            """)
            
            logger.info(f"\n✅ Found {len(result['changeImageElements'])} 'Change Image' elements")
            for i, el in enumerate(result['changeImageElements'], 1):
                logger.info(f"\n{i}. {el['tag']} at ({el['x']}, {el['y']})")
                logger.info(f"   title: {el['title']}")
                logger.info(f"   aria-label: {el['ariaLabel']}")
                logger.info(f"   class: {el['className'][:80]}")
            
            logger.info(f"\n✅ Found {len(result['allIconsNearLogo'])} icons near logo")
            for i, icon in enumerate(result['allIconsNearLogo'][:10], 1):
                logger.info(f"\n{i}. {icon['tag']} (distance: {icon['distance']}px)")
                logger.info(f"   aria-label: {icon['ariaLabel']}")
                logger.info(f"   title: {icon['title']}")
                logger.info(f"   class: {icon['className'][:60]}")
            
            # Save results
            with open('logo_addition_diagnostics/outer_container_hover_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info("\n✅ Results saved to: logo_addition_diagnostics/outer_container_hover_results.json")
        
        logger.info("\n" + "="*100)

if __name__ == "__main__":
    asyncio.run(hover_outer_container())
