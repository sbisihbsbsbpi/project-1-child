#!/usr/bin/env python3
"""Quick script to find templates with logo warnings"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Known template with logos
        template_id = "667f0befd4964026ee7b6ea2"
        
        page = await context.new_page()
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        print(f"Checking: {url}")
        
        await page.goto(url, wait_until='domcontentloaded')
        await asyncio.sleep(5)
        
        result = await page.evaluate("""
            () => {
                const warnings = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                return {
                    count: warnings.length,
                    found: warnings.length > 0
                };
            }
        """)
        
        print(f"Result: {result}")
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
