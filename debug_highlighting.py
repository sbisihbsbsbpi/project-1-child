#!/usr/bin/env python3
"""
Debug Highlighting - Check why some elements don't show red highlight
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    print("=" * 100)
    print("🔍 DEBUGGING HIGHLIGHT ISSUES")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        await asyncio.sleep(2)
        
        # Test highlighting on all elements
        result = await page.evaluate("""
            () => {
                if (!window.navElements) {
                    return { error: 'Navigator not loaded' };
                }
                
                const issues = [];
                
                window.navElements.forEach((item, idx) => {
                    const el = item.el;
                    
                    // Check if element is visible
                    const rect = el.getBoundingClientRect();
                    const computed = window.getComputedStyle(el);
                    
                    const issue = {
                        index: idx + 1,
                        type: item.type,
                        visible: rect.width > 0 && rect.height > 0,
                        display: computed.display,
                        visibility: computed.visibility,
                        opacity: computed.opacity,
                        zIndex: computed.zIndex,
                        position: computed.position,
                        inViewport: rect.top < window.innerHeight && rect.bottom > 0,
                        size: Math.round(rect.width) + 'x' + Math.round(rect.height)
                    };
                    
                    // Check if outline would be visible
                    issue.canShowOutline = issue.visible && issue.display !== 'none' && issue.visibility !== 'hidden' && parseFloat(issue.opacity) > 0;
                    
                    if (!issue.canShowOutline) {
                        issue.problem = 'Element hidden or invisible';
                    } else if (!issue.inViewport) {
                        issue.problem = 'Element outside viewport';
                    }
                    
                    issues.push(issue);
                });
                
                return { issues };
            }
        """)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            return
        
        print("Element Highlighting Analysis:")
        print()
        
        cant_highlight = []
        outside_viewport = []
        can_highlight = []
        
        for issue in result['issues']:
            if not issue['canShowOutline']:
                cant_highlight.append(issue)
            elif not issue['inViewport']:
                outside_viewport.append(issue)
            else:
                can_highlight.append(issue)
        
        print(f"✅ Can highlight properly: {len(can_highlight)}")
        print(f"⚠️  Outside viewport: {len(outside_viewport)}")
        print(f"❌ Cannot highlight (hidden): {len(cant_highlight)}")
        print()
        
        if cant_highlight:
            print("=" * 100)
            print("❌ ELEMENTS THAT CAN'T BE HIGHLIGHTED (Hidden/Invisible)")
            print("=" * 100)
            print()
            for issue in cant_highlight:
                print(f"Element #{issue['index']}: {issue['type']}")
                print(f"  Problem: {issue.get('problem', 'Unknown')}")
                print(f"  Size: {issue['size']}")
                print(f"  Display: {issue['display']}, Visibility: {issue['visibility']}, Opacity: {issue['opacity']}")
                print()
        
        if outside_viewport:
            print("=" * 100)
            print("⚠️  ELEMENTS OUTSIDE VIEWPORT (Need to scroll)")
            print("=" * 100)
            print()
            for issue in outside_viewport[:5]:  # Show first 5
                print(f"Element #{issue['index']}: {issue['type']}")
                print(f"  Size: {issue['size']}")
                print(f"  Position: {issue['position']}, Z-index: {issue['zIndex']}")
                print()
        
        print("=" * 100)
        print("🔧 FIXING HIGHLIGHT STYLES")
        print("=" * 100)
        print()
        
        # Inject stronger highlighting
        await page.evaluate("""
            () => {
                // Remove old style
                const oldStyle = document.getElementById('highlight-styles');
                if (oldStyle) oldStyle.remove();
                
                // Inject STRONGER highlighting
                const style = document.createElement('style');
                style.id = 'highlight-styles';
                style.textContent = `
                    .element-highlight {
                        outline: 8px solid red !important;
                        outline-offset: 2px !important;
                        box-shadow: 0 0 30px rgba(255, 0, 0, 0.8) !important;
                        position: relative !important;
                        z-index: 999998 !important;
                        background-color: rgba(255, 0, 0, 0.1) !important;
                    }
                    .element-highlight::before {
                        content: attr(data-element-label);
                        position: absolute;
                        top: -35px;
                        left: 0;
                        background: red;
                        color: white;
                        padding: 8px 15px;
                        border-radius: 5px;
                        font-size: 14px;
                        font-weight: bold;
                        z-index: 999999;
                        white-space: nowrap;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
                    }
                    .element-highlight::after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        border: 3px dashed yellow;
                        pointer-events: none;
                        z-index: 999999;
                    }
                `;
                document.head.appendChild(style);
                
                console.log('✅ Stronger highlight styles injected!');
            }
        """)
        
        print("✅ Injected STRONGER highlighting:")
        print("  - 8px solid RED outline")
        print("  - Red glow shadow")
        print("  - Red background tint")
        print("  - Yellow dashed border")
        print("  - Larger label")
        print()
        print("👉 Navigate through elements again - highlighting should be MUCH more visible!")


if __name__ == "__main__":
    asyncio.run(main())
