"""
Run the exact JavaScript queries suggested to find the "Change Image" toolbar icon.
This automates the browser console investigation.
"""

import asyncio
from playwright.async_api import async_playwright
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def find_toolbar():
    """Find the Change Image toolbar using browser console queries"""
    
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
        logger.info("QUERY 1: All elements with 'icon' in class names")
        logger.info("="*100)
        
        # Query 1: All icon elements
        icon_elements = await page.evaluate("""
            () => {
                return [...document.querySelectorAll('[class]')]
                    .filter(el => [...el.classList].some(c => c.includes('icon')))
                    .map(el => ({
                        tag: el.tagName,
                        classes: [...el.classList].join(' '),
                        text: (el.innerText || '').trim().substring(0, 80)
                    }));
            }
        """)
        
        logger.info(f"Found {len(icon_elements)} elements with 'icon' in classes")
        for i, el in enumerate(icon_elements[:20], 1):  # Show first 20
            logger.info(f"{i}. {el['tag']}: {el['classes'][:80]}")
            if el['text']:
                logger.info(f"   Text: {el['text']}")
        
        logger.info("\n" + "="*100)
        logger.info("QUERY 2: Elements containing 'Change Image' text")
        logger.info("="*100)
        
        # Query 2: Search for "Change Image" text
        change_image_elements = await page.evaluate("""
            () => {
                return [...document.querySelectorAll('*')]
                    .filter(el => (el.innerText || '').includes('Change Image'))
                    .map(el => ({
                        tag: el.tagName,
                        cls: el.className,
                        text: el.innerText.trim().substring(0, 100)
                    }));
            }
        """)
        
        logger.info(f"Found {len(change_image_elements)} elements with 'Change Image' text")
        for i, el in enumerate(change_image_elements, 1):
            logger.info(f"\n{i}. {el['tag']}")
            logger.info(f"   Class: {el['cls'][:100]}")
            logger.info(f"   Text: {el['text']}")
        
        logger.info("\n" + "="*100)
        logger.info("QUERY 3: Detailed icon table")
        logger.info("="*100)
        
        # Query 3: Detailed icon search
        detailed_icons = await page.evaluate("""
            () => {
                const matches = [...document.querySelectorAll('[class]')].filter(el =>
                    [...el.classList].some(c =>
                        c.includes('icon-insert-image') ||
                        c.includes('icon-dealership-logo') ||
                        c.includes('icon-cover-image') ||
                        c.includes('icon')
                    )
                );
                
                return matches.map(el => ({
                    tag: el.tagName,
                    className: [...el.classList].join(' '),
                    text: (el.innerText || '').trim().slice(0, 80),
                    ariaLabel: el.getAttribute('aria-label'),
                    title: el.getAttribute('title')
                }));
            }
        """)
        
        logger.info(f"Found {len(detailed_icons)} detailed icon matches")
        
        # Save full results
        results = {
            'icon_elements': icon_elements,
            'change_image_elements': change_image_elements,
            'detailed_icons': detailed_icons
        }
        
        with open('logo_addition_diagnostics/toolbar_search_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info("\n✅ Full results saved to: logo_addition_diagnostics/toolbar_search_results.json")
        
        # Try to highlight icons visually
        logger.info("\n" + "="*100)
        logger.info("Highlighting all icon elements with red outline...")
        logger.info("="*100)
        
        await page.evaluate("""
            () => {
                [...document.querySelectorAll('[class*="icon"]')].forEach(el => {
                    el.style.outline = '2px solid red';
                    el.style.outlineOffset = '2px';
                });
            }
        """)
        
        logger.info("✅ Icons highlighted! Check the browser window.")
        logger.info("\n" + "="*100)

if __name__ == "__main__":
    asyncio.run(find_toolbar())
