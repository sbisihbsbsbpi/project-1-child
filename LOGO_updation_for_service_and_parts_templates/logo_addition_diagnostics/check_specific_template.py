#!/usr/bin/env python3
"""
Check specific template for logo containers
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    template_id = "667f0befd4964026ee7b6ea2"
    template_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    print("=" * 100)
    print(f"🔍 CHECKING TEMPLATE: {template_id}")
    print(f"📄 Service History Recap PDF")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            
            # Find the tab
            pages = context.pages
            page = None
            for p in pages:
                if template_id in p.url:
                    page = p
                    break
            
            if not page:
                page = await context.new_page()
                print(f"🌐 Opening: {template_url}")
                await page.goto(template_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
            else:
                print(f"✅ Using existing tab")
            
            # Run detection
            print("\n🔍 DETECTING LOGO CONTAINERS...\n")
            
            result = await page.evaluate("""
                () => {
                    const containers = [];
                    
                    // Strategy 1: Find logo containers in table structure
                    const logoTableElements = Array.from(document.querySelectorAll('table'));
                    let strategy1Count = 0;

                    logoTableElements.forEach((table, tableIdx) => {
                        const firstRow = table.querySelector('tr');
                        if (!firstRow) return;

                        const cells = Array.from(firstRow.querySelectorAll('td'));

                        if (cells.length === 4) {
                            const positions = ['LEFT', 'CENTER', 'RIGHT'];

                            cells.forEach((cell, cellIdx) => {
                                if (cellIdx >= 3) return;

                                const textTemplate = cell.querySelector('.TEXT_TEMPLATE[contenteditable="true"]');

                                if (textTemplate) {
                                    const hasImage = textTemplate.querySelector('img') !== null;
                                    const htmlLength = textTemplate.innerHTML.trim().length;
                                    const isEmpty = !hasImage && htmlLength < 300;
                                    const rect = textTemplate.getBoundingClientRect();

                                    strategy1Count++;
                                    containers.push({
                                        strategy: 'Strategy 1 (Table)',
                                        tableIndex: tableIdx + 1,
                                        position: positions[cellIdx],
                                        id: textTemplate.id,
                                        isEmpty: isEmpty,
                                        hasImage: hasImage,
                                        htmlLength: htmlLength,
                                        visible: rect.width > 0 && rect.height > 0,
                                        rect: {
                                            width: rect.width,
                                            height: rect.height,
                                            top: rect.top,
                                            left: rect.left
                                        }
                                    });
                                }
                            });
                        }
                    });

                    // Strategy 2: Fallback - Find all hidden TEXT_TEMPLATE elements
                    if (strategy1Count === 0) {
                        const allTextTemplates = Array.from(document.querySelectorAll('.TEXT_TEMPLATE[contenteditable="true"]'));

                        allTextTemplates.forEach((el, idx) => {
                            const rect = el.getBoundingClientRect();
                            const isHidden = rect.width === 0 || rect.height < 20;
                            const hasImage = el.querySelector('img') !== null;
                            const htmlLength = el.innerHTML.trim().length;
                            const isEmpty = !hasImage && htmlLength < 300;

                            if (isHidden && isEmpty) {
                                containers.push({
                                    strategy: 'Strategy 2 (Hidden)',
                                    index: containers.length + 1,
                                    id: el.id,
                                    isEmpty: isEmpty,
                                    hasImage: hasImage,
                                    htmlLength: htmlLength,
                                    visible: false,
                                    rect: {
                                        width: rect.width,
                                        height: rect.height,
                                        top: rect.top,
                                        left: rect.left
                                    }
                                });
                            }
                        });
                    }

                    return {
                        strategy1Count: strategy1Count,
                        totalContainers: containers.length,
                        emptyContainers: containers.filter(c => c.isEmpty).length,
                        containers: containers
                    };
                }
            """)
            
            print(f"📊 RESULTS:")
            print(f"   Strategy 1 (Table): {result['strategy1Count']} containers")
            print(f"   Total detected: {result['totalContainers']}")
            print(f"   Empty containers: {result['emptyContainers']}")
            print()

            if result['totalContainers'] == 0:
                print("❌ NO LOGO CONTAINERS DETECTED!")
                print("   This template might not have logo containers at all.")
            else:
                print("✅ DETECTED CONTAINERS:")
                print()
                for i, container in enumerate(result['containers'], 1):
                    status = "🟢 EMPTY" if container['isEmpty'] else "🔴 HAS CONTENT"
                    visible = "👁️ VISIBLE" if container['visible'] else "❌ HIDDEN"

                    if 'tableIndex' in container:
                        print(f"{i}. [{container['strategy']}] Logo {container['tableIndex']} {container['position']}")
                    else:
                        print(f"{i}. [{container['strategy']}] Container {container['index']}")

                    print(f"   ID: {container['id']}")
                    print(f"   Status: {status}")
                    print(f"   Visibility: {visible}")
                    print(f"   Has Image: {container['hasImage']}")
                    print(f"   HTML Length: {container['htmlLength']}")
                    print(f"   Rect: {container['rect']}")
                    print()
            
            print("=" * 100)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
