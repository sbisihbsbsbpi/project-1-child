#!/usr/bin/env python3
"""
Inspect Consumer Scheduling OTP DOM for logo markers and images

This script examines the actual DOM structure to understand:
1. Whether data-learned-logo attributes exist
2. What images are present
3. Whether the API says there's a logo (thumbnail.mediaId)
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def inspect_template():
    """Inspect the Consumer Scheduling OTP template DOM"""
    
    TEMPLATE_ID = "667f0befd4964026ee7b6ea8"
    
    print("="*100)
    print("🔍 Consumer Scheduling OTP - DOM Inspection")
    print("="*100)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        page = await context.new_page()
        
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{TEMPLATE_ID}"
        print(f"Loading: {edit_url}")
        await page.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
        await asyncio.sleep(10)
        print("✅ Template loaded\n")
        
        # Run comprehensive DOM inspection
        result = await page.evaluate("""
            () => {
                const report = {
                    dataLearnedLogo: [],
                    allImages: [],
                    sortableItems: 0,
                    tables: 0,
                    logoMediaIds: []
                };
                
                // 1. Check for data-learned-logo attributes
                const learned = document.querySelectorAll('[data-learned-logo]');
                report.dataLearnedLogo = Array.from(learned).map((el, idx) => ({
                    index: idx + 1,
                    marker: el.getAttribute('data-learned-logo'),
                    tagName: el.tagName,
                    hasImage: el.querySelector('img') !== null,
                    innerHTML: el.innerHTML.substring(0, 200)
                }));
                
                // 2. Get all images
                const allImgs = document.querySelectorAll('img');
                report.allImages = Array.from(allImgs).map((img, idx) => {
                    const rect = img.getBoundingClientRect();
                    const src = img.src || '';
                    
                    // Check if parent has data-learned-logo
                    let parent = img.parentElement;
                    let hasLearnedMarker = false;
                    let markerValue = null;
                    let depth = 0;
                    while (parent && depth < 5) {
                        if (parent.hasAttribute('data-learned-logo')) {
                            hasLearnedMarker = true;
                            markerValue = parent.getAttribute('data-learned-logo');
                            break;
                        }
                        parent = parent.parentElement;
                        depth++;
                    }
                    
                    // Check if it's a media URL
                    const isMediaUrl = src.includes('amazonaws.com') && src.includes('media_');
                    const mediaId = isMediaUrl ? src.split('/').pop().split('.')[0] : null;
                    
                    return {
                        index: idx + 1,
                        src: src.substring(0, 100),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        alt: img.alt || '',
                        hasLearnedMarker: hasLearnedMarker,
                        learnedMarker: markerValue,
                        isMediaUrl: isMediaUrl,
                        mediaId: mediaId,
                        isIcon: src.includes('icon-') || src.includes('favicon'),
                        isTekionLogo: src.includes('tekion-logo')
                    };
                });
                
                // 3. Count sortable items and tables
                report.sortableItems = document.querySelectorAll('[class*="SortableItem"]').length;
                report.tables = document.querySelectorAll('table').length;
                
                // 4. Extract any media IDs from the page
                const mediaImages = report.allImages.filter(img => img.isMediaUrl && !img.isIcon);
                report.logoMediaIds = mediaImages.map(img => img.mediaId).filter(id => id);
                
                return report;
            }
        """)
        
        # Print results
        print("=" * 100)
        print("📊 INSPECTION RESULTS")
        print("=" * 100)
        print()
        
        print(f"📐 Template Structure:")
        print(f"   • Sortable items: {result['sortableItems']}")
        print(f"   • Tables: {result['tables']}")
        print()
        
        print(f"🏷️  data-learned-logo Attributes Found: {len(result['dataLearnedLogo'])}")
        if result['dataLearnedLogo']:
            for item in result['dataLearnedLogo']:
                print(f"   • Marker '{item['marker']}': {item['tagName']}, hasImage={item['hasImage']}")
        else:
            print("   ❌ No data-learned-logo attributes found in template!")
        print()
        
        print(f"🖼️  Images Found: {result['allImages']}")
        
        # Filter for potential dealer logos
        potential_logos = [
            img for img in result['allImages']
            if not img['isIcon'] 
            and not img['isTekionLogo']
            and img['width'] > 30
            and img['height'] > 15
        ]
        
        print(f"   • Potential logos (non-icons, reasonable size): {len(potential_logos)}")
        for logo in potential_logos:
            print(f"\n   Logo #{logo['index']}:")
            print(f"      • Size: {logo['width']}x{logo['height']}px")
            print(f"      • Media URL: {logo['isMediaUrl']}")
            if logo['mediaId']:
                print(f"      • Media ID: {logo['mediaId']}")
            print(f"      • Has learned marker: {logo['hasLearnedMarker']}")
            if logo['learnedMarker']:
                print(f"      • Marker value: {logo['learnedMarker']}")
            print(f"      • Source: {logo['src']}")
        
        print()
        print(f"🆔 Media IDs Found: {len(result['logoMediaIds'])}")
        if result['logoMediaIds']:
            for mid in result['logoMediaIds']:
                print(f"   • {mid}")
        print()
        
        # Check expected media ID
        expected_id = "6a1920d16697f36de6236fc9"
        if expected_id in result['logoMediaIds']:
            print(f"✅ Expected mediaId ({expected_id}) FOUND in template!")
        else:
            print(f"❌ Expected mediaId ({expected_id}) NOT FOUND")
            print(f"   Template may have been updated or logo removed")
        
        await page.close()


if __name__ == '__main__':
    asyncio.run(inspect_template())
