#!/usr/bin/env python3
"""
Visual Element Highlighter
Highlights ALL detected elements on the page with red borders and numbers
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page, print_cdp_info


async def main():
    print("=" * 80)
    print("🎯 VISUAL ELEMENT HIGHLIGHTER")
    print("=" * 80)
    print()
    
    # Connect to existing browser via CDP
    print("🌐 Connecting to browser via CDP (localhost:9223)...")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser via CDP")
            print_cdp_info(browser)
            print()

            # Use existing tab instead of creating new one
            page = await get_or_navigate_to_page(
                browser,
                "https://preprodapp.tekioncloud.com/templates/list",
                wait_for_load=True
            )
            
            print("🎨 Injecting highlighter script...")
            
            # Inject the highlighter
            await page.evaluate("""
                () => {
                    // Remove any existing highlights
                    document.querySelectorAll('.detection-highlight, .detection-badge, .detection-tooltip, .detection-legend, .detection-nav').forEach(el => el.remove());

                    let counter = 1;
                    const highlights = [];
                    let currentIndex = -1; // No element focused initially

                    // Helper to add highlight
                    function addHighlight(element, label, color = '#FF0000') {
                        if (!element || !element.offsetParent) return; // Skip invisible

                        const rect = element.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return;

                        const itemNumber = counter++;

                        // Create highlight overlay
                        const highlight = document.createElement('div');
                        highlight.className = 'detection-highlight';
                        highlight.dataset.index = itemNumber - 1;
                        highlight.style.cssText = `
                            position: fixed;
                            top: ${rect.top + window.scrollY}px;
                            left: ${rect.left + window.scrollX}px;
                            width: ${rect.width}px;
                            height: ${rect.height}px;
                            border: 3px solid ${color};
                            pointer-events: none;
                            z-index: 999999;
                            box-sizing: border-box;
                            transition: all 0.3s ease;
                        `;

                        // Create number badge
                        const badge = document.createElement('div');
                        badge.className = 'detection-badge';
                        badge.dataset.index = itemNumber - 1;
                        badge.textContent = itemNumber;
                        badge.style.cssText = `
                            position: fixed;
                            top: ${rect.top + window.scrollY - 12}px;
                            left: ${rect.left + window.scrollX - 12}px;
                            background: ${color};
                            color: white;
                            border-radius: 50%;
                            width: 24px;
                            height: 24px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-weight: bold;
                            font-size: 12px;
                            z-index: 1000000;
                            font-family: Arial, sans-serif;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                            transition: all 0.3s ease;
                        `;

                        // Create label tooltip
                        const tooltip = document.createElement('div');
                        tooltip.className = 'detection-tooltip';
                        tooltip.dataset.index = itemNumber - 1;
                        tooltip.textContent = label;
                        tooltip.style.cssText = `
                            position: fixed;
                            top: ${rect.top + window.scrollY - 35}px;
                            left: ${rect.left + window.scrollX + 20}px;
                            background: rgba(0, 0, 0, 0.8);
                            color: white;
                            padding: 4px 8px;
                            border-radius: 4px;
                            font-size: 11px;
                            z-index: 1000001;
                            font-family: Arial, sans-serif;
                            white-space: nowrap;
                            max-width: 300px;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            transition: all 0.3s ease;
                        `;

                        document.body.appendChild(highlight);
                        document.body.appendChild(badge);
                        document.body.appendChild(tooltip);

                        highlights.push({ element, highlight, badge, tooltip, label, index: itemNumber - 1 });
                    }

                    // Navigation functions
                    function navigateToElement(index) {
                        if (index < 0 || index >= highlights.length) return;

                        // Reset all highlights
                        highlights.forEach((item, i) => {
                            if (i === index) {
                                // Highlight current element
                                item.highlight.style.border = '5px solid #00FF00';
                                item.highlight.style.boxShadow = '0 0 20px rgba(0, 255, 0, 0.6)';
                                item.badge.style.background = '#00FF00';
                                item.badge.style.transform = 'scale(1.5)';
                                item.badge.style.boxShadow = '0 4px 8px rgba(0, 255, 0, 0.6)';
                                item.tooltip.style.background = 'rgba(0, 255, 0, 0.9)';
                                item.tooltip.style.color = 'black';
                                item.tooltip.style.fontWeight = 'bold';

                                // Scroll to element
                                item.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            } else {
                                // Normal state
                                item.highlight.style.border = '3px solid #FF0000';
                                item.highlight.style.boxShadow = 'none';
                                item.badge.style.background = '#FF0000';
                                item.badge.style.transform = 'scale(1)';
                                item.badge.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
                                item.tooltip.style.background = 'rgba(0, 0, 0, 0.8)';
                                item.tooltip.style.color = 'white';
                                item.tooltip.style.fontWeight = 'normal';
                            }
                        });

                        currentIndex = index;

                        // Update navigation display
                        document.getElementById('currentElementNumber').textContent = `${index + 1} / ${highlights.length}`;
                        document.getElementById('currentElementLabel').textContent = highlights[index].label;
                    }

                    function nextElement() {
                        const newIndex = (currentIndex + 1) % highlights.length;
                        navigateToElement(newIndex);
                    }

                    function prevElement() {
                        const newIndex = currentIndex <= 0 ? highlights.length - 1 : currentIndex - 1;
                        navigateToElement(newIndex);
                    }
                    
                    // 1. DEPARTMENT FILTER
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        addHighlight(deptFilter, '🎛️ Department Filter', '#FF0000');
                    }
                    
                    // 2. SEARCH BOXES
                    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search" i], input[placeholder*="Search"]');
                    searchInputs.forEach((input, i) => {
                        addHighlight(input, `🔍 Search Box ${i+1}: ${input.placeholder}`, '#FF1744');
                    });
                    
                    // 3. BUTTONS
                    const buttons = document.querySelectorAll('button');
                    buttons.forEach((btn, i) => {
                        const text = btn.textContent.trim().substring(0, 30);
                        if (text) {
                            addHighlight(btn, `🔘 Button: ${text}`, '#D32F2F');
                        }
                    });
                    
                    // 4. CHECKBOXES
                    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                    checkboxes.forEach((cb, i) => {
                        const label = cb.nextElementSibling?.textContent?.substring(0, 30) || 
                                     cb.parentElement?.textContent?.substring(0, 30) || 'Checkbox';
                        addHighlight(cb.parentElement || cb, `☑️ Checkbox: ${label}`, '#E53935');
                    });
                    
                    // 5. DROPDOWNS/COMBOBOXES
                    const comboboxes = document.querySelectorAll('[role="combobox"]');
                    comboboxes.forEach((cb, i) => {
                        const text = cb.textContent.trim().substring(0, 30);
                        addHighlight(cb, `📋 Dropdown: ${text}`, '#C62828');
                    });
                    
                    // 6. LINKS
                    const links = document.querySelectorAll('a[href]');
                    links.forEach((link, i) => {
                        const text = link.textContent.trim().substring(0, 30);
                        if (text && link.offsetParent) {
                            addHighlight(link, `🔗 Link: ${text}`, '#B71C1C');
                        }
                    });
                    
                    // 7. INPUT FIELDS
                    const inputs = document.querySelectorAll('input:not([type="checkbox"]):not([type="search"])');
                    inputs.forEach((input, i) => {
                        const placeholder = input.placeholder || input.name || `Input ${i+1}`;
                        addHighlight(input, `📝 Input: ${placeholder}`, '#FF5252');
                    });
                    
                    // 8. TABS
                    const tabs = document.querySelectorAll('[role="tab"]');
                    tabs.forEach((tab, i) => {
                        const text = tab.textContent.trim().substring(0, 30);
                        addHighlight(tab, `📑 Tab: ${text}`, '#FF6E40');
                    });
                    
                    // 9. PAGINATION
                    const pagination = document.querySelectorAll('[class*="pag"]');
                    pagination.forEach((pag, i) => {
                        if (pag.offsetParent && pag.offsetHeight > 0) {
                            addHighlight(pag, `📄 Pagination`, '#FF3D00');
                        }
                    });
                    
                    // 10. IMAGES
                    const images = document.querySelectorAll('img');
                    images.forEach((img, i) => {
                        if (img.offsetParent) {
                            const alt = img.alt || `Image ${i+1}`;
                            addHighlight(img, `🖼️ Image: ${alt}`, '#DD2C00');
                        }
                    });
                    
                    // Create navigation panel
                    const navPanel = document.createElement('div');
                    navPanel.className = 'detection-nav';
                    navPanel.style.cssText = `
                        position: fixed;
                        bottom: 20px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: rgba(0, 0, 0, 0.95);
                        color: white;
                        padding: 15px 25px;
                        border-radius: 50px;
                        z-index: 1000003;
                        font-family: Arial, sans-serif;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.7);
                        display: flex;
                        align-items: center;
                        gap: 15px;
                    `;
                    navPanel.innerHTML = `
                        <button id="prevBtn" style="
                            background: #FF0000;
                            color: white;
                            border: none;
                            border-radius: 50%;
                            width: 40px;
                            height: 40px;
                            cursor: pointer;
                            font-size: 18px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            transition: all 0.2s;
                        " onmouseover="this.style.background='#CC0000'" onmouseout="this.style.background='#FF0000'">
                            ◀
                        </button>
                        <div style="text-align: center; min-width: 200px;">
                            <div id="currentElementNumber" style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">
                                - / ${counter - 1}
                            </div>
                            <div id="currentElementLabel" style="font-size: 11px; color: #AAA;">
                                Use ◀ ▶ to navigate
                            </div>
                        </div>
                        <button id="nextBtn" style="
                            background: #FF0000;
                            color: white;
                            border: none;
                            border-radius: 50%;
                            width: 40px;
                            height: 40px;
                            cursor: pointer;
                            font-size: 18px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            transition: all 0.2s;
                        " onmouseover="this.style.background='#CC0000'" onmouseout="this.style.background='#FF0000'">
                            ▶
                        </button>
                    `;
                    document.body.appendChild(navPanel);

                    // Create legend
                    const legend = document.createElement('div');
                    legend.className = 'detection-legend';
                    legend.style.cssText = `
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: rgba(0, 0, 0, 0.9);
                        color: white;
                        padding: 15px;
                        border-radius: 8px;
                        z-index: 1000002;
                        font-family: Arial, sans-serif;
                        font-size: 13px;
                        max-width: 300px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
                    `;
                    legend.innerHTML = `
                        <div style="font-weight: bold; margin-bottom: 10px; font-size: 16px;">
                            🎯 DETECTED ELEMENTS
                        </div>
                        <div style="margin-bottom: 5px;">Total Elements: <strong>${counter - 1}</strong></div>
                        <hr style="border: 1px solid #444; margin: 10px 0;">
                        <div style="font-size: 11px; line-height: 1.6;">
                            🔴 Red = Normal<br>
                            🟢 Green = Active (Current)<br>
                        </div>
                        <hr style="border: 1px solid #444; margin: 10px 0;">
                        <div style="font-size: 11px; line-height: 1.6;">
                            🎛️ Department Filters<br>
                            🔍 Search Boxes<br>
                            🔘 Buttons<br>
                            ☑️ Checkboxes<br>
                            📋 Dropdowns<br>
                            🔗 Links<br>
                            📝 Input Fields<br>
                            📑 Tabs<br>
                            📄 Pagination<br>
                            🖼️ Images
                        </div>
                        <hr style="border: 1px solid #444; margin: 10px 0;">
                        <button id="toggleHighlights" style="
                            width: 100%;
                            padding: 8px;
                            background: #FF0000;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-weight: bold;
                            margin-top: 5px;
                        ">Hide Highlights</button>
                    `;
                    document.body.appendChild(legend);

                    // Event listeners
                    document.getElementById('prevBtn').addEventListener('click', prevElement);
                    document.getElementById('nextBtn').addEventListener('click', nextElement);

                    // Keyboard navigation
                    document.addEventListener('keydown', (e) => {
                        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                            e.preventDefault();
                            prevElement();
                        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                            e.preventDefault();
                            nextElement();
                        }
                    });

                    // Toggle button functionality
                    let highlightsVisible = true;
                    document.getElementById('toggleHighlights').addEventListener('click', () => {
                        highlightsVisible = !highlightsVisible;
                        const visibility = highlightsVisible ? 'visible' : 'hidden';
                        document.querySelectorAll('.detection-highlight, .detection-badge, .detection-tooltip').forEach(el => {
                            el.style.visibility = visibility;
                        });
                        document.getElementById('toggleHighlights').textContent =
                            highlightsVisible ? 'Hide Highlights' : 'Show Highlights';
                    });

                    console.log(`✅ Highlighted ${counter - 1} elements`);
                    return counter - 1;
                }
            """)
            
            element_count = await page.evaluate("() => document.querySelectorAll('.detection-badge').length")
            
            print(f"✅ Highlighted {element_count} elements with red borders and numbers!")
            print()
            print("=" * 80)
            print("🎨 HIGHLIGHTING COMPLETE!")
            print("=" * 80)
            print()
            print("📍 Elements are now marked with:")
            print("   • Red borders")
            print("   • Numbered badges")
            print("   • Descriptive labels")
            print()
            print("🎛️ Controls:")
            print("   • Legend shown in top-right corner")
            print("   • Toggle button to show/hide highlights")
            print()
            print("⚠️  Keep this script running to maintain highlights")
            print("    Press Ctrl+C to remove highlights and exit")
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🧹 Cleaning up highlights...")
                await page.evaluate("""
                    () => {
                        document.querySelectorAll('.detection-highlight, .detection-badge, .detection-tooltip, .detection-legend').forEach(el => el.remove());
                    }
                """)
                print("✅ Highlights removed!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
