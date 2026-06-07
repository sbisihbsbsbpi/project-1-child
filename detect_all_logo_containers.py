#!/usr/bin/env python3
"""
Detect ALL logo containers in template and label them as TOP/BOTTOM based on DOM order
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def detect_logo_containers():
    """Detect all logo containers and show their DOM order"""
    
    async with async_playwright() as p:
        # Connect to existing Chrome instance
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        
        # Get the active page
        contexts = browser.contexts
        if not contexts:
            print("❌ No browser contexts found")
            return
            
        context = contexts[0]
        pages = context.pages
        
        # Create new page if needed
        if not pages:
            page = await context.new_page()
            print("📄 Opening template...")
            await page.goto("https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48")
            await page.wait_for_timeout(5000)
        else:
            page = pages[0]
            current_url = page.url
            if 'templates/edit' not in current_url:
                print("📄 Navigating to template...")
                await page.goto("https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48")
                await page.wait_for_timeout(5000)

        print("🔍 Detecting all logo containers...")
        print("=" * 80)
        
        # Detect all logo containers and highlight them
        result = await page.evaluate("""
            () => {
                const containers = [];
                let containerIndex = 0;

                // Find all logo tables (4 or 5 column tables)
                const allTables = Array.from(document.querySelectorAll('table'));

                allTables.forEach((table, tableIdx) => {
                    const firstRow = table.querySelector('tr');
                    if (!firstRow) return;

                    const cells = Array.from(firstRow.querySelectorAll('td'));

                    // Logo containers have 4 or 5 columns
                    if (cells.length === 4 || cells.length === 5) {
                        // ✨ FILTER OUT: Check if this table contains dynamic tag links (buttons, not logos)
                        const hasDynamicLinks = table.querySelector('.dynamic_tag_link') !== null;
                        const hasViewSurvey = table.textContent.includes('View Survey');
                        const hasGetDirections = table.textContent.includes('Get Directions');
                        const hasCallUs = table.textContent.includes('Call us') || table.textContent.includes('Call Us');

                        if (hasDynamicLinks || hasViewSurvey || hasGetDirections || hasCallUs) {
                            return; // Skip this table - it's a button/link container, not a logo container
                        }

                        const tableRect = table.getBoundingClientRect();
                        const tableTop = Math.round(tableRect.top + window.scrollY);

                        const containerInfo = {
                            type: 'TABLE',
                            domOrder: containerIndex + 1,
                            tableIndex: tableIdx,
                            columnCount: cells.length,
                            visualTop: tableTop,
                            cells: [],
                            relevantCellCount: 0,  // Count cells with image components or empty logo slots
                            tableElement: table
                        };

                        cells.forEach((cell, cellIdx) => {
                            const imageComponent = cell.querySelector('.templates_Image_imageComponent__tqwK7j9G7t');
                            const actualImage = imageComponent ? imageComponent.querySelector('img') : null;
                            const textTemplate = cell.querySelector('.TEXT_TEMPLATE[contenteditable="true"]');

                            const cellRect = cell.getBoundingClientRect();

                            const hasImage = actualImage !== null;
                            const isEmpty = !actualImage && textTemplate !== null;

                            // Count relevant cells (has image or is empty logo slot)
                            if (hasImage || isEmpty) {
                                containerInfo.relevantCellCount++;
                            }

                            containerInfo.cells.push({
                                cellIndex: cellIdx,
                                hasImage: hasImage,
                                isEmpty: isEmpty,
                                textTemplateId: textTemplate ? textTemplate.id : null,
                                imageSrc: actualImage ? actualImage.src : null,
                                imageAlt: actualImage ? actualImage.alt : null,
                                imageSize: actualImage ? {
                                    width: Math.round(cellRect.width),
                                    height: Math.round(cellRect.height)
                                } : null
                            });
                        });

                        // Only add if this table has at least 1 relevant cell (logo or empty slot)
                        if (containerInfo.relevantCellCount > 0) {
                            containers.push(containerInfo);
                            containerIndex++;
                        }
                    }
                });

                // ✨ HIGHLIGHT CONTAINERS
                containers.forEach((container, idx) => {
                    const isTop = idx === 0;
                    const color = isTop ? 'red' : 'lime';
                    const label = isTop ? 'LOGO-1 (TOP)' : 'LOGO-2 (BOTTOM)';
                    const bgColor = isTop ? 'rgba(255, 0, 0, 0.15)' : 'rgba(0, 255, 0, 0.15)';

                    const table = allTables[container.tableIndex];

                    // Highlight the entire table
                    table.style.outline = `8px solid ${color}`;
                    table.style.backgroundColor = bgColor;
                    table.style.boxShadow = `0 0 30px ${color}`;

                    // Add label
                    const tableLabel = document.createElement('div');
                    tableLabel.style.cssText = `
                        position: absolute;
                        top: -40px;
                        left: 0;
                        background: ${color};
                        color: ${isTop ? 'white' : 'black'};
                        padding: 8px 16px;
                        font-size: 16px;
                        font-weight: bold;
                        border: 3px solid black;
                        z-index: 999999;
                        font-family: monospace;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    `;
                    tableLabel.textContent = label;
                    table.style.position = 'relative';
                    table.appendChild(tableLabel);
                });

                return {
                    totalContainers: containers.length,
                    containers: containers
                };
            }
        """)
        
        print(f"✅ Found {result['totalContainers']} logo container(s)\n")
        
        for container in result['containers']:
            dom_label = "TOP (1st in DOM)" if container['domOrder'] == 1 else "BOTTOM (2nd in DOM)"
            
            print(f"📦 Container #{container['domOrder']} - {dom_label}")
            print(f"   Type: {container['type']}")
            print(f"   Table Index: {container['tableIndex']}")
            print(f"   Columns: {container['columnCount']}")
            print(f"   Visual Position: {container['visualTop']}px from top")
            print(f"\n   Cells:")
            
            for cell in container['cells']:
                status = "HAS LOGO" if cell['hasImage'] else ("EMPTY" if cell['isEmpty'] else "OTHER")
                print(f"      Cell {cell['cellIndex']}: {status}")
                
                if cell['hasImage']:
                    print(f"         └─ Image: {cell['imageSrc'][:80]}...")
                    if cell['imageAlt']:
                        print(f"         └─ Alt: \"{cell['imageAlt']}\"")
                    if cell['imageSize']:
                        print(f"         └─ Size: {cell['imageSize']['width']}x{cell['imageSize']['height']}px")
                elif cell['isEmpty']:
                    print(f"         └─ Container ID: {cell['textTemplateId']}")
            
            print("\n" + "-" * 80 + "\n")
        
        # Summary
        print("📊 SUMMARY:")
        print("=" * 80)
        if result['totalContainers'] == 1:
            print("✅ Single logo container detected (only TOP)")
        elif result['totalContainers'] == 2:
            print("✅ Two logo containers detected (TOP + BOTTOM)")
        else:
            print(f"⚠️  Unusual: {result['totalContainers']} logo containers detected")
        
        print("\n💡 RECOMMENDATION:")
        if result['totalContainers'] == 1:
            print("   This template has only ONE logo row")
            print("   All cells belong to the same container (TOP)")
        elif result['totalContainers'] == 2:
            print("   This template has TWO logo rows")
            print("   Container #1 = TOP (first in HTML)")
            print("   Container #2 = BOTTOM (second in HTML)")

if __name__ == "__main__":
    asyncio.run(detect_logo_containers())
