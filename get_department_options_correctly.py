#!/usr/bin/env python3
"""
Get Department Filter Options - Fixed version
Uses existing page to get ALL department options with correct text
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("🎛️ Getting Department Filter Options (Using Existing Tab)\n")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            pages = context.pages
            
            # Find templates page
            page = None
            for p in pages:
                if 'templates/list' in p.url:
                    page = p
                    break
            
            if not page:
                page = pages[0]
            
            print(f"✅ Using existing page: {page.url}\n")
            
            # Click department filter
            print("🖱️ Opening department dropdown...")
            await page.click('.ant-dropdown-trigger')
            await asyncio.sleep(1.5)
            
            # Extract options from the react-select dropdown
            print("📋 Extracting all department options...\n")
            
            options_data = await page.evaluate("""
                () => {
                    const result = {
                        options: [],
                        current_selections: []
                    };
                    
                    // Strategy 1: Look for react-select options
                    const reactSelectOptions = document.querySelectorAll('[class*="option"]');
                    reactSelectOptions.forEach(option => {
                        const text = option.textContent.trim();
                        if (text && text.length > 0 && text.length < 50 && 
                            !text.includes('Search') && !text.includes('results')) {
                            
                            const checkbox = option.querySelector('input[type="checkbox"]');
                            result.options.push({
                                text: text,
                                is_checked: checkbox ? checkbox.checked : false,
                                className: option.className,
                                html: option.outerHTML.substring(0, 200)
                            });
                        }
                    });
                    
                    // Strategy 2: Look in the dropdown overlay
                    const overlay = document.querySelector('[class*="overlay"]');
                    if (overlay) {
                        const labels = overlay.querySelectorAll('label');
                        labels.forEach(label => {
                            // Skip if it's just a checkbox without text
                            const spans = label.querySelectorAll('span:not([class*="checkbox"])');
                            spans.forEach(span => {
                                const text = span.textContent.trim();
                                if (text && text.length > 2 && text.length < 30) {
                                    const checkbox = label.querySelector('input[type="checkbox"]');
                                    const exists = result.options.some(o => o.text === text);
                                    if (!exists) {
                                        result.options.push({
                                            text: text,
                                            is_checked: checkbox ? checkbox.checked : false,
                                            className: label.className,
                                            html: label.outerHTML.substring(0, 250)
                                        });
                                    }
                                }
                            });
                        });
                    }
                    
                    // Strategy 3: Get from the visible dropdown menu items
                    const dropdownItems = document.querySelectorAll('[class*="css-"][class*="option"]');
                    dropdownItems.forEach(item => {
                        // Get text from the item, excluding checkbox
                        const textNodes = [];
                        item.childNodes.forEach(node => {
                            if (node.nodeType === 3) { // Text node
                                const text = node.textContent.trim();
                                if (text) textNodes.push(text);
                            } else if (node.nodeType === 1 && !node.querySelector('.ant-checkbox')) {
                                const text = node.textContent.trim();
                                if (text && text.length < 30) textNodes.push(text);
                            }
                        });
                        
                        const fullText = textNodes.join(' ').trim();
                        if (fullText && fullText.length > 0) {
                            const checkbox = item.querySelector('input[type="checkbox"]');
                            const exists = result.options.some(o => o.text === fullText);
                            if (!exists) {
                                result.options.push({
                                    text: fullText,
                                    is_checked: checkbox ? checkbox.checked : false,
                                    className: item.className.substring(0, 60),
                                    html: item.outerHTML.substring(0, 300)
                                });
                            }
                        }
                    });
                    
                    // Get current selections from trigger
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    if (trigger) {
                        const selections = trigger.innerText.split('\\n').map(s => s.trim()).filter(s => s.length > 0);
                        result.current_selections = [...new Set(selections)];
                    }
                    
                    return result;
                }
            """)
            
            # Save
            filename = f"department_options_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(options_data, f, indent=2)
            
            # Print
            print("=" * 80)
            print("✅ DEPARTMENT FILTER OPTIONS")
            print("=" * 80)
            
            print(f"\n🎯 Current Selections: {', '.join(options_data['current_selections'])}")
            
            print(f"\n📝 Available Options ({len(options_data['options'])}):")
            for i, opt in enumerate(options_data['options'], 1):
                checked = "☑️" if opt['is_checked'] else "☐"
                print(f"   {i}. {checked} {opt['text']}")
            
            print(f"\n💾 Saved to: {filename}")
            
            # Close dropdown
            await page.keyboard.press('Escape')
            print("\n✅ Dropdown closed")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
