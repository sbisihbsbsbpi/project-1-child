#!/usr/bin/env python3
"""
Deep DOM Analysis - Find template tiles by analyzing actual DOM structure
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("🔍 DEEP DOM ANALYSIS - Finding Template Tiles\n")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            page = await context.new_page()
            
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(4)
            
            print("🔍 Analyzing DOM structure...\n")
            
            # Deep analysis
            analysis = await page.evaluate("""
                () => {
                    const result = {
                        all_elements_with_text: [],
                        template_tiles: [],
                        clickable_cards: [],
                        all_divs_with_content: []
                    };
                    
                    // Function to get element path
                    function getElementPath(element) {
                        const path = [];
                        let current = element;
                        while (current && current !== document.body) {
                            let selector = current.tagName.toLowerCase();
                            if (current.id) {
                                selector += '#' + current.id;
                            } else if (current.className) {
                                const classes = current.className.split(' ').filter(c => c.trim()).slice(0, 2);
                                if (classes.length) selector += '.' + classes.join('.');
                            }
                            path.unshift(selector);
                            current = current.parentElement;
                        }
                        return path.join(' > ');
                    }
                    
                    // 1. Find all elements with specific text patterns
                    const textPatterns = ['Email', 'Text', 'Live Chat', 'Template', 'Draft', 'Archive'];
                    
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.textContent;
                        if (el.children.length === 0 && text && text.trim().length > 0 && text.trim().length < 100) {
                            const trimmedText = text.trim();
                            if (textPatterns.some(pattern => trimmedText.includes(pattern))) {
                                result.all_elements_with_text.push({
                                    text: trimmedText,
                                    tag: el.tagName,
                                    path: getElementPath(el),
                                    parent_class: el.parentElement?.className.substring(0, 60)
                                });
                            }
                        }
                    });
                    
                    // 2. Find clickable card-like structures
                    document.querySelectorAll('div, article, section').forEach(el => {
                        const isClickable = el.onclick || el.style.cursor === 'pointer' || 
                                          el.className.includes('click') || el.className.includes('card') ||
                                          el.getAttribute('role') === 'button';
                        
                        if (isClickable && el.offsetHeight > 80 && el.offsetHeight < 500) {
                            const heading = el.querySelector('h1, h2, h3, h4, h5, h6, [class*="title"], [class*="name"]');
                            result.clickable_cards.push({
                                has_heading: !!heading,
                                heading_text: heading?.textContent.trim(),
                                height: el.offsetHeight,
                                width: el.offsetWidth,
                                classes: el.className.substring(0, 80),
                                children_count: el.children.length,
                                path: getElementPath(el)
                            });
                        }
                    });
                    
                    // 3. Find divs that might contain template info
                    document.querySelectorAll('div').forEach(div => {
                        if (div.offsetHeight > 100 && div.offsetHeight < 400 && div.offsetParent) {
                            const text = div.textContent.trim();
                            const hasMultipleChildren = div.children.length >= 2;
                            const hasImage = div.querySelector('img') !== null;
                            const hasButton = div.querySelector('button') !== null;
                            
                            if (hasMultipleChildren && text.length > 10 && text.length < 500) {
                                result.all_divs_with_content.push({
                                    text_preview: text.substring(0, 100),
                                    has_image: hasImage,
                                    has_button: hasButton,
                                    children_count: div.children.length,
                                    height: div.offsetHeight,
                                    classes: div.className.substring(0, 60),
                                    path: getElementPath(div).substring(0, 150)
                                });
                            }
                        }
                    });
                    
                    // 4. Look for template grid/list container
                    const possibleContainerSelectors = [
                        '[class*="grid"]',
                        '[class*="list"]',
                        '[class*="content"]',
                        '[class*="body"]',
                        '[class*="main"]'
                    ];
                    
                    possibleContainerSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(container => {
                            if (container.offsetHeight > 300 && container.children.length > 0) {
                                // Analyze children
                                Array.from(container.children).forEach((child, idx) => {
                                    if (child.offsetHeight > 50 && idx < 15) {
                                        const childText = child.textContent.trim();
                                        if (childText.length > 10) {
                                            result.template_tiles.push({
                                                index: idx + 1,
                                                text_preview: childText.substring(0, 150),
                                                height: child.offsetHeight,
                                                width: child.offsetWidth,
                                                tag: child.tagName,
                                                classes: child.className.substring(0, 70),
                                                parent_selector: selector,
                                                has_image: child.querySelector('img') !== null,
                                                buttons: Array.from(child.querySelectorAll('button')).map(b => b.textContent.trim()),
                                                path: getElementPath(child).substring(0, 150)
                                            });
                                        }
                                    }
                                });
                            }
                        });
                    });
                    
                    return result;
                }
            """)
            
            # Save and print
            filename = f"dom_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            print("=" * 100)
            print("📊 DEEP DOM ANALYSIS RESULTS")
            print("=" * 100)
            
            print(f"\n📝 Elements with Template-related text: {len(analysis['all_elements_with_text'])}")
            for item in analysis['all_elements_with_text'][:20]:
                print(f"   {item['tag']}: {item['text']}")
            
            print(f"\n🎯 Clickable Card-like Elements: {len(analysis['clickable_cards'])}")
            for card in analysis['clickable_cards'][:10]:
                if card['has_heading']:
                    print(f"   ✓ {card['heading_text']} ({card['height']}px)")
                else:
                    print(f"   - Card {card['height']}x{card['width']}px - {card['children_count']} children")
            
            print(f"\n📦 Potential Template Tiles: {len(analysis['template_tiles'])}")
            for tile in analysis['template_tiles'][:15]:
                print(f"   {tile['index']}. {tile['text_preview']}")
                if tile['buttons']:
                    print(f"      Buttons: {tile['buttons']}")
            
            print(f"\n📋 Divs with Content: {len(analysis['all_divs_with_content'])}")
            for div in analysis['all_divs_with_content'][:10]:
                print(f"   - {div['text_preview']}")
            
            print(f"\n\n✅ Saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
