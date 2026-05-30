#!/usr/bin/env python3
"""
DEMO: Element Storage and Adaptive Detection
Shows how elements are stored, accessed, and adapted when page changes
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from element_storage_manager import ElementStorageManager


async def main():
    print("=" * 100)
    print("🎯 ELEMENT STORAGE & ADAPTATION DEMO")
    print("=" * 100)
    print()
    
    # Initialize storage manager
    storage = ElementStorageManager(storage_dir="element_storage")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print("🌐 Navigating to templates page...")
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(3)
            
            print("\n" + "=" * 100)
            print("STEP 1: DETECT & STORE ELEMENTS")
            print("=" * 100)
            
            # Detect elements
            elements = await page.evaluate("""
                () => {
                    return {
                        department_filter: {
                            text: document.querySelector('.ant-dropdown-trigger')?.textContent.trim(),
                            className: document.querySelector('.ant-dropdown-trigger')?.className,
                            index: 1
                        },
                        tabs: Array.from(document.querySelectorAll('[role="tab"]')).map((tab, i) => ({
                            index: i + 1,
                            text: tab.textContent.trim(),
                            className: tab.className,
                            ariaSelected: tab.getAttribute('aria-selected')
                        })),
                        buttons: Array.from(document.querySelectorAll('button')).map((btn, i) => ({
                            index: i + 1,
                            text: btn.textContent.trim(),
                            className: btn.className,
                            disabled: btn.disabled
                        })).filter(b => b.text)
                    };
                }
            """)
            
            print(f"\n📊 Detected {len(elements['tabs'])} tabs, {len(elements['buttons'])} buttons")
            
            # Store elements
            page_url = "https://preprodapp.tekioncloud.com/templates/list"
            version_id = storage.save_elements(page_url, elements)
            
            print(f"💾 Saved with version ID: {version_id}")
            
            
            print("\n" + "=" * 100)
            print("STEP 2: ACCESS STORED ELEMENTS")
            print("=" * 100)
            
            # Get all elements
            stored_data = storage.get_all_elements(page_url)
            print(f"\n✅ Retrieved {storage._count_elements(stored_data['elements'])} element categories")
            
            # Search for specific elements
            search_results = storage.search_elements(page_url, "draft")
            print(f"🔍 Search for 'draft': Found {len(search_results)} results")
            for result in search_results[:3]:
                print(f"   - {result['category']}: {result['element'].get('text', 'N/A')[:50]}")
            
            
            print("\n" + "=" * 100)
            print("STEP 3: ADAPTIVE ELEMENT FINDING")
            print("=" * 100)
            
            # Try to find "New Template" button using adaptive strategies
            new_template_btn = next((b for b in elements['buttons'] if 'Template' in b['text']), None)
            
            if new_template_btn:
                print(f"\n🎯 Looking for button: '{new_template_btn['text']}'")
                print("   Trying multiple strategies...")
                
                found_element = await storage.find_element_adaptive(page, new_template_btn)
                
                if found_element:
                    print(f"   ✅ FOUND! Element is accessible")
                    
                    # Get element details
                    details = await found_element.evaluate("""
                        el => ({
                            text: el.textContent.trim(),
                            visible: el.offsetParent !== null,
                            position: el.getBoundingClientRect()
                        })
                    """)
                    print(f"   📍 Text: {details['text']}")
                    print(f"   👁️  Visible: {details['visible']}")
                else:
                    print("   ❌ Not found with any strategy")
            
            
            print("\n" + "=" * 100)
            print("STEP 4: DETECT CHANGES")
            print("=" * 100)
            
            # Simulate detecting the page again
            print("\n🔄 Re-detecting elements...")
            new_elements = await page.evaluate("""
                () => {
                    return {
                        department_filter: {
                            text: document.querySelector('.ant-dropdown-trigger')?.textContent.trim(),
                            className: document.querySelector('.ant-dropdown-trigger')?.className,
                            index: 1
                        },
                        tabs: Array.from(document.querySelectorAll('[role="tab"]')).map((tab, i) => ({
                            index: i + 1,
                            text: tab.textContent.trim(),
                            className: tab.className
                        })),
                        buttons: Array.from(document.querySelectorAll('button')).map((btn, i) => ({
                            index: i + 1,
                            text: btn.textContent.trim(),
                            className: btn.className
                        })).filter(b => b.text)
                    };
                }
            """)
            
            # Detect changes
            change_report = storage.detect_changes(page_url, new_elements)
            
            print(f"\n📊 Change Detection Result: {change_report['status'].upper()}")
            print(f"   Old Version: {change_report.get('old_version', 'N/A')}")
            print(f"   Changes Found: {len(change_report['changes'])}")
            
            if change_report['changes']:
                for change in change_report['changes'][:5]:
                    print(f"   - {change['type']}: {change.get('category', 'N/A')}")
            else:
                print("   ✅ No changes detected - page is stable!")
            
            
            print("\n" + "=" * 100)
            print("STEP 5: STORAGE STATISTICS")
            print("=" * 100)
            
            stats = storage.get_statistics()
            print(f"\n📈 Storage Statistics:")
            print(f"   Total Versions: {stats['total_versions']}")
            print(f"   Cached Pages: {stats['cached_pages']}")
            print(f"   Successful Strategies: {stats['successful_strategies']}")
            print(f"   Storage Location: {stats['storage_location']}")
            print(f"\n   Files Created:")
            for filename, exists in stats['files'].items():
                status = "✅" if exists else "❌"
                print(f"      {status} {filename}.json")
            
            
            print("\n" + "=" * 100)
            print("✅ DEMO COMPLETE!")
            print("=" * 100)
            print("\n💡 KEY TAKEAWAYS:")
            print("   1. Elements stored with multiple identifiers (CSS, XPath, text)")
            print("   2. Fast access via in-memory cache + JSON files")
            print("   3. Adaptive finding with 5+ fallback strategies")
            print("   4. Automatic change detection")
            print("   5. Storage persists across runs")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
