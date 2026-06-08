#!/usr/bin/env python3
"""
Debug Media Library - Figure out how to open the media library modal
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_media_library():
    """Debug the media library opening process"""
    
    print("="*100)
    print("🔍 DEBUG: Media Library Modal Opening")
    print("="*100)
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        pages = [p for p in context.pages if "/templates/edit/" in p.url]
        
        if not pages:
            print("❌ No template pages found")
            return
        
        page = pages[0]
        print(f"\n📄 Page: {page.url[:80]}")
        
        # Step 1: Check what's on the page
        print("\n🔍 Step 1: Inspecting page state...")
        state = await page.evaluate("""
            () => {
                const containers = document.querySelectorAll('[data-learned-logo]');
                const info = {
                    containers: containers.length,
                    buttons: []
                };
                
                if (containers.length > 0) {
                    const container = containers[0];
                    const img = container.querySelector('img');
                    
                    // Try to find buttons
                    const allButtons = Array.from(document.querySelectorAll('button'));
                    info.buttons = allButtons.map(btn => ({
                        text: btn.textContent.trim().substring(0, 50),
                        visible: btn.offsetParent !== null,
                        className: btn.className
                    })).filter(b => b.text.length > 0).slice(0, 20);
                }
                
                return info;
            }
        """)
        
        print(f"   Containers: {state['containers']}")
        print(f"   Visible buttons: {len([b for b in state['buttons'] if b['visible']])}")
        print("\n   First 5 buttons:")
        for btn in state['buttons'][:5]:
            print(f"      - '{btn['text']}' (visible: {btn['visible']})")
        
        # Step 2: Try to hover and see what appears
        print("\n🔍 Step 2: Hovering over logo...")
        await page.evaluate("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (container) {
                    const img = container.querySelector('img');
                    if (img) {
                        // Dispatch mouse events
                        img.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                        img.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                        
                        // Also try on container
                        container.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                        container.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                    }
                }
            }
        """)
        
        await page.wait_for_timeout(1000)
        
        # Check what buttons appeared
        after_hover = await page.evaluate("""
            () => {
                const allButtons = Array.from(document.querySelectorAll('button'));
                return allButtons
                    .filter(btn => btn.offsetParent !== null)
                    .map(btn => btn.textContent.trim().substring(0, 50))
                    .filter(text => text.length > 0);
            }
        """)
        
        print(f"   Visible buttons after hover: {len(after_hover)}")
        for btn in after_hover[:10]:
            print(f"      - '{btn}'")
        
        # Step 3: Try to find and click image controls
        print("\n🔍 Step 3: Looking for image control buttons...")
        
        control_buttons = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (!container) return [];
                
                // Look for buttons near the image
                const nearbyButtons = [];
                const allButtons = document.querySelectorAll('button');
                
                allButtons.forEach(btn => {
                    const text = btn.textContent.toLowerCase();
                    if (text.includes('change') || 
                        text.includes('edit') || 
                        text.includes('replace') ||
                        text.includes('image')) {
                        nearbyButtons.push({
                            text: btn.textContent.trim(),
                            visible: btn.offsetParent !== null,
                            hasIcon: btn.querySelector('svg, [class*="icon"]') !== null
                        });
                    }
                });
                
                return nearbyButtons;
            }
        """)
        
        print(f"   Found {len(control_buttons)} image control buttons:")
        for btn in control_buttons:
            print(f"      - '{btn['text']}' (visible: {btn['visible']}, hasIcon: {btn['hasIcon']})")
        
        # Step 4: Check for click handlers on the image itself
        print("\n🔍 Step 4: Checking if image itself is clickable...")
        
        clickable = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (!container) return false;
                
                const img = container.querySelector('img');
                if (!img) return false;
                
                // Check for click handlers
                const hasOnClick = img.onclick !== null;
                const hasEventListener = img.hasAttribute('onclick');
                const isClickable = img.style.cursor === 'pointer' || 
                                   window.getComputedStyle(img).cursor === 'pointer';
                
                return {
                    hasOnClick,
                    hasEventListener,
                    isClickable,
                    cursor: window.getComputedStyle(img).cursor
                };
            }
        """)
        
        print(f"   Image clickable: {clickable}")
        
        # Step 5: Try clicking the image
        print("\n🔍 Step 5: Trying to click the image...")
        
        try:
            await page.click('[data-learned-logo] img', timeout=2000)
            await page.wait_for_timeout(2000)
            print("   ✓ Clicked image")
        except Exception as e:
            print(f"   ✗ Click failed: {e}")
        
        # Check if modal opened
        modal_check = await page.evaluate("""
            () => {
                const modals = document.querySelectorAll('[role="dialog"], [class*="Modal"], [class*="Drawer"]');
                return {
                    count: modals.length,
                    classes: Array.from(modals).map(m => m.className)
                };
            }
        """)
        
        print(f"\n   Modals after click: {modal_check['count']}")
        if modal_check['count'] > 0:
            print(f"   Modal classes: {modal_check['classes']}")
        
        print("\n" + "="*100)
        print("✅ Debug complete! Check the browser to see what happened.")
        print("="*100)

if __name__ == "__main__":
    asyncio.run(debug_media_library())
