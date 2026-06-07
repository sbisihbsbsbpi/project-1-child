#!/usr/bin/env python3
"""
Get detailed information about the current template
"""

import asyncio
from playwright.async_api import async_playwright

async def get_info():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        if not context.pages:
            print("❌ No pages found")
            return
        
        page = context.pages[0]
        
        result = await page.evaluate("""
            () => {
                return {
                    url: window.location.href,
                    title: document.title,
                    templateName: document.querySelector('h1, [class*="templateName"]')?.textContent || 'Unknown',
                    dealershipInfo: document.querySelector('[class*="dealership"]')?.textContent || 'Unknown',
                    bodyText: document.body.textContent.substring(0, 500)
                };
            }
        """)
        
        print("=" * 100)
        print("📄 CURRENT TEMPLATE INFORMATION")
        print("=" * 100)
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print(f"Template Name: {result['templateName']}")
        print(f"Dealership: {result['dealershipInfo']}")
        print()
        print("Body Preview:")
        print(result['bodyText'])
        print("=" * 100)

if __name__ == "__main__":
    asyncio.run(get_info())
