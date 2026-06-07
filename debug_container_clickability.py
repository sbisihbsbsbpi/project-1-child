#!/usr/bin/env python3
"""
Debug why Logo 1 LEFT container is not clickable
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_container():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        if context.pages:
            page = context.pages[0]
        else:
            print("❌ No pages found")
            return
        
        print("🔍 Debugging container clickability...")
        print("=" * 80)
        
        container_id = "6f0b8570-c4dc-45bd-b746-40e3af9af3bb"
        
        result = await page.evaluate(f"""
            () => {{
                const container = document.querySelector('div.TEXT_TEMPLATE[id="{container_id}"]');
                
                if (!container) {{
                    return {{ found: false }};
                }}
                
                const rect = container.getBoundingClientRect();
                const style = window.getComputedStyle(container);
                const parent = container.parentElement;
                const parentStyle = parent ? window.getComputedStyle(parent) : null;
                
                // Check if element at center point is the container
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const elementAtPoint = document.elementFromPoint(centerX, centerY);
                const isClickable = elementAtPoint === container || container.contains(elementAtPoint);
                
                return {{
                    found: true,
                    position: {{
                        top: Math.round(rect.top + window.scrollY),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }},
                    visibility: {{
                        display: style.display,
                        visibility: style.visibility,
                        opacity: style.opacity,
                        zIndex: style.zIndex
                    }},
                    parent: {{
                        tag: parent ? parent.tagName : null,
                        className: parent ? parent.className : null,
                        display: parentStyle ? parentStyle.display : null,
                        visibility: parentStyle ? parentStyle.visibility : null
                    }},
                    clickable: {{
                        isClickable: isClickable,
                        elementAtPoint: elementAtPoint ? elementAtPoint.tagName + '.' + elementAtPoint.className : null
                    }},
                    attributes: {{
                        contenteditable: container.getAttribute('contenteditable'),
                        id: container.id,
                        className: container.className
                    }}
                }};
            }}
        """)
        
        if not result['found']:
            print("❌ Container not found!")
            return
        
        print(f"✅ Container found!")
        print()
        print(f"📍 Position:")
        print(f"   Top: {result['position']['top']}px")
        print(f"   Left: {result['position']['left']}px")
        print(f"   Size: {result['position']['width']}x{result['position']['height']}px")
        print()
        print(f"👁️  Visibility:")
        print(f"   Display: {result['visibility']['display']}")
        print(f"   Visibility: {result['visibility']['visibility']}")
        print(f"   Opacity: {result['visibility']['opacity']}")
        print(f"   Z-Index: {result['visibility']['zIndex']}")
        print()
        print(f"👪 Parent:")
        print(f"   Tag: {result['parent']['tag']}")
        print(f"   Class: {result['parent']['className'][:80] if result['parent']['className'] else 'None'}")
        print(f"   Display: {result['parent']['display']}")
        print(f"   Visibility: {result['parent']['visibility']}")
        print()
        print(f"🖱️  Clickability:")
        print(f"   Is Clickable: {result['clickable']['isClickable']}")
        print(f"   Element at center point: {result['clickable']['elementAtPoint']}")
        print()
        print(f"📋 Attributes:")
        print(f"   Contenteditable: {result['attributes']['contenteditable']}")
        print(f"   ID: {result['attributes']['id']}")
        print(f"   Class: {result['attributes']['className']}")
        print()
        
        if not result['clickable']['isClickable']:
            print("❌ ISSUE FOUND: Container is NOT clickable!")
            print(f"   Something else is covering it: {result['clickable']['elementAtPoint']}")
        else:
            print("✅ Container appears to be clickable")
        
        print()
        print("💡 Recommendation:")
        if result['position']['top'] < 0:
            print("   Container is OFF-SCREEN (negative top position)")
            print("   → Need to scroll it into view before clicking")
        elif not result['clickable']['isClickable']:
            print("   Container is covered by another element")
            print("   → Need to remove overlay or use JavaScript click")

        # Now check what toolbar buttons are available
        print()
        print("=" * 80)
        print("🔍 Checking available toolbar buttons...")
        print("=" * 80)

        toolbar_result = await page.evaluate("""
            () => {
                const allIcons = Array.from(document.querySelectorAll('[class*="icon-"]'));
                const visibleIcons = allIcons.filter(icon => {
                    const style = window.getComputedStyle(icon);
                    const rect = icon.getBoundingClientRect();
                    return style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0' &&
                           rect.width > 0 && rect.height > 0;
                });

                return visibleIcons.map(icon => ({
                    className: icon.className,
                    ariaLabel: icon.getAttribute('aria-label'),
                    parent: icon.parentElement ? icon.parentElement.className : null
                }));
            }
        """)

        print(f"Found {len(toolbar_result)} visible icon buttons:")
        for icon in toolbar_result[:20]:  # Show first 20
            print(f"   • {icon['ariaLabel'] or icon['className']}")

        # Check specifically for insert-image icon
        has_insert = any('insert-image' in (icon.get('ariaLabel') or icon.get('className') or '') for icon in toolbar_result)
        print()
        if has_insert:
            print("✅ Insert Image button IS available!")
        else:
            print("❌ Insert Image button NOT found!")
            print("   Available insert-related icons:")
            insert_related = [icon for icon in toolbar_result if 'insert' in (icon.get('ariaLabel') or icon.get('className') or '').lower()]
            for icon in insert_related:
                print(f"      • {icon['ariaLabel'] or icon['className']}")

if __name__ == "__main__":
    asyncio.run(debug_container())
