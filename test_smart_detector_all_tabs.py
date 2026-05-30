#!/usr/bin/env python3
"""
Test Smart Detector on All Open Template Tabs
Verifies the detection logic works across all templates
"""

import asyncio
from playwright.async_api import async_playwright
from smart_logo_detector import SmartLogoDetector
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def test_all_tabs():
    print("=" * 80)
    print("🧪 TESTING SMART DETECTOR ON ALL TEMPLATE TABS")
    print("=" * 80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find all template tabs
    template_pages = []
    for page in context.pages:
        if 'templates/edit' in page.url and 'templates/list' not in page.url:
            title = await page.title()
            template_pages.append({
                'page': page,
                'url': page.url,
                'title': title
            })
    
    print(f"Found {len(template_pages)} template tabs")
    print()
    
    # Test detector on each
    detector = SmartLogoDetector()
    
    total_logos_found = 0
    old_logo_count = 0
    new_logo_count = 0
    
    for idx, template_info in enumerate(template_pages, 1):
        page = template_info['page']
        title = template_info['title']
        
        print(f"[{idx}/{len(template_pages)}] Testing: {title[:60]}")
        
        results = await detector.detect_logos(page)
        
        if results['detected_logos']:
            total_logos_found += len(results['detected_logos'])
            
            for logo in results['detected_logos']:
                media_id = logo.get('mediaId', 'Unknown')
                
                # Check if it's old or new logo
                if media_id == '6a0c6722864813539e4da7ae':
                    old_logo_count += 1
                    print(f"  ✅ FOUND OLD LOGO (Nucar): {logo['width']}x{logo['height']} at {logo['position']['location']}")
                    print(f"     Confidence: {logo['confidence']}% | Method: {logo['detection_method']}")
                elif media_id == '6a19132b6697f36de6236fb1':
                    new_logo_count += 1
                    print(f"  ✅ FOUND NEW LOGO (Tilton): {logo['width']}x{logo['height']} at {logo['position']['location']}")
                    print(f"     Confidence: {logo['confidence']}% | Method: {logo['detection_method']}")
                else:
                    print(f"  🔍 Found logo: {logo['width']}x{logo['height']} at {logo['position']['location']}")
                    print(f"     Media ID: {media_id}")
                    print(f"     Confidence: {logo['confidence']}% | Method: {logo['detection_method']}")
        else:
            print(f"  ⚪ No logos detected")
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 DETECTION SUMMARY")
    print("=" * 80)
    print(f"Templates analyzed: {len(template_pages)}")
    print(f"Total logos detected: {total_logos_found}")
    print(f"Old logos (Nucar): {old_logo_count}")
    print(f"New logos (Tilton): {new_logo_count}")
    print(f"Other logos: {total_logos_found - old_logo_count - new_logo_count}")
    print()
    
    if old_logo_count > 0:
        print("✅ SUCCESS: Smart detector can identify old logos for replacement!")
    else:
        print("⚠️  No old logos found - they may have already been replaced")
    
    print()
    
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_all_tabs())
