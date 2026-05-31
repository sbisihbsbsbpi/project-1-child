#!/usr/bin/env python3
"""
Targeted Logo Container & Insert Image Button Detection
Focuses on:
- Elements 4, 5, 6: Logo 1 containers (left, center, right)
- Elements 14, 15, 16: Logo 2 containers (left, center, right)
- Insert image icon buttons
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
    print("🎯 LOGO CONTAINERS & INSERT IMAGE BUTTONS - TARGETED DETECTION")
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

            print("🔍 Detecting logo containers and insert buttons...\n")

            # Inject targeted detection script
            result = await page.evaluate("""
                () => {
                    // Remove any existing highlights
                    document.querySelectorAll('.logo-highlight, .logo-label, .logo-legend, .logo-nav').forEach(el => el.remove());

                    const data = {
                        timestamp: new Date().toISOString(),
                        logo_containers: {
                            logo1: { left: null, center: null, right: null },
                            logo2: { left: null, center: null, right: null }
                        },
                        insert_buttons: []
                    };

                    // Get all contenteditable elements (we know elements 4,5,6 and 14,15,16)
                    const editableElements = Array.from(document.querySelectorAll('[contenteditable="true"]'));

                    // Map to logo containers
                    // Elements are 1-indexed, arrays are 0-indexed
                    if (editableElements.length >= 16) {
                        data.logo_containers.logo1.left = {
                            index: 4,
                            id: editableElements[3]?.id,
                            content: editableElements[3]?.textContent.trim(),
                            element: editableElements[3]
                        };
                        data.logo_containers.logo1.center = {
                            index: 5,
                            id: editableElements[4]?.id,
                            content: editableElements[4]?.textContent.trim(),
                            element: editableElements[4]
                        };
                        data.logo_containers.logo1.right = {
                            index: 6,
                            id: editableElements[5]?.id,
                            content: editableElements[5]?.textContent.trim(),
                            element: editableElements[5]
                        };

                        data.logo_containers.logo2.left = {
                            index: 14,
                            id: editableElements[13]?.id,
                            content: editableElements[13]?.textContent.trim(),
                            element: editableElements[13]
                        };
                        data.logo_containers.logo2.center = {
                            index: 15,
                            id: editableElements[14]?.id,
                            content: editableElements[14]?.textContent.trim(),
                            element: editableElements[14]
                        };
                        data.logo_containers.logo2.right = {
                            index: 16,
                            id: editableElements[15]?.id,
                            content: editableElements[15]?.textContent.trim(),
                            element: editableElements[15]
                        };
                    }

                    // Find all insert image buttons
                    const insertButtons = document.querySelectorAll('.icon-insert-image[aria-label="icon-insert-image"]');
                    insertButtons.forEach((btn, idx) => {
                        const rect = btn.getBoundingClientRect();
                        data.insert_buttons.push({
                            index: idx + 1,
                            classes: btn.className,
                            visible: rect.width > 0 && rect.height > 0,
                            position: { top: rect.top, left: rect.left },
                            element: btn
                        });
                    });

                    // Store in window for navigation
                    window.logoElements = [];
                    window.currentLogoIndex = 0;

                    // Helper to create highlights
                    function createHighlight(element, label, color, number) {
                        if (!element || !element.offsetParent) return;

                        const rect = element.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return;

                        window.logoElements.push({
                            number: number,
                            element: element,
                            label: label,
                            color: color,
                            rect: {
                                top: rect.top + window.scrollY,
                                left: rect.left + window.scrollX,
                                width: rect.width,
                                height: rect.height
                            }
                        });

                        // Create highlight border
                        const highlight = document.createElement('div');
                        highlight.className = 'logo-highlight';
                        highlight.dataset.number = number;
                        highlight.style.cssText = `
                            position: absolute;
                            top: ${rect.top + window.scrollY}px;
                            left: ${rect.left + window.scrollX}px;
                            width: ${rect.width}px;
                            height: ${rect.height}px;
                            border: 3px solid ${color};
                            pointer-events: none;
                            z-index: 999998;
                            box-sizing: border-box;
                            opacity: 0.5;
                            transition: all 0.3s ease;
                        `;

                        // Create number badge
                        const badge = document.createElement('div');
                        badge.className = 'logo-label';
                        badge.dataset.number = number;
                        badge.textContent = number;
                        badge.style.cssText = `
                            position: absolute;
                            top: ${rect.top + window.scrollY - 15}px;
                            left: ${rect.left + window.scrollX - 15}px;
                            background: ${color};
                            color: white;
                            border-radius: 50%;
                            width: 30px;
                            height: 30px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-weight: bold;
                            font-size: 14px;
                            z-index: 999999;
                            font-family: Arial, sans-serif;
                            box-shadow: 0 3px 6px rgba(0,0,0,0.4);
                            opacity: 0.5;
                            transition: all 0.3s ease;
                        `;

                        // Create label
                        const labelDiv = document.createElement('div');
                        labelDiv.className = 'logo-label';
                        labelDiv.dataset.number = number;
                        labelDiv.textContent = label;
                        labelDiv.style.cssText = `
                            position: absolute;
                            top: ${rect.top + window.scrollY - 35}px;
                            left: ${rect.left + window.scrollX + 20}px;
                            background: rgba(0, 0, 0, 0.9);
                            color: white;
                            padding: 4px 10px;
                            border-radius: 4px;
                            font-size: 12px;
                            z-index: 999999;
                            font-family: Arial, sans-serif;
                            white-space: nowrap;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                            opacity: 0;
                            transition: all 0.3s ease;
                        `;

                        document.body.appendChild(highlight);
                        document.body.appendChild(badge);
                        document.body.appendChild(labelDiv);
                    }

                    // Highlight logo containers
                    let logoNum = 1;

                    // Logo 1 containers (Purple/Magenta shades)
                    if (data.logo_containers.logo1.left?.element) {
                        createHighlight(data.logo_containers.logo1.left.element,
                            '🖼️ LOGO 1 - LEFT Align', '#FF00FF', logoNum++);
                    }
                    if (data.logo_containers.logo1.center?.element) {
                        createHighlight(data.logo_containers.logo1.center.element,
                            '🖼️ LOGO 1 - CENTER Align', '#CC00FF', logoNum++);
                    }
                    if (data.logo_containers.logo1.right?.element) {
                        createHighlight(data.logo_containers.logo1.right.element,
                            '🖼️ LOGO 1 - RIGHT Align', '#9900FF', logoNum++);
                    }

                    // Logo 2 containers (Cyan/Teal shades)
                    if (data.logo_containers.logo2.left?.element) {
                        createHighlight(data.logo_containers.logo2.left.element,
                            '🖼️ LOGO 2 - LEFT Align', '#00FFFF', logoNum++);
                    }
                    if (data.logo_containers.logo2.center?.element) {
                        createHighlight(data.logo_containers.logo2.center.element,
                            '🖼️ LOGO 2 - CENTER Align', '#00CCFF', logoNum++);
                    }
                    if (data.logo_containers.logo2.right?.element) {
                        createHighlight(data.logo_containers.logo2.right.element,
                            '🖼️ LOGO 2 - RIGHT Align', '#0099FF', logoNum++);
                    }

                    // Highlight insert image buttons
                    data.insert_buttons.forEach((btn, idx) => {
                        if (btn.element && btn.visible) {
                            createHighlight(btn.element.parentElement || btn.element,
                                '➕ Insert Image Button', '#00FF00', logoNum++);
                        }
                    });

                    // Navigation functions
                    function highlightElement(index) {
                        document.querySelectorAll('.logo-highlight').forEach(el => {
                            el.style.opacity = '0.5';
                            el.style.borderWidth = '3px';
                            el.style.boxShadow = 'none';
                        });
                        document.querySelectorAll('.logo-label').forEach(el => {
                            el.style.opacity = '0.5';
                        });

                        if (index < 0 || index >= window.logoElements.length) return;

                        const current = window.logoElements[index];
                        window.currentLogoIndex = index;

                        const highlights = document.querySelectorAll(`[data-number="${current.number}"]`);
                        highlights.forEach(el => {
                            if (el.classList.contains('logo-highlight')) {
                                el.style.opacity = '1';
                                el.style.borderWidth = '5px';
                                el.style.boxShadow = '0 0 30px rgba(255, 255, 0, 0.8)';
                            } else {
                                el.style.opacity = '1';
                            }
                        });

                        current.element.scrollIntoView({ behavior: 'smooth', block: 'center' });

                        document.getElementById('logoNavCounter').textContent = `${index + 1} / ${window.logoElements.length}`;
                        document.getElementById('logoCurrentInfo').innerHTML = `<strong>${current.label}</strong>`;
                    }

                    function nextElement() {
                        let newIndex = window.currentLogoIndex + 1;
                        if (newIndex >= window.logoElements.length) newIndex = 0;
                        highlightElement(newIndex);
                    }

                    function prevElement() {
                        let newIndex = window.currentLogoIndex - 1;
                        if (newIndex < 0) newIndex = window.logoElements.length - 1;
                        highlightElement(newIndex);
                    }

                    // Create navigation panel
                    const nav = document.createElement('div');
                    nav.className = 'logo-nav';
                    nav.style.cssText = `
                        position: fixed;
                        bottom: 20px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: rgba(0, 0, 0, 0.95);
                        color: white;
                        padding: 15px 25px;
                        border-radius: 15px;
                        z-index: 1000001;
                        font-family: Arial, sans-serif;
                        box-shadow: 0 5px 25px rgba(0,0,0,0.8);
                        display: flex;
                        align-items: center;
                        gap: 20px;
                    `;
                    nav.innerHTML = `
                        <button id="logoPrevBtn" style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 12px 24px;
                            cursor: pointer;
                            font-weight: bold;
                            font-size: 15px;
                            transition: all 0.2s;
                            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4);
                        ">◀ Prev</button>

                        <div style="text-align: center; min-width: 250px;">
                            <div id="logoNavCounter" style="font-size: 20px; font-weight: bold; margin-bottom: 5px; color: #FFD700;">
                                1 / ${window.logoElements.length}
                            </div>
                            <div id="logoCurrentInfo" style="font-size: 12px; color: #00FF00;">
                                Starting...
                            </div>
                        </div>

                        <button id="logoNextBtn" style="
                            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 12px 24px;
                            cursor: pointer;
                            font-weight: bold;
                            font-size: 15px;
                            transition: all 0.2s;
                            box-shadow: 0 2px 10px rgba(245, 87, 108, 0.4);
                        ">Next ▶</button>
                    `;
                    document.body.appendChild(nav);

                    // Legend
                    const legend = document.createElement('div');
                    legend.className = 'logo-legend';
                    legend.style.cssText = `
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: rgba(0, 0, 0, 0.95);
                        color: white;
                        padding: 20px;
                        border-radius: 10px;
                        z-index: 1000001;
                        font-family: Arial, sans-serif;
                        font-size: 13px;
                        max-width: 320px;
                        box-shadow: 0 5px 20px rgba(0,0,0,0.6);
                    `;
                    legend.innerHTML = `
                        <div style="font-weight: bold; margin-bottom: 15px; font-size: 16px; border-bottom: 2px solid #FFD700; padding-bottom: 10px; color: #FFD700;">
                            🎯 LOGO CONTAINERS & BUTTONS
                        </div>
                        <div style="margin: 10px 0; padding: 8px; background: rgba(255,0,255,0.2); border-left: 4px solid #FF00FF; border-radius: 4px;">
                            <strong style="color: #FF00FF;">🖼️ LOGO 1 Containers</strong><br/>
                            <span style="font-size: 11px; color: #DDD;">
                                • Elements 4, 5, 6<br/>
                                • Left, Center, Right alignment
                            </span>
                        </div>
                        <div style="margin: 10px 0; padding: 8px; background: rgba(0,255,255,0.2); border-left: 4px solid #00FFFF; border-radius: 4px;">
                            <strong style="color: #00FFFF;">🖼️ LOGO 2 Containers</strong><br/>
                            <span style="font-size: 11px; color: #DDD;">
                                • Elements 14, 15, 16<br/>
                                • Left, Center, Right alignment
                            </span>
                        </div>
                        <div style="margin: 10px 0; padding: 8px; background: rgba(0,255,0,0.2); border-left: 4px solid #00FF00; border-radius: 4px;">
                            <strong style="color: #00FF00;">➕ Insert Image Buttons</strong><br/>
                            <span style="font-size: 11px; color: #DDD;">
                                • ${data.insert_buttons.length} buttons found<br/>
                                • icon-insert-image class
                            </span>
                        </div>
                        <hr style="border: 1px solid #444; margin: 15px 0;">
                        <div style="font-size: 11px; color: #888; text-align: center;">
                            Total: ${window.logoElements.length} elements<br/>
                            Use ← → arrow keys to navigate
                        </div>
                    `;
                    document.body.appendChild(legend);

                    // Event listeners
                    document.getElementById('logoPrevBtn').addEventListener('click', prevElement);
                    document.getElementById('logoNextBtn').addEventListener('click', nextElement);

                    document.addEventListener('keydown', (e) => {
                        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                            e.preventDefault();
                            nextElement();
                        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                            e.preventDefault();
                            prevElement();
                        }
                    });

                    // Hover effects
                    const prevBtn = document.getElementById('logoPrevBtn');
                    const nextBtn = document.getElementById('logoNextBtn');

                    prevBtn.addEventListener('mouseenter', () => {
                        prevBtn.style.transform = 'scale(1.05) translateY(-2px)';
                    });
                    prevBtn.addEventListener('mouseleave', () => {
                        prevBtn.style.transform = 'scale(1) translateY(0)';
                    });

                    nextBtn.addEventListener('mouseenter', () => {
                        nextBtn.style.transform = 'scale(1.05) translateY(-2px)';
                    });
                    nextBtn.addEventListener('mouseleave', () => {
                        nextBtn.style.transform = 'scale(1) translateY(0)';
                    });

                    // Initialize
                    setTimeout(() => {
                        if (window.logoElements.length > 0) {
                            highlightElement(0);
                        }
                    }, 500);

                    console.log('Logo container detection complete!');
                    console.log(`Found ${window.logoElements.length} elements`);
                    console.log(`Logo 1 containers: 4, 5, 6 (Left, Center, Right)`);
                    console.log(`Logo 2 containers: 14, 15, 16 (Left, Center, Right)`);
                    console.log(`Insert buttons: ${data.insert_buttons.length}`);

                    return data;
                }
            """)

            print(f"✅ Highlighting complete!\n")

            # Save results
            filename = f"logo_containers_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Clean result for JSON serialization
            clean_result = {
                'timestamp': result['timestamp'],
                'logo_containers': {
                    'logo1': {
                        'left': {
                            'index': result['logo_containers']['logo1']['left']['index'],
                            'id': result['logo_containers']['logo1']['left']['id'],
                            'content': result['logo_containers']['logo1']['left']['content']
                        } if result['logo_containers']['logo1']['left'] else None,
                        'center': {
                            'index': result['logo_containers']['logo1']['center']['index'],
                            'id': result['logo_containers']['logo1']['center']['id'],
                            'content': result['logo_containers']['logo1']['center']['content']
                        } if result['logo_containers']['logo1']['center'] else None,
                        'right': {
                            'index': result['logo_containers']['logo1']['right']['index'],
                            'id': result['logo_containers']['logo1']['right']['id'],
                            'content': result['logo_containers']['logo1']['right']['content']
                        } if result['logo_containers']['logo1']['right'] else None
                    },
                    'logo2': {
                        'left': {
                            'index': result['logo_containers']['logo2']['left']['index'],
                            'id': result['logo_containers']['logo2']['left']['id'],
                            'content': result['logo_containers']['logo2']['left']['content']
                        } if result['logo_containers']['logo2']['left'] else None,
                        'center': {
                            'index': result['logo_containers']['logo2']['center']['index'],
                            'id': result['logo_containers']['logo2']['center']['id'],
                            'content': result['logo_containers']['logo2']['center']['content']
                        } if result['logo_containers']['logo2']['center'] else None,
                        'right': {
                            'index': result['logo_containers']['logo2']['right']['index'],
                            'id': result['logo_containers']['logo2']['right']['id'],
                            'content': result['logo_containers']['logo2']['right']['content']
                        } if result['logo_containers']['logo2']['right'] else None
                    }
                },
                'insert_buttons': [{
                    'index': btn['index'],
                    'classes': btn['classes'],
                    'visible': btn['visible'],
                    'position': btn['position']
                } for btn in result['insert_buttons']]
            }

            with open(filename, 'w') as f:
                json.dump(clean_result, f, indent=2)


            print("=" * 100)
            print("📊 LOGO CONTAINERS DETECTION SUMMARY")
            print("=" * 100)

            print("\n🖼️  LOGO 1 CONTAINERS (Elements 4, 5, 6):")
            print("   " + "─" * 60)
            logo1 = result['logo_containers']['logo1']
            if logo1['left']:
                print(f"   📌 LEFT (Element 4):")
                print(f"      ID: {logo1['left']['id']}")
                print(f"      Content: {logo1['left']['content'][:50] if logo1['left']['content'] else '(empty)'}")
            if logo1['center']:
                print(f"   📌 CENTER (Element 5):")
                print(f"      ID: {logo1['center']['id']}")
                print(f"      Content: {logo1['center']['content'][:50] if logo1['center']['content'] else '(empty)'}")
            if logo1['right']:
                print(f"   📌 RIGHT (Element 6):")
                print(f"      ID: {logo1['right']['id']}")
                print(f"      Content: {logo1['right']['content'][:50] if logo1['right']['content'] else '(empty)'}")

            print("\n🖼️  LOGO 2 CONTAINERS (Elements 14, 15, 16):")
            print("   " + "─" * 60)
            logo2 = result['logo_containers']['logo2']
            if logo2['left']:
                print(f"   📌 LEFT (Element 14):")
                print(f"      ID: {logo2['left']['id']}")
                print(f"      Content: {logo2['left']['content'][:50] if logo2['left']['content'] else '(empty)'}")
            if logo2['center']:
                print(f"   📌 CENTER (Element 15):")
                print(f"      ID: {logo2['center']['id']}")
                print(f"      Content: {logo2['center']['content'][:50] if logo2['center']['content'] else '(empty)'}")
            if logo2['right']:
                print(f"   📌 RIGHT (Element 16):")
                print(f"      ID: {logo2['right']['id']}")
                print(f"      Content: {logo2['right']['content'][:50] if logo2['right']['content'] else '(empty)'}")

            print("\n➕ INSERT IMAGE BUTTONS:")
            print("   " + "─" * 60)
            print(f"   Total Found: {len(result['insert_buttons'])}")
            for btn in result['insert_buttons'][:5]:
                print(f"   Button {btn['index']}: Visible={btn['visible']}, Position=({btn['position']['top']:.0f}, {btn['position']['left']:.0f})")

            print("\n" + "=" * 100)
            print("🎨 VISUAL HIGHLIGHTS ACTIVE")
            print("=" * 100)
            print("\n✅ Logo containers highlighted with colored borders")
            print("✅ Insert image buttons highlighted in green")
            print("✅ Navigation panel at bottom center")
            print("✅ Legend at top right")

            print("\n🎮 NAVIGATION:")
            print("   • Click 'Prev' / 'Next' buttons")
            print("   • Use ← → arrow keys")

            print("\n🎨 COLOR GUIDE:")
            print("   🟣 Purple/Magenta = Logo 1 containers (4, 5, 6)")
            print("   🔵 Cyan/Teal      = Logo 2 containers (14, 15, 16)")
            print("   🟢 Green          = Insert Image buttons")

            print(f"\n📁 Results saved to: {filename}")
            print("\n⚠️  Keep this script running to maintain highlights")
            print("    Press Ctrl+C to remove highlights and exit\n")

            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🧹 Cleaning up highlights...")
                await page.evaluate("""
                    () => {
                        document.querySelectorAll('.logo-highlight, .logo-label, .logo-legend, .logo-nav').forEach(el => el.remove());
                        delete window.logoElements;
                        delete window.currentLogoIndex;
                    }
                """)
                print("✅ Highlights removed!")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

