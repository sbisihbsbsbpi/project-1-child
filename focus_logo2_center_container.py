#!/usr/bin/env python3
"""
Focus on Logo 2 CENTER Alignment Container
Element 15 - ID: 983932ae-d79a-40fe-a9ba-df07c9beee47
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
    print("🎯 LOGO 2 CENTER ALIGNMENT - FOCUSED DETECTION")
    print("=" * 100)

    template_id = "667f0befd4964026ee7b6e48"
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    target_id = "983932ae-d79a-40fe-a9ba-df07c9beee47"

    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")

            context = browser.contexts[0]
            page = await context.new_page()

            print(f"🌐 Navigating to edit page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)

            print(f"🔍 Focusing on Logo 2 CENTER container...")
            print(f"   Target ID: {target_id}\n")

            # Inject focused detection script
            result = await page.evaluate(f"""
                () => {{
                    // Remove any existing highlights
                    document.querySelectorAll('.focus-highlight, .focus-label, .focus-info').forEach(el => el.remove());

                    const targetId = '{target_id}';
                    const data = {{
                        timestamp: new Date().toISOString(),
                        target_element: null,
                        structure: {{
                            contenteditable_div: null,
                            parent_wrapper: null,
                            sortable_padding: null,
                            unselectable_div: null,
                            delete_icon: null
                        }},
                        properties: {{}},
                        rect: null,
                        nearest_insert_button: null
                    }};

                    // Find the target element - must be the contenteditable one
                    const allMatches = Array.from(document.querySelectorAll(`[id="${{targetId}}"]`));
                    const targetElement = allMatches.find(el => el.getAttribute('contenteditable') === 'true');

                    if (!targetElement) {{
                        console.error('Target contenteditable element not found!');
                        console.log('Found elements with this ID:', allMatches);
                        return {{ error: 'Contenteditable element not found', target_id: targetId, found: allMatches.length }};
                    }}

                    console.log('Target element found:', targetElement);
                    console.log('Class:', targetElement.className);
                    console.log('Contenteditable:', targetElement.getAttribute('contenteditable'));

                    data.target_element = {{
                        id: targetElement.id,
                        tag: targetElement.tagName,
                        className: targetElement.className,
                        contenteditable: targetElement.getAttribute('contenteditable'),
                        placeholder: targetElement.getAttribute('placeholder'),
                        'data-offset': targetElement.getAttribute('data-offset'),
                        textContent: targetElement.textContent,
                        innerHTML: targetElement.innerHTML
                    }};

                    // Analyze structure
                    const rect = targetElement.getBoundingClientRect();
                    data.rect = {{
                        top: rect.top + window.scrollY,
                        left: rect.left + window.scrollX,
                        width: rect.width,
                        height: rect.height,
                        bottom: rect.bottom + window.scrollY,
                        right: rect.right + window.scrollX
                    }};

                    // Get parent structure
                    let current = targetElement;
                    let level = 0;
                    while (current && level < 10) {{
                        const classes = current.className || '';

                        if (classes.includes('sortableItemDisplayPadding')) {{
                            data.structure.sortable_padding = {{
                                tag: current.tagName,
                                className: current.className
                            }};
                        }}
                        if (classes.includes('elementUnselectable')) {{
                            data.structure.unselectable_div = {{
                                tag: current.tagName,
                                className: current.className
                            }};

                            // Find delete icon within
                            const deleteIcon = current.querySelector('.icon-cross');
                            if (deleteIcon) {{
                                data.structure.delete_icon = {{
                                    className: deleteIcon.className,
                                    'aria-label': deleteIcon.getAttribute('aria-label'),
                                    hidden: deleteIcon.className.includes('hidden')
                                }};
                            }}
                        }}

                        current = current.parentElement;
                        level++;
                    }}

                    // Find nearest insert image button
                    const insertButtons = document.querySelectorAll('.icon-insert-image');
                    let nearestButton = null;
                    let nearestDistance = Infinity;

                    insertButtons.forEach(btn => {{
                        const btnRect = btn.getBoundingClientRect();
                        const distance = Math.sqrt(
                            Math.pow(btnRect.top - rect.top, 2) +
                            Math.pow(btnRect.left - rect.left, 2)
                        );
                        if (distance < nearestDistance) {{
                            nearestDistance = distance;
                            nearestButton = {{
                                distance: distance,
                                position: {{
                                    top: btnRect.top + window.scrollY,
                                    left: btnRect.left + window.scrollX
                                }},
                                className: btn.className
                            }};
                        }}
                    }});

                    data.nearest_insert_button = nearestButton;

                    // Create massive highlight
                    const highlight = document.createElement('div');
                    highlight.className = 'focus-highlight';
                    highlight.style.cssText = `
                        position: absolute;
                        top: ${{data.rect.top - 10}}px;
                        left: ${{data.rect.left - 10}}px;
                        width: ${{data.rect.width + 20}}px;
                        height: ${{data.rect.height + 20}}px;
                        border: 6px solid #00FF00;
                        background: rgba(0, 255, 0, 0.1);
                        pointer-events: none;
                        z-index: 999998;
                        box-sizing: border-box;
                        box-shadow: 0 0 40px rgba(0, 255, 0, 0.8), inset 0 0 20px rgba(0, 255, 0, 0.3);
                        animation: pulse 2s infinite;
                    `;
                    document.body.appendChild(highlight);

                    // Add CSS animation
                    const style = document.createElement('style');
                    style.textContent = `
                        @keyframes pulse {{
                            0%, 100% {{
                                border-color: #00FF00;
                                box-shadow: 0 0 40px rgba(0, 255, 0, 0.8), inset 0 0 20px rgba(0, 255, 0, 0.3);
                            }}
                            50% {{
                                border-color: #00FFFF;
                                box-shadow: 0 0 60px rgba(0, 255, 255, 1), inset 0 0 30px rgba(0, 255, 255, 0.5);
                            }}
                        }}
                    `;
                    document.head.appendChild(style);

                    // Create label
                    const label = document.createElement('div');
                    label.className = 'focus-label';
                    label.style.cssText = `
                        position: absolute;
                        top: ${{data.rect.top - 50}}px;
                        left: ${{data.rect.left}}px;
                        background: linear-gradient(135deg, #00FF00 0%, #00FFFF 100%);
                        color: #000;
                        padding: 10px 20px;
                        border-radius: 8px;
                        font-size: 16px;
                        z-index: 999999;
                        font-family: Arial, sans-serif;
                        font-weight: bold;
                        box-shadow: 0 4px 15px rgba(0, 255, 0, 0.6);
                    `;
                    label.innerHTML = '🎯 LOGO 2 - CENTER ALIGNMENT<br/><span style="font-size: 12px;">Element 15 (Index 14)</span>';
                    document.body.appendChild(label);

                    // Create info panel
                    const infoPanel = document.createElement('div');
                    infoPanel.className = 'focus-info';
                    infoPanel.style.cssText = `
                        position: fixed;
                        top: 50%;
                        right: 20px;
                        transform: translateY(-50%);
                        background: rgba(0, 0, 0, 0.95);
                        color: white;
                        padding: 25px;
                        border-radius: 12px;
                        z-index: 1000001;
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                        max-width: 400px;
                        box-shadow: 0 5px 30px rgba(0, 255, 0, 0.4);
                        border: 2px solid #00FF00;
                    `;
                    infoPanel.innerHTML = `
                        <div style="font-weight: bold; margin-bottom: 15px; font-size: 18px; color: #00FF00; border-bottom: 2px solid #00FF00; padding-bottom: 10px;">
                            📋 ELEMENT DETAILS
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(0, 255, 0, 0.1); border-radius: 4px;">
                            <strong style="color: #00FFFF;">🆔 Element ID:</strong><br/>
                            <code style="color: #FFD700; font-size: 10px; word-break: break-all;">${{targetId}}</code>
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(0, 255, 0, 0.1); border-radius: 4px;">
                            <strong style="color: #00FFFF;">🏷️ Class:</strong><br/>
                            <code style="color: #FFD700; font-size: 10px;">TEXT_TEMPLATE focus_node</code>
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(0, 255, 0, 0.1); border-radius: 4px;">
                            <strong style="color: #00FFFF;">✏️ Contenteditable:</strong><br/>
                            <code style="color: #FFD700;">${{data.target_element.contenteditable}}</code>
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(0, 255, 0, 0.1); border-radius: 4px;">
                            <strong style="color: #00FFFF;">📐 Dimensions:</strong><br/>
                            <code style="color: #FFD700;">
                                Width: ${{Math.round(data.rect.width)}}px<br/>
                                Height: ${{Math.round(data.rect.height)}}px
                            </code>
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(0, 255, 0, 0.1); border-radius: 4px;">
                            <strong style="color: #00FFFF;">📍 Position:</strong><br/>
                            <code style="color: #FFD700;">
                                Top: ${{Math.round(data.rect.top)}}px<br/>
                                Left: ${{Math.round(data.rect.left)}}px
                            </code>
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(0, 255, 0, 0.1); border-radius: 4px;">
                            <strong style="color: #00FFFF;">📝 Content:</strong><br/>
                            <code style="color: #FFD700;">${{data.target_element.textContent || '(empty)'}}</code>
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(255, 165, 0, 0.2); border-radius: 4px; border-left: 4px solid #FFA500;">
                            <strong style="color: #FFA500;">🗑️ Delete Icon:</strong><br/>
                            <code style="color: #FFD700; font-size: 10px;">
                                Status: ${{data.structure.delete_icon?.hidden ? 'Hidden' : 'Visible'}}<br/>
                                Class: icon-cross
                            </code>
                        </div>

                        <div style="margin: 10px 0; padding: 10px; background: rgba(0, 150, 255, 0.2); border-radius: 4px; border-left: 4px solid #0096FF;">
                            <strong style="color: #0096FF;">➕ Nearest Insert Button:</strong><br/>
                            <code style="color: #FFD700; font-size: 10px;">
                                Distance: ${{nearestButton ? Math.round(nearestButton.distance) : 'N/A'}}px<br/>
                                Position: ${{nearestButton ? `(${{Math.round(nearestButton.position.top)}}, ${{Math.round(nearestButton.position.left)}})` : 'N/A'}}
                            </code>
                        </div>

                        <hr style="border: 1px solid #444; margin: 15px 0;">

                        <div style="font-size: 11px; color: #888; text-align: center; margin-top: 10px;">
                            🎯 Logo 2 CENTER Container<br/>
                            Ready for logo insertion
                        </div>
                    `;
                    document.body.appendChild(infoPanel);

                    // Scroll to element
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                    console.log('Logo 2 CENTER container focused!');
                    console.log('Element ID:', targetId);
                    console.log('Full data:', data);

                    return data;
                }}
            """)


            print("✅ Element found and highlighted!\n")

            # Save results
            filename = f"logo2_center_focus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Clean result for JSON
            clean_result = {
                'timestamp': result['timestamp'],
                'target_element': result['target_element'],
                'structure': result['structure'],
                'rect': result['rect'],
                'nearest_insert_button': result['nearest_insert_button']
            }

            with open(filename, 'w') as f:
                json.dump(clean_result, f, indent=2)

            print("=" * 100)
            print("🎯 LOGO 2 CENTER ALIGNMENT - ANALYSIS COMPLETE")
            print("=" * 100)

            print("\n📋 ELEMENT INFORMATION:")
            print("   " + "─" * 70)
            print(f"   🆔 ID: {result['target_element']['id']}")
            print(f"   🏷️  Class: {result['target_element']['className']}")
            print(f"   📝 Tag: {result['target_element']['tag']}")
            print(f"   ✏️  Contenteditable: {result['target_element']['contenteditable']}")
            print(f"   📊 Data-offset: {result['target_element']['data-offset']}")
            print(f"   📄 Content: {result['target_element']['textContent'] or '(empty)'}")

            print("\n📐 DIMENSIONS & POSITION:")
            print("   " + "─" * 70)
            print(f"   📏 Width: {result['rect']['width']:.0f}px")
            print(f"   📏 Height: {result['rect']['height']:.0f}px")
            print(f"   📍 Top: {result['rect']['top']:.0f}px")
            print(f"   📍 Left: {result['rect']['left']:.0f}px")

            print("\n🏗️  STRUCTURE:")
            print("   " + "─" * 70)
            if result['structure']['sortable_padding']:
                print(f"   ✅ Sortable Padding: {result['structure']['sortable_padding']['className']}")
            if result['structure']['unselectable_div']:
                print(f"   ✅ Unselectable Div: {result['structure']['unselectable_div']['className'][:60]}...")
            if result['structure']['delete_icon']:
                icon = result['structure']['delete_icon']
                print(f"   🗑️  Delete Icon: {icon['aria-label']} - {'Hidden' if icon['hidden'] else 'Visible'}")

            print("\n➕ NEAREST INSERT BUTTON:")
            print("   " + "─" * 70)
            if result['nearest_insert_button']:
                btn = result['nearest_insert_button']
                print(f"   📏 Distance: {btn['distance']:.0f}px")
                print(f"   📍 Position: ({btn['position']['top']:.0f}, {btn['position']['left']:.0f})")
                print(f"   🏷️  Class: {btn['className'][:60]}...")

            print("\n" + "=" * 100)
            print("🎨 VISUAL HIGHLIGHTS")
            print("=" * 100)
            print("\n✅ Container highlighted with pulsing green border")
            print("✅ Label showing 'LOGO 2 - CENTER ALIGNMENT'")
            print("✅ Info panel on right side with all details")
            print("✅ Auto-scrolled to center of view")

            print("\n💡 KEY FEATURES:")
            print("   • Pulsing animation (green → cyan → green)")
            print("   • Glowing box shadow effect")
            print("   • Semi-transparent background overlay")
            print("   • Complete structure analysis displayed")

            print("\n📌 HTML STRUCTURE:")
            print("   " + "─" * 70)
            print("   <div class='sortableItemDisplayPadding'>")
            print("     <div class='templates_SortableItem_elementUnselectable__3cVv8L95sj'>")
            print("       <div class='icon-cross hidden'> <!-- Delete icon -->")
            print("       <div id='983932ae-d79a-40fe-a9ba-df07c9beee47'>")
            print("         <div style='width: 100%; height: auto;'>")
            print("           <div class='TEXT_TEMPLATE focus_node'")
            print("                id='983932ae-d79a-40fe-a9ba-df07c9beee47'")
            print("                contenteditable='true'>")
            print("             <!-- LOGO 2 CENTER CONTENT HERE -->")
            print("           </div>")
            print("         </div>")
            print("       </div>")
            print("     </div>")
            print("   </div>")

            print(f"\n📁 Results saved to: {filename}")
            print("\n⚠️  Keep this script running to maintain highlight")
            print("    Press Ctrl+C to remove highlight and exit\n")

            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🧹 Cleaning up highlight...")
                await page.evaluate("""
                    () => {
                        document.querySelectorAll('.focus-highlight, .focus-label, .focus-info').forEach(el => el.remove());
                    }
                """)
                print("✅ Highlight removed!")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

