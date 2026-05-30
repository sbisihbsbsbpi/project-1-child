#!/usr/bin/env python3
"""
Highlight the dealer logo elements on the template edit page
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
        
        # Use existing tab
        page = context.pages[0]
        await page.bring_to_front()
        
        print("🎨 Highlighting DEALER LOGO elements...")
        print("=" * 80)
        
        # Inject highlighting script
        result = await page.evaluate("""
            () => {
                // Find all elements with ID='DEALER_LOGO'
                const dealerLogos = document.querySelectorAll('[id="DEALER_LOGO"]');
                
                // Find elements with logo-related classes
                const logoIcons = document.querySelectorAll('[class*="dealership-logo"], [class*="icon-dealership"]');
                
                const results = [];
                let highlightIndex = 1;
                
                // Highlight DEALER_LOGO elements
                dealerLogos.forEach((el) => {
                    // Add red border
                    el.style.border = '3px solid red';
                    el.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.8)';
                    el.style.position = 'relative';
                    el.style.zIndex = '10000';
                    
                    // Add badge
                    const badge = document.createElement('div');
                    badge.textContent = highlightIndex;
                    badge.style.cssText = `
                        position: absolute;
                        top: -15px;
                        left: -15px;
                        background: red;
                        color: white;
                        border-radius: 50%;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 16px;
                        z-index: 10001;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    `;
                    el.appendChild(badge);
                    
                    const rect = el.getBoundingClientRect();
                    results.push({
                        index: highlightIndex,
                        type: 'DEALER_LOGO',
                        id: el.id,
                        className: el.className.substring(0, 60),
                        size: `${rect.width.toFixed(0)}x${rect.height.toFixed(0)}px`,
                        position: `top=${rect.top.toFixed(0)}px, left=${rect.left.toFixed(0)}px`,
                        text: el.textContent?.trim().substring(0, 50) || ''
                    });
                    
                    highlightIndex++;
                });
                
                // Highlight logo icons (different color)
                logoIcons.forEach((el) => {
                    if (!el.closest('[id="DEALER_LOGO"]')) {
                        el.style.border = '2px solid orange';
                        el.style.boxShadow = '0 0 8px rgba(255, 165, 0, 0.6)';
                        
                        const rect = el.getBoundingClientRect();
                        results.push({
                            index: highlightIndex,
                            type: 'LOGO_ICON',
                            className: el.className.substring(0, 60),
                            size: `${rect.width.toFixed(0)}x${rect.height.toFixed(0)}px`,
                            position: `top=${rect.top.toFixed(0)}px, left=${rect.left.toFixed(0)}px`
                        });
                        
                        highlightIndex++;
                    }
                });
                
                return results;
            }
        """)
        
        print(f"\n✅ Highlighted {len(result)} logo elements:\n")
        
        for item in result:
            if item['type'] == 'DEALER_LOGO':
                print(f"🔴 {item['index']}. DEALER LOGO (Red border)")
                print(f"     ID: {item['id']}")
                print(f"     Class: {item['className']}")
                print(f"     Size: {item['size']}")
                print(f"     Position: {item['position']}")
                if item.get('text'):
                    print(f"     Text: {item['text']}")
            else:
                print(f"🟠 {item['index']}. Logo Icon (Orange border)")
                print(f"     Class: {item['className']}")
                print(f"     Size: {item['size']}")
                print(f"     Position: {item['position']}")
            print()
        
        print("=" * 80)
        print("✅ Logo elements are now highlighted with:")
        print("   🔴 Red borders + numbered badges = DEALER_LOGO elements")
        print("   🟠 Orange borders = Logo icons")
        print("\n📸 Taking screenshot...")
        
        await page.screenshot(path='template_logo_highlighted.png', full_page=True)
        print("✅ Screenshot saved: template_logo_highlighted.png")
        
        print("\n💡 The highlights will remain until you refresh the page.")


if __name__ == "__main__":
    asyncio.run(main())
