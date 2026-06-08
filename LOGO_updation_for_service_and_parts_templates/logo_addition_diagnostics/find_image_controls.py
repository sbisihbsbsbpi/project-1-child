#!/usr/bin/env python3
"""
Find Image Controls - Discover how to properly interact with image controls
"""

import asyncio
from playwright.async_api import async_playwright

async def find_controls():
    """Find the actual image controls and how to trigger them"""
    
    print("="*100)
    print("🔍 FINDING IMAGE CONTROLS - Deep Dive")
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
        
        # Method 1: Look for the ImageComponent wrapper
        print("\n🔍 Method 1: Looking for ImageComponent controls...")
        
        image_component_info = await page.evaluate("""
            () => {
                const imageComponents = document.querySelectorAll('[class*="Image_imageComponent"]');
                const info = [];
                
                imageComponents.forEach((comp, idx) => {
                    const img = comp.querySelector('img');
                    if (!img) return;
                    
                    // Look for sibling/child elements that might be controls
                    const allButtons = comp.querySelectorAll('button, [role="button"], [class*="button"]');
                    const allIcons = comp.querySelectorAll('svg, [class*="icon"], [class*="Icon"]');
                    
                    info.push({
                        index: idx,
                        hasImage: true,
                        imageFilename: img.src.split('/').pop().split('?')[0],
                        buttonsInside: allButtons.length,
                        iconsInside: allIcons.length,
                        className: comp.className,
                        // Get all children tags
                        childTags: Array.from(comp.children).map(c => c.tagName),
                        // Check for overlay/controls divs
                        hasOverlay: comp.querySelector('[class*="overlay"], [class*="control"], [class*="toolbar"]') !== null
                    });
                });
                
                return info;
            }
        """)
        
        print(f"   Found {len(image_component_info)} ImageComponent elements:")
        for comp in image_component_info[:3]:
            print(f"\n   Component {comp['index']}:")
            print(f"      Image: {comp['imageFilename']}")
            print(f"      Buttons inside: {comp['buttonsInside']}")
            print(f"      Icons inside: {comp['iconsInside']}")
            print(f"      Has overlay: {comp['hasOverlay']}")
            print(f"      Children: {comp['childTags']}")
        
        # Method 2: Try actual Playwright hover on the image
        print(f"\n🔍 Method 2: Using Playwright's real hover (not JS events)...")
        
        try:
            # Use Playwright's actual hover method
            selector = '[data-learned-logo] img'
            print(f"   → Hovering on: {selector}")
            await page.hover(selector, timeout=5000)
            await page.wait_for_timeout(2000)
            
            # Now check what appeared
            controls_appeared = await page.evaluate("""
                () => {
                    // Look for any recently shown buttons/controls
                    const visibleButtons = Array.from(document.querySelectorAll('button'))
                        .filter(btn => {
                            const style = window.getComputedStyle(btn);
                            return style.display !== 'none' && 
                                   style.visibility !== 'hidden' && 
                                   style.opacity !== '0' &&
                                   btn.offsetParent !== null;
                        })
                        .map(btn => ({
                            text: btn.textContent.trim().substring(0, 50),
                            ariaLabel: btn.getAttribute('aria-label'),
                            className: btn.className,
                            hasIcon: btn.querySelector('svg') !== null
                        }));
                    
                    // Look for tooltips/popovers that might have appeared
                    const tooltips = Array.from(document.querySelectorAll('[role="tooltip"], [class*="tooltip"], [class*="popover"]'))
                        .map(t => ({
                            text: t.textContent.trim().substring(0, 100),
                            visible: t.offsetParent !== null
                        }));
                    
                    return {
                        buttons: visibleButtons,
                        tooltips: tooltips.filter(t => t.visible)
                    };
                }
            """)
            
            print(f"\n   Visible buttons after hover: {len(controls_appeared['buttons'])}")
            for btn in controls_appeared['buttons'][:10]:
                label = btn['ariaLabel'] or btn['text'] or '(no text)'
                print(f"      - {label} {('🎨' if btn['hasIcon'] else '')}")
            
            if controls_appeared['tooltips']:
                print(f"\n   Tooltips appeared: {len(controls_appeared['tooltips'])}")
                for tt in controls_appeared['tooltips'][:5]:
                    print(f"      - {tt['text']}")
            
        except Exception as e:
            print(f"   ❌ Hover failed: {e}")
        
        # Method 3: Look for context menu or right-click options
        print(f"\n🔍 Method 3: Checking for context menu...")
        
        try:
            await page.click('[data-learned-logo] img', button='right', timeout=2000)
            await page.wait_for_timeout(1000)
            
            context_menu = await page.evaluate("""
                () => {
                    const menus = document.querySelectorAll('[role="menu"], [class*="menu"], [class*="Menu"], [class*="context"]');
                    return Array.from(menus)
                        .filter(m => m.offsetParent !== null)
                        .map(m => ({
                            items: Array.from(m.querySelectorAll('[role="menuitem"], li, button'))
                                .map(item => item.textContent.trim())
                                .filter(text => text.length > 0)
                        }));
                }
            """)
            
            if context_menu and len(context_menu) > 0:
                print(f"   ✅ Context menu appeared with {context_menu[0]['items'].length} items:")
                for item in context_menu[0]['items'][:10]:
                    print(f"      - {item}")
            else:
                print(f"   ❌ No context menu appeared")
            
            # Close context menu
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
        except Exception as e:
            print(f"   ❌ Right-click failed: {e}")
        
        # Method 4: Look for the resizable wrapper controls
        print(f"\n🔍 Method 4: Checking resizable wrapper for handles...")
        
        resizable_info = await page.evaluate("""
            () => {
                const resizables = document.querySelectorAll('[class*="resizable"]');
                const info = [];
                
                resizables.forEach(r => {
                    const hasImg = r.querySelector('img') !== null;
                    if (!hasImg) return;
                    
                    // Look for resize handles
                    const handles = r.querySelectorAll('[class*="handle"], [class*="Handle"], [style*="cursor"]');
                    
                    // Look for action buttons that might appear on selection
                    const actionBtns = r.querySelectorAll('button, [role="button"]');
                    
                    info.push({
                        className: r.className,
                        handles: handles.length,
                        actionButtons: actionBtns.length,
                        isSelected: r.className.includes('selected') || r.className.includes('Selected')
                    });
                });
                
                return info;
            }
        """)
        
        print(f"   Found {len(resizable_info)} resizable wrappers:")
        for r in resizable_info[:3]:
            print(f"      - Handles: {r['handles']}, Buttons: {r['actionButtons']}, Selected: {r['isSelected']}")
        
        # Method 5: Try clicking directly on the image to select it
        print(f"\n🔍 Method 5: Clicking image to select it...")
        
        try:
            await page.click('[data-learned-logo] img', timeout=2000)
            await page.wait_for_timeout(1000)
            
            # Check if image got selected and controls appeared
            selection_state = await page.evaluate("""
                () => {
                    const container = document.querySelector('[data-learned-logo]');
                    if (!container) return null;
                    
                    // Walk up to find if any parent has "selected" class
                    let current = container;
                    let depth = 0;
                    while (current && depth < 10) {
                        if (current.className && 
                            (current.className.includes('selected') || 
                             current.className.includes('Selected') ||
                             current.className.includes('active'))) {
                            return {
                                selected: true,
                                element: current.tagName,
                                className: current.className
                            };
                        }
                        current = current.parentElement;
                        depth++;
                    }
                    
                    return { selected: false };
                }
            """)
            
            if selection_state and selection_state['selected']:
                print(f"   ✅ Image selected! Element: <{selection_state['element']}>")
                print(f"      Class: {selection_state['className'][:80]}")
            else:
                print(f"   ℹ️  Image might not show selection state")
            
        except Exception as e:
            print(f"   ❌ Click failed: {e}")
        
        print("\n" + "="*100)
        print("💡 TIP: Manually hover over a logo in the browser and observe what happens!")
        print("   Then run this script again to see if we can detect those controls.")
        print("="*100)

if __name__ == "__main__":
    asyncio.run(find_controls())
