#!/usr/bin/env python3
"""
Analyze ALL Images in Template
Find any images that were inserted anywhere in the template
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
    print("🔍 ANALYZING ALL IMAGES IN TEMPLATE")
    print("=" * 100)
    
    template_id = "667f0befd4964026ee7b6e48"
    
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
                return
            
            await target_page.bring_to_front()
            await asyncio.sleep(2)
            
            # Find ALL images in the template
            print(f"\n{'='*100}")
            print(f"📊 SEARCHING FOR ALL IMAGES")
            print(f"{'='*100}")
            
            result = await target_page.evaluate("""
                () => {
                    // Find all images in the document
                    const allImages = Array.from(document.querySelectorAll('img'));
                    
                    // Categorize images
                    const templateImages = [];
                    const uiImages = [];
                    
                    allImages.forEach((img, idx) => {
                        const src = img.src || '';
                        const rect = img.getBoundingClientRect();
                        const parent = img.parentElement;
                        const closestContainer = img.closest('[id*="f0b8570"], [id*="653caa9"], [id*="7da3c0a"], [id*="fa2920b"], [id*="83932ae"], [id*="d454086"]');
                        
                        const imgInfo = {
                            index: idx,
                            src: src.substring(0, 120),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            naturalWidth: img.naturalWidth,
                            naturalHeight: img.naturalHeight,
                            alt: img.alt || '',
                            parentTag: parent?.tagName,
                            parentClass: parent?.className.substring(0, 60) || '',
                            inLogoContainer: closestContainer !== null,
                            containerUUID: closestContainer?.id || null,
                            visible: rect.width > 0 && rect.height > 0
                        };
                        
                        // Categorize
                        if (src.includes('amazonaws.com/media_') || src.includes('Tilton') || closestContainer) {
                            templateImages.push(imgInfo);
                        } else {
                            uiImages.push(imgInfo);
                        }
                    });
                    
                    // Also check the specific containers
                    const containerIds = [
                        '6f0b8570-c4dc-45bd-b746-40e3af9af3bb',  // Logo 1 LEFT
                        '7653caa9-31b7-4e2b-8233-f0bda43672ea',  // Logo 1 CENTER
                        '47da3c0a-2c2b-4f8f-8a31-4ba8fdae03aa',  // Logo 1 RIGHT
                        '9fa2920b-10f8-48d2-9947-b014398d21be',  // Logo 2 LEFT
                        '983932ae-d79a-40fe-a9ba-df07c9beee47',  // Logo 2 CENTER
                        '9d454086-c1f2-4bf0-b4a7-8e95dc244aae'   // Logo 2 RIGHT
                    ];
                    
                    const containerCheck = containerIds.map(id => {
                        const container = document.querySelector(`[id="${id}"]`);
                        if (!container) return { id, found: false };
                        
                        const hasImg = container.querySelector('img') !== null;
                        const innerHTML = container.innerHTML;
                        
                        return {
                            id: id.substring(0, 8) + '...',
                            found: true,
                            hasImage: hasImg,
                            contentLength: innerHTML.length,
                            preview: innerHTML.substring(0, 100)
                        };
                    });
                    
                    return {
                        totalImages: allImages.length,
                        templateImages: templateImages,
                        uiImages: uiImages,
                        containerCheck: containerCheck
                    };
                }
            """)
            
            print(f"\n📊 RESULTS:")
            print(f"   Total Images Found: {result['totalImages']}")
            print(f"   Template Images: {len(result['templateImages'])}")
            print(f"   UI Images: {len(result['uiImages'])}")
            
            if result['templateImages']:
                print(f"\n{'─'*100}")
                print(f"🖼️  TEMPLATE IMAGES (Likely inserted logos):")
                print(f"{'─'*100}")
                
                for img in result['templateImages']:
                    in_container = "✅ IN LOGO CONTAINER" if img['inLogoContainer'] else "📄 Other"
                    print(f"\n   Image #{img['index']}: {in_container}")
                    print(f"      Size: {img['width']}x{img['height']}px (display)")
                    print(f"      Natural: {img['naturalWidth']}x{img['naturalHeight']}px")
                    print(f"      Parent: <{img['parentTag']}> class=\"{img['parentClass']}...\"")
                    if img['containerUUID']:
                        print(f"      Container UUID: {img['containerUUID']}")
                    print(f"      Src: {img['src']}...")
            
            print(f"\n{'─'*100}")
            print(f"📦 LOGO CONTAINER CHECK:")
            print(f"{'─'*100}")
            
            for check in result['containerCheck']:
                if not check['found']:
                    print(f"   ❌ {check['id']}: Not found")
                elif check['hasImage']:
                    print(f"   ✅ {check['id']}: HAS IMAGE ({check['contentLength']} chars)")
                else:
                    print(f"   ⭕ {check['id']}: Empty ({check['contentLength']} chars)")
            
            # Save results
            output_file = f"all_images_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 Full analysis saved to: {output_file}")
            
            print(f"\n{'='*100}")
            print(f"✅ IMAGE ANALYSIS COMPLETE")
            print(f"{'='*100}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
