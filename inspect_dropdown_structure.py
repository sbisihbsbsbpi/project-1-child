#!/usr/bin/env python3
"""
Inspect Department Dropdown Structure
Analyzes the actual DOM structure when dropdown is open
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page


async def main():
    print("=" * 80)
    print("🔍 INSPECTING DROPDOWN STRUCTURE")
    print("=" * 80)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser via CDP\n")
            
            page = await get_or_navigate_to_page(
                browser,
                "https://preprodapp.tekioncloud.com/templates/list",
                wait_for_load=True
            )
            
            print("\n1️⃣  Clicking department filter...")
            await page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(2)
            print("   ✅ Clicked\n")
            
            print("2️⃣  Analyzing dropdown structure...\n")
            
            # Deep scan for dropdown elements
            dropdown_info = await page.evaluate("""
                () => {
                    const info = {
                        dropdown_containers: [],
                        menu_elements: [],
                        overlay_elements: [],
                        all_visible_elements: []
                    };
                    
                    // Find all elements with 'dropdown' in class name
                    document.querySelectorAll('[class*="dropdown" i]').forEach(el => {
                        if (el.offsetParent !== null) {
                            info.dropdown_containers.push({
                                tag: el.tagName,
                                className: el.className,
                                text: el.textContent.substring(0, 100),
                                children: el.children.length,
                                role: el.getAttribute('role')
                            });
                        }
                    });
                    
                    // Find all elements with 'menu' in class name
                    document.querySelectorAll('[class*="menu" i]').forEach(el => {
                        if (el.offsetParent !== null) {
                            info.menu_elements.push({
                                tag: el.tagName,
                                className: el.className,
                                text: el.textContent.substring(0, 100),
                                children: el.children.length,
                                role: el.getAttribute('role')
                            });
                        }
                    });
                    
                    // Find overlay/portal elements (Ant Design uses portals)
                    document.querySelectorAll('[class*="overlay" i], [class*="portal" i]').forEach(el => {
                        if (el.offsetParent !== null) {
                            info.overlay_elements.push({
                                tag: el.tagName,
                                className: el.className,
                                text: el.textContent.substring(0, 100)
                            });
                        }
                    });
                    
                    // Find elements with 'ant-' prefix that appeared recently
                    document.querySelectorAll('[class*="ant-"]').forEach(el => {
                        const classes = el.className;
                        if (typeof classes === 'string' && 
                            classes.includes('ant-') && 
                            el.offsetParent !== null &&
                            !classes.includes('ant-tabs') &&
                            !classes.includes('ant-select')) {
                            
                            const text = el.textContent.trim();
                            if (text && text.length < 100 && text.length > 0) {
                                info.all_visible_elements.push({
                                    tag: el.tagName,
                                    className: el.className.substring(0, 80),
                                    text: text,
                                    role: el.getAttribute('role')
                                });
                            }
                        }
                    });
                    
                    return info;
                }
            """)
            
            print("📊 RESULTS:")
            print("=" * 80)
            
            print(f"\n🎯 DROPDOWN CONTAINERS ({len(dropdown_info['dropdown_containers'])}):")
            for i, el in enumerate(dropdown_info['dropdown_containers'][:10], 1):
                print(f"\n   {i}. {el['tag']}")
                print(f"      Class: {el['className'][:70]}")
                print(f"      Role: {el['role']}")
                print(f"      Children: {el['children']}")
                print(f"      Text: {el['text'][:60]}")
            
            print(f"\n📋 MENU ELEMENTS ({len(dropdown_info['menu_elements'])}):")
            for i, el in enumerate(dropdown_info['menu_elements'][:10], 1):
                print(f"\n   {i}. {el['tag']}")
                print(f"      Class: {el['className'][:70]}")
                print(f"      Role: {el['role']}")
                print(f"      Children: {el['children']}")
                print(f"      Text: {el['text'][:60]}")
            
            print(f"\n🌐 ALL VISIBLE ANT ELEMENTS ({len(dropdown_info['all_visible_elements'])}):")
            for i, el in enumerate(dropdown_info['all_visible_elements'][:20], 1):
                print(f"\n   {i}. {el['tag']} - {el['text'][:50]}")
                print(f"      Class: {el['className']}")
                print(f"      Role: {el['role']}")
            
            # Try to find department options
            print("\n" + "=" * 80)
            print("🔍 SEARCHING FOR DEPARTMENT OPTIONS...")
            print("=" * 80)
            
            departments = await page.evaluate("""
                () => {
                    const depts = [];
                    const keywords = ['sales', 'service', 'parts', 'all'];
                    
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.textContent.trim().toLowerCase();
                        
                        if (el.children.length === 0 && 
                            el.offsetParent !== null &&
                            keywords.some(kw => text === kw)) {
                            
                            depts.push({
                                tag: el.tagName,
                                text: el.textContent.trim(),
                                className: el.className,
                                clickable: el.onclick !== null || 
                                          el.style.cursor === 'pointer' ||
                                          el.className.includes('clickable') ||
                                          el.className.includes('item')
                            });
                        }
                    });
                    
                    return depts;
                }
            """)
            
            print(f"\nFound {len(departments)} potential department options:")
            for dept in departments:
                print(f"\n   • {dept['text']}")
                print(f"     Tag: {dept['tag']}")
                print(f"     Class: {dept['className'][:60]}")
                print(f"     Clickable: {dept['clickable']}")
            
            print("\n" + "=" * 80)
            print("✅ INSPECTION COMPLETE")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
