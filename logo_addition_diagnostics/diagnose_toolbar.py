#!/usr/bin/env python3
"""
Diagnose why the toolbar doesn't appear after clicking a container
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    template_id = "667f0befd4964026ee7b6e46"  # RO Invoiced
    container_id = "6f0b8570-c4dc-45bd-b746-40e3af9af3bb"  # Logo 2 LEFT
    
    print("=" * 100)
    print(f"🔍 DIAGNOSING TOOLBAR ISSUE")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            pages = context.pages
            page = None
            
            for p in pages:
                if template_id in p.url:
                    page = p
                    break
            
            if not page:
                print(f"❌ Template not open. Please open the template first.")
                return
            
            print(f"📄 Using template: RO Invoiced ({template_id})")
            print(f"🎯 Target container: {container_id}\n")
            
            # Test different click methods
            print("=" * 100)
            print("TEST 1: JAVASCRIPT CLICK + FOCUS")
            print("=" * 100)
            
            await page.evaluate(f"""
                const el = document.querySelector('div.TEXT_TEMPLATE[id="{container_id}"][contenteditable="true"]');
                el.click();
                el.focus();
            """)
            
            print("✅ Executed JavaScript click + focus")
            print("⏳ Waiting 3 seconds for toolbar...")
            await asyncio.sleep(3)
            
            # Check if toolbar appeared
            toolbar_visible = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('.icon-insert-image'));
                    const visible = buttons.filter(btn => {
                        const rect = btn.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    });
                    return {
                        total: buttons.length,
                        visible: visible.length,
                        positions: visible.map(btn => {
                            const rect = btn.getBoundingClientRect();
                            return { top: rect.top, left: rect.left };
                        })
                    };
                }
            """)
            
            print(f"\n📊 RESULT:")
            print(f"   Total Insert Image buttons: {toolbar_visible['total']}")
            print(f"   Visible buttons: {toolbar_visible['visible']}")
            if toolbar_visible['visible'] > 0:
                print(f"   ✅ TOOLBAR APPEARED!")
                for i, pos in enumerate(toolbar_visible['positions'], 1):
                    print(f"      {i}. Top: {pos['top']:.1f}, Left: {pos['left']:.1f}")
            else:
                print(f"   ❌ TOOLBAR DID NOT APPEAR")
            
            print("\n" + "=" * 100)
            print("TEST 2: TRY PLAYWRIGHT CLICK (WITHOUT FORCE)")
            print("=" * 100)
            
            # First unfocus
            await page.evaluate("document.activeElement?.blur()")
            await asyncio.sleep(1)
            
            try:
                selector = f'div.TEXT_TEMPLATE[id="{container_id}"][contenteditable="true"]'
                await page.click(selector, timeout=5000)
                print("✅ Playwright click succeeded")
            except Exception as e:
                print(f"❌ Playwright click failed: {e}")
            
            print("⏳ Waiting 3 seconds for toolbar...")
            await asyncio.sleep(3)
            
            toolbar_visible2 = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('.icon-insert-image'));
                    const visible = buttons.filter(btn => {
                        const rect = btn.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    });
                    return visible.length;
                }
            """)
            
            print(f"\n📊 RESULT:")
            print(f"   Visible Insert Image buttons: {toolbar_visible2}")
            if toolbar_visible2 > 0:
                print(f"   ✅ TOOLBAR APPEARED!")
            else:
                print(f"   ❌ TOOLBAR DID NOT APPEAR")
            
            print("\n" + "=" * 100)
            print("TEST 3: CHECK CONTAINER PROPERTIES")
            print("=" * 100)
            
            container_info = await page.evaluate(f"""
                () => {{
                    const el = document.querySelector('div.TEXT_TEMPLATE[id="{container_id}"][contenteditable="true"]');
                    if (!el) return {{ exists: false }};
                    
                    const rect = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    
                    return {{
                        exists: true,
                        rect: {{
                            width: rect.width,
                            height: rect.height,
                            top: rect.top,
                            left: rect.left
                        }},
                        styles: {{
                            display: styles.display,
                            visibility: styles.visibility,
                            opacity: styles.opacity,
                            pointerEvents: styles.pointerEvents
                        }},
                        isFocused: document.activeElement === el,
                        contenteditable: el.getAttribute('contenteditable'),
                        innerHTML: el.innerHTML
                    }};
                }}
            """)
            
            if container_info['exists']:
                print(f"✅ Container exists")
                print(f"   Rect: {container_info['rect']}")
                print(f"   Styles: {container_info['styles']}")
                print(f"   Is Focused: {container_info['isFocused']}")
                print(f"   Contenteditable: {container_info['contenteditable']}")
                print(f"   HTML: {container_info['innerHTML']}")
            else:
                print(f"❌ Container not found!")
            
            print("\n" + "=" * 100)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
