#!/usr/bin/env python3
"""
Screenshot Department Dropdown and Get ALL DOM Content
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("📸 Taking screenshot and getting dropdown content\n")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            pages = context.pages
            
            page = None
            for p in pages:
                if 'templates/list' in p.url:
                    page = p
                    break
            
            if not page:
                page = pages[0]
            
            print(f"✅ Using page: {page.url}\n")
            
            # Click department filter
            print("🖱️ Clicking department dropdown...")
            await page.click('.ant-dropdown-trigger')
            await asyncio.sleep(2)
            
            # Take screenshot
            screenshot_file = f"department_dropdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_file, full_page=False)
            print(f"📸 Screenshot saved: {screenshot_file}\n")
            
            # Get ALL text from page
            print("🔍 Getting all visible text content...\n")
            
            all_content = await page.evaluate("""
                () => {
                    const content = {
                        all_visible_text: [],
                        dropdown_content: null,
                        checkbox_labels: [],
                        select_options: []
                    };
                    
                    // Get all visible elements with text
                    document.querySelectorAll('*').forEach(el => {
                        if (el.offsetParent !== null && el.children.length === 0) {
                            const text = el.textContent.trim();
                            if (text && text.length > 0 && text.length < 100) {
                                content.all_visible_text.push({
                                    text: text,
                                    tag: el.tagName,
                                    className: el.className.substring(0, 50)
                                });
                            }
                        }
                    });
                    
                    // Get dropdown overlay content
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    if (dropdown) {
                        content.dropdown_content = {
                            html: dropdown.outerHTML,
                            text: dropdown.textContent,
                            className: dropdown.className
                        };
                    }
                    
                    // Get all labels with checkboxes
                    document.querySelectorAll('label').forEach(label => {
                        const checkbox = label.querySelector('input[type="checkbox"]');
                        if (checkbox && label.offsetParent !== null) {
                            content.checkbox_labels.push({
                                text: label.textContent.trim(),
                                checked: checkbox.checked,
                                html: label.outerHTML.substring(0, 400)
                            });
                        }
                    });
                    
                    // Get react-select specific elements
                    const reactSelect = document.querySelector('[class*="css-"][class*="container"]');
                    if (reactSelect) {
                        const options = reactSelect.querySelectorAll('[class*="option"]');
                        options.forEach(opt => {
                            content.select_options.push({
                                text: opt.textContent.trim(),
                                html: opt.outerHTML.substring(0, 300)
                            });
                        });
                    }
                    
                    return content;
                }
            """)
            
            # Save JSON
            filename = f"dropdown_full_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(all_content, f, indent=2)
            
            print("=" * 80)
            print("📋 DROPDOWN CONTENT ANALYSIS")
            print("=" * 80)
            
            print(f"\n📝 All Visible Text Elements: {len(all_content['all_visible_text'])}")
            
            # Filter for likely department names
            likely_departments = []
            for item in all_content['all_visible_text']:
                text = item['text']
                if any(word in text for word in ['Sales', 'Service', 'Parts', 'Department', 'Business']):
                    if text not in likely_departments and len(text) < 50:
                        likely_departments.append(text)
                        print(f"   - {text}")
            
            print(f"\n☑️ Checkbox Labels: {len(all_content['checkbox_labels'])}")
            for label in all_content['checkbox_labels'][:10]:
                checked = "☑️" if label['checked'] else "☐"
                print(f"   {checked} {label['text'][:60]}")
            
            print(f"\n📋 Select Options: {len(all_content['select_options'])}")
            for opt in all_content['select_options'][:10]:
                print(f"   - {opt['text'][:60]}")
            
            print(f"\n💾 Saved to: {filename}")
            print(f"📸 Screenshot: {screenshot_file}")
            
            # Close dropdown
            await page.keyboard.press('Escape')
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
