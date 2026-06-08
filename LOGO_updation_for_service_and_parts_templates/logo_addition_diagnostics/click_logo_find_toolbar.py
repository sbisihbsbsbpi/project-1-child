"""
Click on the Nucar logo to trigger the toolbar, then search for "Change Image" elements.
"""

import asyncio
from playwright.async_api import async_playwright
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def click_and_find_toolbar():
    """Click Nucar logo and find the toolbar that appears"""
    
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
        logger.info("STEP 1: Click on the Nucar logo with warning")
        logger.info("="*100)
        
        # Click on the Nucar logo
        click_result = await page.evaluate("""
            () => {
                // Find warning icon
                const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb, .icon-alert1, [class*="errorWarningIconsWithPopover_warningIcon"]');
                if (!warningIcon) return { success: false, error: 'Warning icon not found' };
                
                const container = warningIcon.closest('[class*="SortableItem"]');
                if (!container) return { success: false, error: 'Container not found' };
                
                // Find the image component
                const imageDiv = container.querySelector('[role="button"]');
                if (!imageDiv) return { success: false, error: 'Image div not found' };
                
                // Click it
                imageDiv.click();
                
                return {
                    success: true,
                    clicked: true,
                    className: imageDiv.className
                };
            }
        """)
        
        if not click_result.get('success'):
            logger.error(f"Failed to click logo: {click_result.get('error')}")
            return
        
        logger.info(f"✅ Clicked on logo: {click_result['className'][:80]}")
        
        # Wait for toolbar to appear
        await asyncio.sleep(2)
        
        logger.info("\n" + "="*100)
        logger.info("STEP 2: Search for 'Change Image' text (AFTER click)")
        logger.info("="*100)
        
        # Search for "Change Image" text
        change_image_elements = await page.evaluate("""
            () => {
                return [...document.querySelectorAll('*')]
                    .filter(el => {
                        const text = el.innerText || el.textContent || '';
                        const title = el.getAttribute('title') || '';
                        return text.includes('Change Image') || title.includes('Change Image');
                    })
                    .map(el => ({
                        tag: el.tagName,
                        cls: el.className,
                        text: (el.innerText || '').trim().substring(0, 100),
                        title: el.getAttribute('title'),
                        ariaLabel: el.getAttribute('aria-label'),
                        id: el.id
                    }));
            }
        """)
        
        logger.info(f"Found {len(change_image_elements)} elements with 'Change Image'")
        for i, el in enumerate(change_image_elements, 1):
            logger.info(f"\n{i}. {el['tag']}")
            logger.info(f"   Class: {el['cls'][:100]}")
            logger.info(f"   Title: {el['title']}")
            logger.info(f"   Text: {el['text'][:80]}")
            logger.info(f"   aria-label: {el['ariaLabel']}")
        
        logger.info("\n" + "="*100)
        logger.info("STEP 3: Search for toolbar/actions containers")
        logger.info("="*100)
        
        # Search for toolbar containers
        toolbars = await page.evaluate("""
            () => {
                return [...document.querySelectorAll('[class*="toolbar"], [class*="Toolbar"], [class*="actions"], [class*="Actions"]')]
                    .filter(el => {
                        const bounds = el.getBoundingClientRect();
                        return bounds.width > 0 && bounds.height > 0;
                    })
                    .map(el => ({
                        tag: el.tagName,
                        cls: el.className,
                        childCount: el.children.length,
                        y: Math.round(el.getBoundingClientRect().y)
                    }));
            }
        """)
        
        logger.info(f"Found {len(toolbars)} visible toolbar/actions containers")
        for i, toolbar in enumerate(toolbars, 1):
            logger.info(f"\n{i}. {toolbar['tag']} (Y={toolbar['y']})")
            logger.info(f"   Class: {toolbar['cls'][:100]}")
            logger.info(f"   Children: {toolbar['childCount']}")
        
        logger.info("\n" + "="*100)
        logger.info("STEP 4: Get ALL icons in the top 100px of viewport")
        logger.info("="*100)
        
        # Get icons in toolbar area (top of page)
        top_icons = await page.evaluate("""
            () => {
                return [...document.querySelectorAll('[class*="icon"]')]
                    .filter(el => {
                        const bounds = el.getBoundingClientRect();
                        return bounds.y >= 0 && bounds.y < 150 && bounds.width > 0;
                    })
                    .map(el => ({
                        tag: el.tagName,
                        cls: [...el.classList].join(' '),
                        ariaLabel: el.getAttribute('aria-label'),
                        title: el.getAttribute('title'),
                        y: Math.round(el.getBoundingClientRect().y),
                        x: Math.round(el.getBoundingClientRect().x)
                    }));
            }
        """)
        
        logger.info(f"Found {len(top_icons)} icons in top toolbar area")
        for i, icon in enumerate(top_icons, 1):
            logger.info(f"\n{i}. {icon['tag']} at ({icon['x']}, {icon['y']})")
            logger.info(f"   aria-label: {icon['ariaLabel']}")
            logger.info(f"   title: {icon['title']}")
            logger.info(f"   class: {icon['cls'][:80]}")
        
        # Save results
        results = {
            'change_image_elements': change_image_elements,
            'toolbars': toolbars,
            'top_icons': top_icons
        }
        
        with open('logo_addition_diagnostics/click_toolbar_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info("\n✅ Results saved to: logo_addition_diagnostics/click_toolbar_results.json")
        logger.info("="*100)

if __name__ == "__main__":
    asyncio.run(click_and_find_toolbar())
