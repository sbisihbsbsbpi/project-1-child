#!/usr/bin/env python3
"""
Department Filter Dropdown Options Detector
Uses existing CDP connection to detect all dropdown options
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🎛️ DEPARTMENT FILTER DROPDOWN OPTIONS DETECTION")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser via CDP")
            
            # Use existing context and page
            context = browser.contexts[0]
            pages = context.pages
            
            # Find the templates page
            page = None
            for p in pages:
                url = p.url
                if 'templates/list' in url:
                    page = p
                    print(f"✅ Found templates page: {url}")
                    break
            
            if not page:
                print("⚠️  Templates page not found, using first page...")
                page = pages[0] if pages else await context.new_page()
                await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                              wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
            
            print("\n🔍 Detecting department filter dropdown...\n")
            
            # Click the department filter to open dropdown
            print("🖱️ Clicking department filter...")
            await page.click('.ant-dropdown-trigger')
            await asyncio.sleep(1)
            
            # Detect all dropdown options
            print("📋 Extracting dropdown menu options...\n")
            
            dropdown_data = await page.evaluate("""
                () => {
                    const data = {
                        timestamp: new Date().toISOString(),
                        department_filter: {
                            current_selection: null,
                            trigger_element: null,
                            dropdown_menu: null,
                            options: []
                        }
                    };
                    
                    // Get trigger element
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    if (trigger) {
                        data.department_filter.trigger_element = {
                            html: trigger.outerHTML.substring(0, 500),
                            text: trigger.innerText,
                            selector: '.ant-dropdown-trigger'
                        };
                        data.department_filter.current_selection = trigger.innerText.trim();
                    }
                    
                    // Get dropdown menu (it appears as a separate element)
                    const dropdownMenu = document.querySelector('.ant-dropdown');
                    if (dropdownMenu) {
                        data.department_filter.dropdown_menu = {
                            visible: dropdownMenu.offsetParent !== null,
                            html: dropdownMenu.outerHTML.substring(0, 1000),
                            className: dropdownMenu.className
                        };
                        
                        // Get all menu items
                        const menuItems = dropdownMenu.querySelectorAll('.ant-dropdown-menu-item');
                        menuItems.forEach((item, index) => {
                            const checkbox = item.querySelector('input[type="checkbox"]');
                            const label = item.querySelector('label');
                            const text = item.textContent.trim();
                            
                            data.department_filter.options.push({
                                index: index + 1,
                                text: text,
                                value: label?.getAttribute('for') || text,
                                is_checked: checkbox ? checkbox.checked : false,
                                selector: `.ant-dropdown-menu-item:nth-child(${index + 1})`,
                                html: item.outerHTML.substring(0, 300)
                            });
                        });
                    }
                    
                    // Also check for ant-select-dropdown
                    const selectDropdown = document.querySelector('.ant-select-dropdown');
                    if (selectDropdown && !dropdownMenu) {
                        data.department_filter.dropdown_menu = {
                            visible: true,
                            type: 'ant-select-dropdown',
                            className: selectDropdown.className
                        };
                        
                        // Get options from select dropdown
                        const options = selectDropdown.querySelectorAll('.ant-select-dropdown-menu-item');
                        options.forEach((option, index) => {
                            data.department_filter.options.push({
                                index: index + 1,
                                text: option.textContent.trim(),
                                selector: `.ant-select-dropdown-menu-item:nth-child(${index + 1})`,
                                html: option.outerHTML.substring(0, 200)
                            });
                        });
                    }
                    
                    // Check for checkbox menu
                    const checkboxMenu = document.querySelectorAll('.ant-checkbox-wrapper');
                    if (checkboxMenu.length > 0 && data.department_filter.options.length === 0) {
                        checkboxMenu.forEach((checkbox, index) => {
                            const label = checkbox.querySelector('span:not(.ant-checkbox)');
                            const input = checkbox.querySelector('input[type="checkbox"]');
                            
                            if (label) {
                                data.department_filter.options.push({
                                    index: index + 1,
                                    text: label.textContent.trim(),
                                    is_checked: input ? input.checked : false,
                                    selector: `.ant-checkbox-wrapper:nth-child(${index + 1})`,
                                    html: checkbox.outerHTML.substring(0, 200)
                                });
                            }
                        });
                    }
                    
                    return data;
                }
            """)
            
            # Save JSON
            filename = f"department_dropdown_options_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(dropdown_data, f, indent=2)
            
            # Print results
            print("=" * 100)
            print("✅ DEPARTMENT FILTER DROPDOWN DETECTION COMPLETE")
            print("=" * 100)
            
            dept = dropdown_data['department_filter']
            
            print(f"\n🎯 Current Selection: {dept['current_selection']}")
            
            if dept['dropdown_menu']:
                print(f"\n📋 Dropdown Menu: {'Visible' if dept['dropdown_menu']['visible'] else 'Hidden'}")
                print(f"   Type: {dept['dropdown_menu'].get('type', 'ant-dropdown')}")
            
            print(f"\n📝 Dropdown Options ({len(dept['options'])}):")
            for option in dept['options']:
                checked = "☑️" if option.get('is_checked', False) else "☐"
                print(f"   {option['index']}. {checked} {option['text']}")
                print(f"      Selector: {option['selector']}")
            
            print(f"\n💾 Saved to: {filename}")
            
            # Close the dropdown
            print("\n🖱️ Closing dropdown...")
            await page.keyboard.press('Escape')
            
            print("\n✅ Done! Check the JSON file for complete details.")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
