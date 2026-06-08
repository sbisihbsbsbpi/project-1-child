#!/usr/bin/env python3
"""
Inspect Icon - Check what the icon inside ImageComponent is
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect_icon():
    """Inspect the icon that's inside the ImageComponent"""
    
    print("="*100)
    print("🔍 INSPECTING ICON INSIDE IMAGE COMPONENT")
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
        
        # Inspect the icon
        icon_info = await page.evaluate("""
            () => {
                const imageComponent = document.querySelector('[class*="Image_imageComponent"]');
                if (!imageComponent) return null;
                
                const icon = imageComponent.querySelector('svg, [class*="icon"], [class*="Icon"]');
                if (!icon) return null;
                
                // Get all details about this icon
                const rect = icon.getBoundingClientRect();
                const style = window.getComputedStyle(icon);
                
                // Check if it's clickable
                const parent = icon.parentElement;
                const isButton = parent && parent.tagName === 'BUTTON';
                const hasClickHandler = icon.onclick !== null || parent.onclick !== null;
                
                // Get the icon's purpose from aria-label or title
                const purpose = icon.getAttribute('aria-label') || 
                              icon.getAttribute('title') ||
                              parent.getAttribute('aria-label') ||
                              parent.getAttribute('title') ||
                              '';
                
                return {
                    tagName: icon.tagName,
                    className: icon.className,
                    visible: rect.width > 0 && rect.height > 0,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    top: Math.round(rect.top),
                    left: Math.round(rect.left),
                    cursor: style.cursor,
                    parentTag: parent ? parent.tagName : null,
                    parentClass: parent ? parent.className : null,
                    isButton: isButton,
                    hasClickHandler: hasClickHandler,
                    purpose: purpose,
                    ariaHidden: icon.getAttribute('aria-hidden'),
                    // Get siblings
                    siblingCount: parent ? parent.children.length : 0
                };
            }
        """)
        
        if not icon_info:
            print("❌ No icon found")
            return
        
        print(f"\n📊 ICON DETAILS:")
        print(f"   Tag: {icon_info['tagName']}")
        print(f"   Class: {icon_info['className'][:80] if icon_info['className'] else '(none)'}")
        print(f"   Size: {icon_info['width']}x{icon_info['height']}px")
        print(f"   Position: top={icon_info['top']}px, left={icon_info['left']}px")
        print(f"   Visible: {icon_info['visible']}")
        print(f"   Cursor: {icon_info['cursor']}")
        print(f"   Aria-hidden: {icon_info['ariaHidden']}")
        print(f"   Purpose: {icon_info['purpose'] or '(no label)'}")
        print(f"\n   Parent: {icon_info['parentTag']} (class: {icon_info['parentClass'][:60] if icon_info['parentClass'] else '(none)'})")
        print(f"   Is button: {icon_info['isButton']}")
        print(f"   Has click handler: {icon_info['hasClickHandler']}")
        print(f"   Siblings: {icon_info['siblingCount']}")
        
        # Try clicking the icon
        print(f"\n🔍 Trying to click the icon...")
        
        try:
            # Try clicking the icon itself
            await page.click('[class*="Image_imageComponent"] svg', timeout=2000)
            await page.wait_for_timeout(1500)
            print(f"   ✓ Clicked icon")
            
            # Check if anything opened
            modals = await page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll('[role="dialog"], [class*="Modal"], [class*="Drawer"]');
                    return {
                        count: dialogs.length,
                        visible: Array.from(dialogs).filter(d => d.offsetParent !== null).length
                    };
                }
            """)
            
            print(f"   Modals after click: {modals['count']} total, {modals['visible']} visible")
            
            if modals['visible'] > 0:
                print(f"   ✅ A modal opened!")
                
                # Extract what's in the modal
                modal_content = await page.evaluate("""
                    () => {
                        const dialogs = Array.from(document.querySelectorAll('[role="dialog"], [class*="Modal"], [class*="Drawer"]'))
                            .filter(d => d.offsetParent !== null);
                        
                        if (dialogs.length === 0) return null;
                        
                        const modal = dialogs[dialogs.length - 1];
                        return {
                            title: modal.querySelector('h1, h2, h3, [class*="title"]')?.textContent.trim() || '',
                            buttons: Array.from(modal.querySelectorAll('button'))
                                .map(b => b.textContent.trim())
                                .filter(t => t.length > 0),
                            images: modal.querySelectorAll('img').length
                        };
                    }
                """)
                
                if modal_content:
                    print(f"\n   📋 Modal Content:")
                    print(f"      Title: {modal_content['title'] or '(no title)'}")
                    print(f"      Images: {modal_content['images']}")
                    print(f"      Buttons: {modal_content['buttons'][:5]}")
                
            else:
                print(f"   ℹ️  No modal opened")
            
        except Exception as e:
            print(f"   ❌ Click failed: {e}")
        
        # Also try clicking the parent button if it exists
        if icon_info['isButton']:
            print(f"\n🔍 Icon's parent is a button, trying to click that...")
            
            try:
                await page.click('[class*="Image_imageComponent"] button', timeout=2000)
                await page.wait_for_timeout(1500)
                print(f"   ✓ Clicked parent button")
                
                modals2 = await page.evaluate("""
                    () => {
                        const dialogs = document.querySelectorAll('[role="dialog"], [class*="Modal"], [class*="Drawer"]');
                        return Array.from(dialogs).filter(d => d.offsetParent !== null).length;
                    }
                """)
                
                print(f"   Modals visible: {modals2}")
                
            except Exception as e:
                print(f"   ❌ Button click failed: {e}")
        
        print("\n" + "="*100)
        print("✅ Inspection complete!")
        print("="*100)

if __name__ == "__main__":
    asyncio.run(inspect_icon())
