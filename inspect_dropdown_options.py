#!/usr/bin/env python3
"""
Inspect Department Dropdown Options
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        pages = context.pages
        
        templates_page = None
        for page in pages:
            if 'templates/list' in page.url:
                templates_page = page
                break
        
        if not templates_page:
            print("❌ No templates page found")
            return
        
        await templates_page.bring_to_front()
        
        print("🔍 Opening dropdown...")
        await templates_page.click('.ant-dropdown-trigger')
        await asyncio.sleep(2)
        
        print("\n📋 Inspecting dropdown contents...\n")
        
        options = await templates_page.evaluate("""
            () => {
                const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                if (!dropdown) return {error: "Dropdown not found"};
                
                const result = {
                    html: dropdown.innerHTML.substring(0, 1000),
                    options: []
                };
                
                // Try different selectors
                const selectors = [
                    '.ant-dropdown-menu-item',
                    '[class*="menu-item"]',
                    'label',
                    'li',
                    'div'
                ];
                
                for (let selector of selectors) {
                    const elements = dropdown.querySelectorAll(selector);
                    if (elements.length > 0) {
                        result.options.push({
                            selector: selector,
                            count: elements.length,
                            texts: Array.from(elements).slice(0, 10).map(el => ({
                                text: el.textContent.trim(),
                                tagName: el.tagName,
                                className: el.className
                            }))
                        });
                    }
                }
                
                return result;
            }
        """)
        
        if options.get('error'):
            print(f"❌ {options['error']}")
        else:
            print("HTML Snippet:")
            print(options.get('html', 'No HTML'))
            print("\n" + "=" * 80)
            print("OPTIONS FOUND:")
            print("=" * 80)
            
            for opt_group in options['options']:
                print(f"\nSelector: {opt_group['selector']}")
                print(f"Count: {opt_group['count']}")
                print("\nTexts:")
                for item in opt_group['texts']:
                    print(f"  - {item['tagName']}: '{item['text'][:60]}'")
                    print(f"    Class: {item['className'][:80]}")
        
        await templates_page.keyboard.press('Escape')


if __name__ == "__main__":
    asyncio.run(main())
