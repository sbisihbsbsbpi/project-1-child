#!/usr/bin/env python3
"""
Comprehensive Important Elements Detector
Detects ALL important elements on the Tekion templates page
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright


async def main():
    print("=" * 80)
    print("🔍 COMPREHENSIVE IMPORTANT ELEMENTS DETECTION")
    print("=" * 80)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print("🌐 Navigating to templates page...")
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(3)
            
            print("🔍 Detecting ALL elements...")
            
            # Detect all elements comprehensively
            elements_data = await page.evaluate("""
                () => {
                    const elements = {
                        filters: {},
                        tabs: [],
                        buttons: [],
                        dropdowns: [],
                        counts: [],
                        headings: [],
                        inputs: [],
                        table_headers: [],
                        table_rows: [],
                        pagination: {},
                        menu_items: [],
                        status_indicators: [],
                        all_text_content: []
                    };
                    
                    // 1. DEPARTMENT FILTER (Ant Design)
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        elements.filters.department = {
                            type: 'dropdown',
                            text: deptFilter.textContent.trim(),
                            className: deptFilter.className,
                            selector: '.ant-dropdown-trigger',
                            visible: true
                        };
                    }
                    
                    // 2. ALL BUTTONS
                    document.querySelectorAll('button').forEach((btn, i) => {
                        if (btn.offsetParent !== null) {
                            const text = btn.textContent.trim();
                            if (text) {
                                elements.buttons.push({
                                    index: i + 1,
                                    text: text,
                                    type: btn.type,
                                    className: btn.className,
                                    ariaLabel: btn.getAttribute('aria-label'),
                                    disabled: btn.disabled
                                });
                            }
                        }
                    });
                    
                    // 3. TABS (with counts)
                    document.querySelectorAll('[role="tab"]').forEach((tab, i) => {
                        const text = tab.textContent.trim();
                        const match = text.match(/(.+?)\\s*\\((\\d+)\\)/);
                        
                        elements.tabs.push({
                            index: i + 1,
                            fullText: text,
                            label: match ? match[1] : text,
                            count: match ? parseInt(match[2]) : null,
                            ariaSelected: tab.getAttribute('aria-selected') === 'true',
                            className: tab.className
                        });
                    });
                    
                    // 4. DROPDOWNS/COMBOBOXES
                    document.querySelectorAll('[role="combobox"]').forEach((cb, i) => {
                        elements.dropdowns.push({
                            index: i + 1,
                            text: cb.textContent.trim(),
                            ariaExpanded: cb.getAttribute('aria-expanded'),
                            className: cb.className
                        });
                    });
                    
                    // 5. ALL HEADINGS (h1, h2, h3, h4, h5, h6)
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(tag => {
                        document.querySelectorAll(tag).forEach((heading, i) => {
                            const text = heading.textContent.trim();
                            if (text && heading.offsetParent !== null) {
                                elements.headings.push({
                                    tag: tag,
                                    text: text,
                                    className: heading.className
                                });
                            }
                        });
                    });
                    
                    // 6. TEXT WITH NUMBERS IN PARENTHESES (counts)
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.textContent.trim();
                        const match = text.match(/^(.+?)\\s*\\((\\d+)\\)$/);
                        if (match && el.children.length === 0 && el.offsetParent !== null) {
                            elements.counts.push({
                                label: match[1],
                                count: parseInt(match[2]),
                                text: text,
                                tagName: el.tagName,
                                className: el.className
                            });
                        }
                    });
                    
                    // 7. ALL INPUT FIELDS
                    document.querySelectorAll('input').forEach((input, i) => {
                        if (input.offsetParent !== null) {
                            elements.inputs.push({
                                index: i + 1,
                                type: input.type,
                                placeholder: input.placeholder,
                                value: input.value,
                                name: input.name,
                                className: input.className
                            });
                        }
                    });
                    
                    // 8. TABLE HEADERS
                    document.querySelectorAll('th').forEach((th, i) => {
                        const text = th.textContent.trim();
                        if (text) {
                            elements.table_headers.push({
                                index: i + 1,
                                text: text,
                                className: th.className
                            });
                        }
                    });
                    
                    // 9. PAGINATION INFO
                    const paginationText = document.querySelector('[class*="pagination"]')?.textContent;
                    if (paginationText) {
                        elements.pagination.text = paginationText;
                    }
                    
                    // 10. ALL VISIBLE TEXT (for analysis)
                    const allText = document.body.textContent.split('\\n')
                        .map(line => line.trim())
                        .filter(line => line.length > 0 && line.length < 100);
                    
                    elements.all_text_content = [...new Set(allText)].slice(0, 200);
                    
                    return elements;
                }
            """)
            
            # Save to JSON
            output = {
                "timestamp": datetime.now().isoformat(),
                "url": "https://preprodapp.tekioncloud.com/templates/list",
                "elements": elements_data
            }
            
            filename = f"important_elements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            
            print(f"\n✅ Saved to: {filename}")
            
            # Print summary
            print("\n" + "=" * 80)
            print("📊 DETECTION SUMMARY")
            print("=" * 80)
            
            print(f"\n🎛️ FILTERS:")
            if elements_data['filters'].get('department'):
                print(f"   Department Filter: {elements_data['filters']['department']['text']}")
            
            print(f"\n📑 TABS ({len(elements_data['tabs'])}):")
            for tab in elements_data['tabs']:
                count_str = f" ({tab['count']})" if tab['count'] is not None else ""
                active = "✓ " if tab['ariaSelected'] else "  "
                print(f"   {active}Tab {tab['index']}: {tab['label']}{count_str}")
            
            print(f"\n🔘 IMPORTANT BUTTONS:")
            important_keywords = ['Draft', 'Archive', 'Template', 'Action', 'New', 'Edit', 'Delete']
            for btn in elements_data['buttons']:
                if any(keyword.lower() in btn['text'].lower() for keyword in important_keywords):
                    print(f"   Button {btn['index']}: {btn['text']}")
            
            print(f"\n📋 DROPDOWNS ({len(elements_data['dropdowns'])}):")
            for dd in elements_data['dropdowns']:
                print(f"   Dropdown {dd['index']}: {dd['text']}")

            print(f"\n📊 COUNTS DETECTED ({len(elements_data['counts'])}):")
            for count in elements_data['counts'][:10]:
                print(f"   {count['label']}: {count['count']}")

            print(f"\n📰 HEADINGS ({len(elements_data['headings'])}):")
            for heading in elements_data['headings'][:15]:
                print(f"   {heading['tag'].upper()}: {heading['text']}")

            print(f"\n🔍 INPUT FIELDS ({len(elements_data['inputs'])}):")
            for inp in elements_data['inputs'][:10]:
                if inp['placeholder']:
                    print(f"   {inp['type']}: {inp['placeholder']}")

            print(f"\n📋 TABLE HEADERS ({len(elements_data['table_headers'])}):")
            for th in elements_data['table_headers']:
                print(f"   {th['text']}")

            print("\n" + "=" * 80)
            print(f"✅ Complete data saved to: {filename}")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

