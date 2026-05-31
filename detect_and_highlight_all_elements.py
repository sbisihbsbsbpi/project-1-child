#!/usr/bin/env python3
"""
Comprehensive Template Editor Detection & Visual Highlighter
Detects ALL elements and highlights them with colored borders and labels
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
    print("🎯 COMPREHENSIVE DETECTION & VISUAL HIGHLIGHTING")
    print("=" * 100)
    
    template_id = "667f0befd4964026ee7b6e48"
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print(f"🌐 Navigating to edit page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)
            
            print("🔍 Detecting and highlighting all elements...\n")
            
            # Inject detection and highlighting script with navigation
            result = await page.evaluate("""
                () => {
                    // Remove any existing highlights
                    document.querySelectorAll('.detection-highlight, .detection-label, .detection-legend, .detection-nav').forEach(el => el.remove());

                    const data = {
                        timestamp: new Date().toISOString(),
                        detected: {
                            contenteditable: [],
                            sortable_items: [],
                            tables: [],
                            delete_icons: [],
                            element_containers: []
                        }
                    };

                    // Store all elements with their metadata
                    window.detectedElements = [];
                    window.currentElementIndex = 0;

                    let counter = 1;

                    // Helper to add highlight
                    function addHighlight(element, label, color, category) {
                        if (!element || !element.offsetParent) return;

                        const rect = element.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return;

                        const elementData = {
                            number: counter,
                            element: element,
                            label: label,
                            color: color,
                            category: category,
                            rect: {
                                top: rect.top + window.scrollY,
                                left: rect.left + window.scrollX,
                                width: rect.width,
                                height: rect.height
                            }
                        };

                        window.detectedElements.push(elementData);

                        // Create highlight border
                        const highlight = document.createElement('div');
                        highlight.className = 'detection-highlight';
                        highlight.dataset.number = counter;
                        highlight.dataset.category = category;
                        highlight.style.cssText = `
                            position: absolute;
                            top: ${elementData.rect.top}px;
                            left: ${elementData.rect.left}px;
                            width: ${elementData.rect.width}px;
                            height: ${elementData.rect.height}px;
                            border: 2px solid ${color};
                            pointer-events: none;
                            z-index: 999998;
                            box-sizing: border-box;
                            opacity: 0.3;
                            transition: all 0.3s ease;
                        `;

                        // Create number badge
                        const badge = document.createElement('div');
                        badge.className = 'detection-label';
                        badge.dataset.number = counter;
                        badge.textContent = counter;
                        badge.style.cssText = `
                            position: absolute;
                            top: ${elementData.rect.top - 10}px;
                            left: ${elementData.rect.left - 10}px;
                            background: ${color};
                            color: white;
                            border-radius: 50%;
                            width: 20px;
                            height: 20px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-weight: bold;
                            font-size: 10px;
                            z-index: 999999;
                            font-family: Arial, sans-serif;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                            opacity: 0.3;
                            transition: all 0.3s ease;
                        `;

                        // Create label
                        const labelDiv = document.createElement('div');
                        labelDiv.className = 'detection-label';
                        labelDiv.dataset.number = counter;
                        labelDiv.textContent = label;
                        labelDiv.style.cssText = `
                            position: absolute;
                            top: ${elementData.rect.top - 25}px;
                            left: ${elementData.rect.left + 15}px;
                            background: rgba(0, 0, 0, 0.8);
                            color: white;
                            padding: 2px 6px;
                            border-radius: 3px;
                            font-size: 10px;
                            z-index: 999999;
                            font-family: Arial, sans-serif;
                            white-space: nowrap;
                            max-width: 250px;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            opacity: 0;
                            transition: all 0.3s ease;
                        `;

                        document.body.appendChild(highlight);
                        document.body.appendChild(badge);
                        document.body.appendChild(labelDiv);

                        return counter++;
                    }
                    
                    // 1. CONTENTEDITABLE ELEMENTS (RED)
                    console.log('Detecting contenteditable elements...');
                    document.querySelectorAll('[contenteditable="true"]').forEach((el, idx) => {
                        const content = el.textContent.trim().substring(0, 40) || '(empty)';
                        const num = addHighlight(el, `📝 Editable: ${content}`, '#FF0000', 'editable');
                        data.detected.contenteditable.push({
                            number: num,
                            id: el.id,
                            content: el.textContent.trim().substring(0, 100)
                        });
                    });
                    
                    // 2. SORTABLE ITEM CONTAINERS (BLUE)
                    console.log('Detecting sortable items...');
                    document.querySelectorAll('[class*="SortableItem_elementContainer"]').forEach((el, idx) => {
                        const num = addHighlight(el, '🔀 Sortable Container', '#0000FF', 'sortable');
                        data.detected.sortable_items.push({
                            number: num,
                            classes: el.className.substring(0, 80)
                        });
                    });
                    
                    // 3. TABLE CELLS WITH CONTENT (GREEN)
                    console.log('Detecting table cells...');
                    let tableCellCount = 0;
                    document.querySelectorAll('td').forEach((cell, idx) => {
                        const editable = cell.querySelector('[contenteditable="true"]');
                        if (editable && tableCellCount < 20) {  // Limit to first 20 for performance
                            const num = addHighlight(cell, '📊 Table Cell (editable)', '#00FF00', 'table');
                            data.detected.tables.push({
                                number: num,
                                has_editable: true
                            });
                            tableCellCount++;
                        }
                    });

                    // 4. DELETE ICONS (ORANGE)
                    console.log('Detecting delete icons...');
                    document.querySelectorAll('.icon-cross').forEach((icon, idx) => {
                        if (idx < 15) {  // Limit to first 15
                            const num = addHighlight(icon.parentElement, '🗙 Delete Icon', '#FF8800', 'delete');
                            data.detected.delete_icons.push({
                                number: num,
                                hidden: icon.className.includes('hidden')
                            });
                        }
                    });

                    // Navigation functions
                    function highlightElement(index) {
                        // Reset all elements to dim
                        document.querySelectorAll('.detection-highlight').forEach(el => {
                            el.style.opacity = '0.3';
                            el.style.borderWidth = '2px';
                        });
                        document.querySelectorAll('.detection-label').forEach(el => {
                            el.style.opacity = '0.3';
                        });

                        if (index < 0 || index >= window.detectedElements.length) return;

                        const current = window.detectedElements[index];
                        window.currentElementIndex = index;

                        // Highlight current element
                        const highlights = document.querySelectorAll(`[data-number="${current.number}"]`);
                        highlights.forEach(el => {
                            if (el.classList.contains('detection-highlight')) {
                                el.style.opacity = '1';
                                el.style.borderWidth = '4px';
                                el.style.boxShadow = '0 0 20px rgba(255, 255, 0, 0.6)';
                            } else {
                                el.style.opacity = '1';
                            }
                        });

                        // Scroll to element
                        current.element.scrollIntoView({ behavior: 'smooth', block: 'center' });

                        // Update counter display
                        document.getElementById('navCounter').textContent = `${index + 1} / ${window.detectedElements.length}`;
                        document.getElementById('currentInfo').innerHTML = `
                            <strong>${current.category.toUpperCase()}</strong><br/>
                            ${current.label.substring(0, 50)}...
                        `;
                    }

                    function nextElement() {
                        let newIndex = window.currentElementIndex + 1;
                        if (newIndex >= window.detectedElements.length) newIndex = 0;
                        highlightElement(newIndex);
                    }

                    function prevElement() {
                        let newIndex = window.currentElementIndex - 1;
                        if (newIndex < 0) newIndex = window.detectedElements.length - 1;
                        highlightElement(newIndex);
                    }

                    // Create navigation panel
                    const nav = document.createElement('div');
                    nav.className = 'detection-nav';
                    nav.style.cssText = `
                        position: fixed;
                        bottom: 20px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: rgba(0, 0, 0, 0.95);
                        color: white;
                        padding: 15px 20px;
                        border-radius: 12px;
                        z-index: 1000000;
                        font-family: Arial, sans-serif;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.7);
                        display: flex;
                        align-items: center;
                        gap: 15px;
                    `;
                    nav.innerHTML = `
                        <button id="prevBtn" style="
                            background: #4CAF50;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 10px 20px;
                            cursor: pointer;
                            font-weight: bold;
                            font-size: 14px;
                            transition: all 0.2s;
                        ">◀ Prev</button>

                        <div style="text-align: center; min-width: 200px;">
                            <div id="navCounter" style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                                1 / ${window.detectedElements.length}
                            </div>
                            <div id="currentInfo" style="font-size: 10px; color: #AAA; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                Starting...
                            </div>
                        </div>

                        <button id="nextBtn" style="
                            background: #2196F3;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 10px 20px;
                            cursor: pointer;
                            font-weight: bold;
                            font-size: 14px;
                            transition: all 0.2s;
                        ">Next ▶</button>
                    `;
                    document.body.appendChild(nav);

                    // Create legend
                    const legend = document.createElement('div');
                    legend.className = 'detection-legend';
                    legend.style.cssText = `
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: rgba(0, 0, 0, 0.95);
                        color: white;
                        padding: 15px;
                        border-radius: 8px;
                        z-index: 1000000;
                        font-family: Arial, sans-serif;
                        font-size: 12px;
                        max-width: 300px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                    `;
                    legend.innerHTML = `
                        <div style="font-weight: bold; margin-bottom: 10px; font-size: 14px; border-bottom: 2px solid #444; padding-bottom: 8px;">
                            🎯 ELEMENT DETECTION
                        </div>
                        <div style="margin: 8px 0;">
                            <span style="display: inline-block; width: 15px; height: 15px; background: #FF0000; margin-right: 8px; border-radius: 2px;"></span>
                            <strong>Red</strong> = Contenteditable (${data.detected.contenteditable.length})
                        </div>
                        <div style="margin: 8px 0;">
                            <span style="display: inline-block; width: 15px; height: 15px; background: #0000FF; margin-right: 8px; border-radius: 2px;"></span>
                            <strong>Blue</strong> = Sortable Items (${data.detected.sortable_items.length})
                        </div>
                        <div style="margin: 8px 0;">
                            <span style="display: inline-block; width: 15px; height: 15px; background: #00FF00; margin-right: 8px; border-radius: 2px;"></span>
                            <strong>Green</strong> = Table Cells (${data.detected.tables.length})
                        </div>
                        <div style="margin: 8px 0;">
                            <span style="display: inline-block; width: 15px; height: 15px; background: #FF8800; margin-right: 8px; border-radius: 2px;"></span>
                            <strong>Orange</strong> = Delete Icons (${data.detected.delete_icons.length})
                        </div>
                        <hr style="border: 1px solid #444; margin: 12px 0;">
                        <div style="font-size: 11px; color: #AAA; text-align: center;">
                            Total Elements: ${window.detectedElements.length}
                        </div>
                        <div style="font-size: 10px; color: #888; text-align: center; margin-top: 8px;">
                            Use ← → arrow keys to navigate
                        </div>
                    `;
                    document.body.appendChild(legend);

                    // Event listeners
                    document.getElementById('prevBtn').addEventListener('click', prevElement);
                    document.getElementById('nextBtn').addEventListener('click', nextElement);

                    // Keyboard navigation
                    document.addEventListener('keydown', (e) => {
                        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                            e.preventDefault();
                            nextElement();
                        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                            e.preventDefault();
                            prevElement();
                        }
                    });

                    // Button hover effects
                    const prevBtn = document.getElementById('prevBtn');
                    const nextBtn = document.getElementById('nextBtn');

                    prevBtn.addEventListener('mouseenter', () => {
                        prevBtn.style.background = '#45a049';
                        prevBtn.style.transform = 'scale(1.05)';
                    });
                    prevBtn.addEventListener('mouseleave', () => {
                        prevBtn.style.background = '#4CAF50';
                        prevBtn.style.transform = 'scale(1)';
                    });

                    nextBtn.addEventListener('mouseenter', () => {
                        nextBtn.style.background = '#1976D2';
                        nextBtn.style.transform = 'scale(1.05)';
                    });
                    nextBtn.addEventListener('mouseleave', () => {
                        nextBtn.style.background = '#2196F3';
                        nextBtn.style.transform = 'scale(1)';
                    });

                    // Initialize by highlighting first element
                    setTimeout(() => {
                        highlightElement(0);
                    }, 500);

                    console.log('Detection complete!', data);
                    console.log(`Total elements: ${window.detectedElements.length}`);
                    console.log('Use Prev/Next buttons or ← → arrow keys to navigate');
                    return data;
                }
            """)

            print(f"✅ Highlighting complete!\n")

            # Save results
            filename = f"detection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)

            print("=" * 100)
            print("📊 DETECTION SUMMARY")
            print("=" * 100)

            print(f"\n🔴 CONTENTEDITABLE ELEMENTS: {len(result['detected']['contenteditable'])}")
            for item in result['detected']['contenteditable'][:10]:
                content = item['content'][:50] if item['content'] else '(empty)'
                print(f"   #{item['number']}: ID={item['id'][:30]} - {content}")

            print(f"\n🔵 SORTABLE ITEMS: {len(result['detected']['sortable_items'])}")
            for item in result['detected']['sortable_items'][:10]:
                print(f"   #{item['number']}: {item['classes'][:60]}")

            print(f"\n🟢 TABLE CELLS: {len(result['detected']['tables'])}")
            print(f"   (Showing first 20 cells with editable content)")

            print(f"\n🟠 DELETE ICONS: {len(result['detected']['delete_icons'])}")
            hidden_count = sum(1 for item in result['detected']['delete_icons'] if item['hidden'])
            print(f"   Hidden: {hidden_count}, Visible: {len(result['detected']['delete_icons']) - hidden_count}")

            print("\n" + "=" * 100)
            print("🎨 VISUAL HIGHLIGHTS ACTIVE")
            print("=" * 100)
            print(f"\n✅ All elements are now highlighted with colored borders!")
            print(f"✅ Legend displayed in top-right corner")
            print(f"✅ Toggle button to show/hide highlights")
            print(f"\n📊 Color Guide:")
            print(f"   🔴 RED    = Contenteditable elements")
            print(f"   🔵 BLUE   = Sortable item containers")
            print(f"   🟢 GREEN  = Table cells (with editable content)")
            print(f"   🟠 ORANGE = Delete icons")

            print(f"\n📁 Results saved to: {filename}")
            print("\n🎮 NAVIGATION CONTROLS:")
            print("    • Click 'Prev' button to go to previous element")
            print("    • Click 'Next' button to go to next element")
            print("    • Use ← → arrow keys for keyboard navigation")
            print("    • Use ↑ ↓ arrow keys for keyboard navigation")
            print("\n⚠️  Keep this script running to maintain highlights")
            print("    Press Ctrl+C to remove highlights and exit")

            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🧹 Cleaning up highlights...")
                await page.evaluate("""
                    () => {
                        document.querySelectorAll('.detection-highlight, .detection-label, .detection-legend, .detection-nav').forEach(el => el.remove());
                        delete window.detectedElements;
                        delete window.currentElementIndex;
                    }
                """)
                print("✅ Highlights removed!")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

