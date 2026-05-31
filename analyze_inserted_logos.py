#!/usr/bin/env python3
"""
Analyze Template After Logo Insertion
Connect to CDP and inspect what the automation did
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


# All 6 logo container IDs
LOGO_CONTAINERS = [
    # Logo 1
    {"name": "Logo 1 LEFT", "id": "6f0b8570-c4dc-45bd-b746-40e3af9af3bb", "alignment": "left"},
    {"name": "Logo 1 CENTER", "id": "7653caa9-31b7-4e2b-8233-f0bda43672ea", "alignment": "center"},
    {"name": "Logo 1 RIGHT", "id": "47da3c0a-2c2b-4f8f-8a31-4ba8fdae03aa", "alignment": "right"},
    
    # Logo 2
    {"name": "Logo 2 LEFT", "id": "9fa2920b-10f8-48d2-9947-b014398d21be", "alignment": "left"},
    {"name": "Logo 2 CENTER", "id": "983932ae-d79a-40fe-a9ba-df07c9beee47", "alignment": "center"},
    {"name": "Logo 2 RIGHT", "id": "9d454086-c1f2-4bf0-b4a7-8e95dc244aae", "alignment": "right"},
]


async def main():
    print("=" * 100)
    print("🔍 ANALYZING TEMPLATE AFTER LOGO INSERTION")
    print("=" * 100)
    
    template_id = "667f0befd4964026ee7b6e48"
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            
            # Find the template editor page
            print("🔍 Looking for template editor page...")
            pages = context.pages
            target_page = None
            
            for page in pages:
                if template_id in page.url:
                    target_page = page
                    print(f"✅ Found template editor page: {page.url}")
                    break
            
            if not target_page:
                print(f"❌ Template editor page not found!")
                print(f"   Looking for URL containing: {template_id}")
                print(f"\n📋 Available pages:")
                for i, page in enumerate(pages, 1):
                    print(f"   {i}. {page.url}")
                return
            
            await target_page.bring_to_front()
            await asyncio.sleep(2)
            
            # Analyze each container
            print(f"\n{'='*100}")
            print(f"📊 ANALYZING ALL 6 LOGO CONTAINERS")
            print(f"{'='*100}")
            
            analysis_results = []
            
            for i, container in enumerate(LOGO_CONTAINERS, 1):
                print(f"\n{'─'*100}")
                print(f"📍 Container {i}/6: {container['name']}")
                print(f"{'─'*100}")
                print(f"   ID: {container['id']}")
                print(f"   Alignment: {container['alignment']}")
                
                # Analyze the container
                result = await target_page.evaluate(f"""
                    () => {{
                        const containerId = "{container['id']}";
                        const container = document.querySelector(`div[id="${{containerId}}"]`);
                        
                        if (!container) {{
                            return {{
                                found: false,
                                error: 'Container not found in DOM'
                            }};
                        }}
                        
                        // Check if it's the TEXT_TEMPLATE version (contenteditable)
                        const isContentEditable = container.classList.contains('TEXT_TEMPLATE');
                        const isEditable = container.hasAttribute('contenteditable');
                        
                        // Get content
                        const innerHTML = container.innerHTML;
                        const textContent = container.textContent.trim();
                        const hasImage = container.querySelector('img') !== null;
                        
                        // Get visibility
                        const style = window.getComputedStyle(container);
                        const isVisible = style.display !== 'none' && 
                                         style.visibility !== 'hidden' &&
                                         style.opacity !== '0';
                        
                        const rect = container.getBoundingClientRect();
                        const hasSize = rect.width > 0 && rect.height > 0;
                        
                        // Image analysis
                        let imageInfo = null;
                        if (hasImage) {{
                            const img = container.querySelector('img');
                            const imgRect = img.getBoundingClientRect();
                            imageInfo = {{
                                src: img.src.substring(0, 100),
                                alt: img.alt || '',
                                width: Math.round(imgRect.width),
                                height: Math.round(imgRect.height),
                                naturalWidth: img.naturalWidth,
                                naturalHeight: img.naturalHeight
                            }};
                        }}
                        
                        // Parent structure
                        const parentClass = container.parentElement?.className || '';
                        const hasParentWrapper = parentClass.includes('sortableItemDisplayPadding');
                        
                        return {{
                            found: true,
                            isContentEditable: isContentEditable,
                            isEditable: isEditable,
                            hasContent: innerHTML.length > 0,
                            contentLength: innerHTML.length,
                            hasImage: hasImage,
                            imageInfo: imageInfo,
                            isVisible: isVisible,
                            hasSize: hasSize,
                            dimensions: {{
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                top: Math.round(rect.top),
                                left: Math.round(rect.left)
                            }},
                            hasParentWrapper: hasParentWrapper,
                            htmlPreview: innerHTML.substring(0, 200)
                        }};
                    }}
                """)
                
                if not result.get('found'):
                    print(f"   ❌ {result.get('error')}")
                    analysis_results.append({
                        "container": container['name'],
                        "status": "NOT_FOUND"
                    })
                    continue
                
                # Display results
                status = "✅ HAS LOGO" if result['hasImage'] else "⭕ EMPTY"
                print(f"\n   Status: {status}")
                print(f"   Visible: {'✅' if result['isVisible'] else '❌'}")
                print(f"   Has Size: {'✅' if result['hasSize'] else '❌'}")
                print(f"   Dimensions: {result['dimensions']['width']}x{result['dimensions']['height']}px")
                print(f"   Content Length: {result['contentLength']} characters")
                
                if result['hasImage']:
                    img_info = result['imageInfo']
                    print(f"\n   📷 IMAGE DETAILS:")
                    print(f"      Size: {img_info['width']}x{img_info['height']}px (display)")
                    print(f"      Natural: {img_info['naturalWidth']}x{img_info['naturalHeight']}px")
                    print(f"      Src: {img_info['src']}...")
                    print(f"      Alt: {img_info['alt'] or 'N/A'}")
                else:
                    print(f"\n   📄 HTML Preview: {result['htmlPreview'] or '(empty)'}")
                
                analysis_results.append({
                    "container": container['name'],
                    "id": container['id'],
                    "alignment": container['alignment'],
                    "status": "HAS_LOGO" if result['hasImage'] else "EMPTY",
                    "visible": result['isVisible'],
                    "hasSize": result['hasSize'],
                    "dimensions": result['dimensions'],
                    "imageInfo": result['imageInfo']
                })

            # Summary
            print(f"\n\n{'='*100}")
            print(f"📊 SUMMARY")
            print(f"{'='*100}")

            total = len(analysis_results)
            has_logo = sum(1 for r in analysis_results if r['status'] == 'HAS_LOGO')
            empty = sum(1 for r in analysis_results if r['status'] == 'EMPTY')
            not_found = sum(1 for r in analysis_results if r['status'] == 'NOT_FOUND')

            print(f"\n   Total Containers: {total}")
            print(f"   ✅ With Logo: {has_logo}")
            print(f"   ⭕ Empty: {empty}")
            print(f"   ❌ Not Found: {not_found}")

            print(f"\n{'─'*100}")
            print(f"CONTAINER STATUS:")
            print(f"{'─'*100}")

            for r in analysis_results:
                if r['status'] == 'HAS_LOGO':
                    img = r['imageInfo']
                    print(f"   ✅ {r['container']}: {img['width']}x{img['height']}px")
                elif r['status'] == 'EMPTY':
                    vis = "visible" if r['visible'] else "hidden"
                    print(f"   ⭕ {r['container']}: Empty ({vis})")
                else:
                    print(f"   ❌ {r['container']}: {r['status']}")

            # Save results
            output_file = f"logo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'template_id': template_id,
                    'summary': {
                        'total': total,
                        'has_logo': has_logo,
                        'empty': empty,
                        'not_found': not_found
                    },
                    'containers': analysis_results
                }, f, indent=2)

            print(f"\n💾 Analysis saved to: {output_file}")

            # Take screenshot
            screenshot_path = f"logo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await target_page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")

            print(f"\n{'='*100}")
            print(f"✅ ANALYSIS COMPLETE")
            print(f"{'='*100}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

