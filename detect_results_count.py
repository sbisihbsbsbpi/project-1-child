#!/usr/bin/env python3
"""
Detect the results count text after filtering
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
        
        # Find templates page
        page = None
        for p in context.pages:
            if 'templates/list' in p.url:
                page = p
                break
        
        if not page:
            print("❌ Templates page not found")
            return
        
        await page.bring_to_front()
        
        print("🔍 Looking for results count text...")
        
        # Wait a bit for page to be stable
        await asyncio.sleep(2)
        
        # Search for results text
        results_info = await page.evaluate("""
            () => {
                const results = [];
                
                // Look for text containing "Result"
                const allElements = document.querySelectorAll('*');
                
                for (let el of allElements) {
                    const text = el.textContent.trim();
                    
                    // Check for patterns like "11 Result(s)", "X results", etc.
                    if (text.match(/\\d+\\s*(Result|result|Results|RESULTS)/)) {
                        // Only leaf nodes
                        if (el.children.length === 0 || el.children.length === 1) {
                            results.push({
                                text: text,
                                tagName: el.tagName,
                                className: el.className,
                                visible: el.offsetParent !== null
                            });
                        }
                    }
                }
                
                return results;
            }
        """)
        
        print(f"\n📊 Found {len(results_info)} elements with 'Result' text:\n")
        
        for i, result in enumerate(results_info, 1):
            visible = "✅ VISIBLE" if result['visible'] else "❌ HIDDEN"
            print(f"{i}. {visible}")
            print(f"   Text: {result['text'][:100]}")
            print(f"   Tag: {result['tagName']}")
            print(f"   Class: {result['className'][:80]}")
            print()
        
        # Also check for the active tab count
        tab_info = await page.evaluate("""
            () => {
                const activeTab = document.querySelector('[role="tab"][aria-selected="true"]');
                if (activeTab) {
                    const text = activeTab.textContent.trim();
                    const match = text.match(/(\\w+)\\s*\\((\\d+)\\)/);
                    return {
                        fullText: text,
                        tabName: match ? match[1] : null,
                        count: match ? parseInt(match[2]) : null
                    };
                }
                return null;
            }
        """)
        
        if tab_info:
            print("📑 Active Tab Info:")
            print(f"   Full Text: {tab_info['fullText']}")
            print(f"   Tab Name: {tab_info['tabName']}")
            print(f"   Count: {tab_info['count']}")


if __name__ == "__main__":
    asyncio.run(main())
