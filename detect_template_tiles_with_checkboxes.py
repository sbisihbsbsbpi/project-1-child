#!/usr/bin/env python3
"""
Template Tiles & Checkbox Detector
Detects template tiles/cards with their checkboxes on Tekion templates page
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
    print("🎯 TEMPLATE TILES & CHECKBOXES DETECTION")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print("🌐 Navigating to templates page...")
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(4)
            
            print("🔍 Detecting template tiles and checkboxes...\n")
            
            # Comprehensive detection
            page_data = await page.evaluate("""
                () => {
                    const data = {
                        timestamp: new Date().toISOString(),
                        
                        // Key page elements
                        page_elements: {
                            department_filter: null,
                            tabs: [],
                            action_buttons: [],
                            page_selector: null
                        },
                        
                        // Template tiles/cards
                        template_tiles: [],
                        
                        // Checkboxes found
                        checkboxes: [],
                        
                        // Raw structure for analysis
                        structure_analysis: {
                            all_classes_with_template: [],
                            all_classes_with_media: [],
                            all_classes_with_tile: [],
                            all_classes_with_checkbox: []
                        }
                    };
                    
                    // === PAGE ELEMENTS ===
                    
                    // 1. Department Filter
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        const cleanText = deptFilter.textContent.split('}').pop().trim();
                        data.page_elements.department_filter = {
                            text: cleanText,
                            selector: '.ant-dropdown-trigger'
                        };
                    }
                    
                    // 2. Tabs with counts
                    document.querySelectorAll('[role="tab"]').forEach(tab => {
                        const text = tab.textContent.trim();
                        const match = text.match(/(.+?)\\s*\\((\\d+)\\)/);
                        data.page_elements.tabs.push({
                            label: match ? match[1] : text,
                            count: match ? parseInt(match[2]) : 0,
                            active: tab.getAttribute('aria-selected') === 'true',
                            full_text: text
                        });
                    });
                    
                    // 3. Action buttons
                    document.querySelectorAll('button').forEach(btn => {
                        const text = btn.textContent.trim();
                        if (text.match(/Draft|Archive|Actions|New Template/i)) {
                            data.page_elements.action_buttons.push({
                                text: text,
                                disabled: btn.disabled
                            });
                        }
                    });
                    
                    // 4. Page size selector
                    const pageSelector = document.querySelector('[role="combobox"]');
                    if (pageSelector) {
                        data.page_elements.page_selector = {
                            text: pageSelector.textContent.trim()
                        };
                    }
                    
                    // === TEMPLATE TILES ===
                    
                    // Look for elements with 'template', 'media', 'tile' in class names
                    const allElements = document.querySelectorAll('*');
                    
                    allElements.forEach(el => {
                        const className = el.className;
                        if (typeof className === 'string') {
                            if (className.includes('template') && !data.structure_analysis.all_classes_with_template.includes(className)) {
                                data.structure_analysis.all_classes_with_template.push(className.substring(0, 150));
                            }
                            if (className.includes('media') && !data.structure_analysis.all_classes_with_media.includes(className)) {
                                data.structure_analysis.all_classes_with_media.push(className.substring(0, 150));
                            }
                            if (className.includes('tile') && !data.structure_analysis.all_classes_with_tile.includes(className)) {
                                data.structure_analysis.all_classes_with_tile.push(className.substring(0, 150));
                            }
                            if (className.includes('checkbox') && !data.structure_analysis.all_classes_with_checkbox.includes(className)) {
                                data.structure_analysis.all_classes_with_checkbox.push(className.substring(0, 150));
                            }
                        }
                    });
                    
                    // Find template tiles (cards/items)
                    const tileSelectors = [
                        '[class*="mediaTile"]',
                        '[class*="template"][class*="card"]',
                        '[class*="template"][class*="item"]',
                        '[class*="template"][class*="tile"]'
                    ];
                    
                    tileSelectors.forEach(selector => {
                        const tiles = document.querySelectorAll(selector);
                        tiles.forEach((tile, index) => {
                            if (tile.offsetParent && tile.offsetHeight > 30) {
                                const tileInfo = {
                                    index: index + 1,
                                    selector: selector,
                                    classes: tile.className.substring(0, 200),
                                    
                                    // Try to find checkbox
                                    has_checkbox: false,
                                    checkbox_info: null,
                                    
                                    // Try to find title/name
                                    title: null,
                                    
                                    // Try to find image
                                    has_image: false,
                                    image_src: null,
                                    
                                    // Other elements
                                    buttons: [],
                                    badges: []
                                };
                                
                                // Find checkbox
                                const checkbox = tile.querySelector('input[type="checkbox"]');
                                if (checkbox) {
                                    tileInfo.has_checkbox = true;
                                    const checkboxWrapper = checkbox.closest('.ant-checkbox-wrapper');
                                    tileInfo.checkbox_info = {
                                        checked: checkbox.checked,
                                        wrapper_classes: checkboxWrapper?.className.substring(0, 200) || '',
                                        is_checked_class: checkboxWrapper?.className.includes('checked') || false,
                                        html_snippet: checkboxWrapper?.outerHTML.substring(0, 300) || ''
                                    };
                                }

                                // Find title/heading
                                const heading = tile.querySelector('h1, h2, h3, h4, h5, h6, [class*="title"], [class*="name"]');
                                if (heading) {
                                    tileInfo.title = heading.textContent.trim().substring(0, 100);
                                }

                                // Find image
                                const img = tile.querySelector('img');
                                if (img) {
                                    tileInfo.has_image = true;
                                    tileInfo.image_src = img.src.substring(0, 200);
                                }

                                // Find buttons in tile
                                tile.querySelectorAll('button').forEach(btn => {
                                    const btnText = btn.textContent.trim();
                                    if (btnText && btnText.length < 50) {
                                        tileInfo.buttons.push(btnText);
                                    }
                                });

                                // Find badges/tags
                                const badges = tile.querySelectorAll('[class*="badge"], [class*="tag"], [class*="label"]');
                                badges.forEach(badge => {
                                    const text = badge.textContent.trim();
                                    if (text && text.length < 30) {
                                        tileInfo.badges.push(text);
                                    }
                                });

                                data.template_tiles.push(tileInfo);
                            }
                        });
                    });

                    // === ALL CHECKBOXES ===
                    document.querySelectorAll('input[type="checkbox"]').forEach((checkbox, index) => {
                        if (checkbox.offsetParent) {
                            const wrapper = checkbox.closest('.ant-checkbox-wrapper, label');
                            const containerDiv = checkbox.closest('[class*="checkboxWrapper"]');

                            data.checkboxes.push({
                                index: index + 1,
                                checked: checkbox.checked,
                                wrapper_classes: wrapper?.className.substring(0, 200) || '',
                                container_classes: containerDiv?.className.substring(0, 200) || '',
                                parent_classes: checkbox.parentElement?.className.substring(0, 200) || '',
                                data_test: checkbox.getAttribute('data-test') || '',
                                data_test_id: checkbox.getAttribute('data-test-id') || '',
                                html_snippet: wrapper?.outerHTML.substring(0, 400) || checkbox.outerHTML.substring(0, 400)
                            });
                        }
                    });

                    return data;
                }
            """)

            # Save to JSON
            filename = f"template_tiles_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(page_data, f, indent=2)

            print(f"✅ Saved to: {filename}\n")

            # Print summary
            print("=" * 100)
            print("📊 DETECTION RESULTS")
            print("=" * 100)

            print(f"\n🎛️ PAGE ELEMENTS:")
            if page_data['page_elements']['department_filter']:
                print(f"   Department Filter: {page_data['page_elements']['department_filter']['text']}")

            print(f"\n📑 TABS ({len(page_data['page_elements']['tabs'])}):")
            for tab in page_data['page_elements']['tabs']:
                active = "✓ " if tab['active'] else "  "
                print(f"   {active}{tab['label']} ({tab['count']})")

            print(f"\n🔘 ACTION BUTTONS ({len(page_data['page_elements']['action_buttons'])}):")
            for btn in page_data['page_elements']['action_buttons']:
                print(f"   {btn['text']}")

            if page_data['page_elements']['page_selector']:
                print(f"\n📋 PAGE SELECTOR: {page_data['page_elements']['page_selector']['text']}")

            print(f"\n\n🎯 TEMPLATE TILES DETECTED: {len(page_data['template_tiles'])}")
            for tile in page_data['template_tiles'][:10]:  # Show first 10
                print(f"\n   Tile #{tile['index']}:")
                if tile['title']:
                    print(f"      Title: {tile['title']}")
                print(f"      Has Checkbox: {'✅' if tile['has_checkbox'] else '❌'}")
                if tile['has_checkbox'] and tile['checkbox_info']:
                    print(f"      Checkbox Checked: {'✅' if tile['checkbox_info']['checked'] else '❌'}")
                print(f"      Has Image: {'✅' if tile['has_image'] else '❌'}")
                if tile['buttons']:
                    print(f"      Buttons: {', '.join(tile['buttons'])}")

            print(f"\n\n☑️ ALL CHECKBOXES DETECTED: {len(page_data['checkboxes'])}")
            for cb in page_data['checkboxes'][:5]:  # Show first 5
                print(f"\n   Checkbox #{cb['index']}:")
                print(f"      Checked: {'✅' if cb['checked'] else '❌'}")
                print(f"      Wrapper: {cb['wrapper_classes'][:80]}...")
                if cb['data_test']:
                    print(f"      Data-test: {cb['data_test']}")

            print(f"\n\n🔍 CLASS NAME ANALYSIS:")
            print(f"   Classes with 'template': {len(page_data['structure_analysis']['all_classes_with_template'])}")
            print(f"   Classes with 'media': {len(page_data['structure_analysis']['all_classes_with_media'])}")
            print(f"   Classes with 'tile': {len(page_data['structure_analysis']['all_classes_with_tile'])}")
            print(f"   Classes with 'checkbox': {len(page_data['structure_analysis']['all_classes_with_checkbox'])}")

            if page_data['structure_analysis']['all_classes_with_media']:
                print(f"\n   Sample 'media' classes:")
                for cls in page_data['structure_analysis']['all_classes_with_media'][:5]:
                    print(f"      • {cls}")

            print("\n" + "=" * 100)
            print(f"✅ Full data saved to: {filename}")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

