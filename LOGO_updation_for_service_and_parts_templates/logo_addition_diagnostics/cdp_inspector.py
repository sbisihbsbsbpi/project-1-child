#!/usr/bin/env python3
"""
CDP Inspector - Direct Browser Tab Investigation
=================================================

This script connects to the existing browser via CDP and inspects open tabs
to understand why logo validation didn't run for "Customer Pay Closed" template.

Usage:
    python3 cdp_inspector.py
"""

import asyncio
import sys
import os
import json
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def inspect_open_tabs(cdp_url: str = "http://localhost:9223"):
    """Connect to browser and inspect all open tabs"""
    
    print("=" * 100)
    print("🔍 CDP INSPECTOR - Investigating Open Browser Tabs")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        try:
            # Connect to existing browser
            print(f"\n🌐 Connecting to browser at {cdp_url}...")
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            
            # Get all contexts
            contexts = browser.contexts
            print(f"✅ Connected! Found {len(contexts)} browser context(s)")
            
            if not contexts:
                print("❌ No browser contexts found - browser might be closed")
                return
            
            context = contexts[0]
            pages = context.pages
            print(f"📑 Found {len(pages)} open tab(s)")
            
            # Inspect each page
            for idx, page in enumerate(pages, 1):
                print(f"\n{'=' * 80}")
                print(f"📄 TAB {idx}: {page.url[:100]}...")
                print(f"{'=' * 80}")
                
                # Get page title
                title = await page.title()
                print(f"📌 Title: {title}")
                
                # Check if this is a template editor page
                if "template-editor" in page.url or "templates" in page.url:
                    print(f"✅ This is a TEMPLATE EDITOR page")
                    
                    # Extract template name from page
                    template_info = await page.evaluate("""
                        () => {
                            // Try to find template name from breadcrumb or title
                            const breadcrumb = document.querySelector('[data-testid="breadcrumb"]');
                            const templateName = breadcrumb ? breadcrumb.textContent : document.title;
                            
                            return {
                                templateName: templateName,
                                url: window.location.href
                            };
                        }
                    """)
                    
                    print(f"📝 Template: {template_info.get('templateName', 'Unknown')}")
                    
                    # Run logo detection on this page
                    print(f"\n🔍 Running logo detection analysis...")
                    
                    detection_info = await page.evaluate("""
                        () => {
                            const info = {
                                detectedLogos: [],
                                learnedContainers: [],
                                allImages: [],
                                trulyDynamicResults: null
                            };
                            
                            // Check for learned logo markers
                            const learned = document.querySelectorAll('[data-learned-logo]');
                            info.learnedContainers = Array.from(learned).map((el, idx) => {
                                const img = el.querySelector('img');
                                return {
                                    index: idx + 1,
                                    marker: el.getAttribute('data-learned-logo'),
                                    hasImage: img !== null,
                                    imageSrc: img ? img.src : null,
                                    imageFilename: img && img.src ? img.src.split('/').pop() : null,
                                    outline: el.style.outline,
                                    isGreenBorder: el.style.outline.includes('lime') || el.style.outline.includes('green'),
                                    isRedBorder: el.style.outline.includes('red'),
                                    isPinkBorder: el.style.outline.includes('pink') || el.style.outline.includes('hotpink')
                                };
                            });
                            
                            // Get ALL images on the page
                            const allImgs = document.querySelectorAll('img');
                            info.allImages = Array.from(allImgs).map((img, idx) => {
                                const rect = img.getBoundingClientRect();
                                return {
                                    index: idx + 1,
                                    src: img.src ? img.src.substring(0, 100) : null,
                                    filename: img.src ? img.src.split('/').pop() : null,
                                    alt: img.alt,
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height),
                                    visible: rect.width > 0 && rect.height > 0
                                };
                            });
                            
                            return info;
                        }
                    """)
                    
                    # Print detection results
                    print(f"\n📊 DETECTION RESULTS:")
                    print(f"   • Learned containers: {len(detection_info['learnedContainers'])}")
                    print(f"   • Total images: {len(detection_info['allImages'])}")
                    
                    if detection_info['learnedContainers']:
                        print(f"\n🎨 LEARNED CONTAINERS (with borders):")
                        for container in detection_info['learnedContainers']:
                            border_type = "🟢 GREEN" if container['isGreenBorder'] else "🔴 RED" if container['isRedBorder'] else "🩷 PINK" if container['isPinkBorder'] else "⚪ OTHER"
                            print(f"   {border_type} Container #{container['index']}: {container['marker']}")
                            print(f"      - Has image: {container['hasImage']}")
                            if container['hasImage']:
                                print(f"      - Filename: {container['imageFilename']}")
                                print(f"      - Src: {container['imageSrc'][:80]}...")
                    
                    print(f"\n🖼️  ALL IMAGES ON PAGE (first 10):")
                    for img in detection_info['allImages'][:10]:
                        if img['visible'] and img['width'] > 30:
                            print(f"   Image #{img['index']}: {img['filename']}")
                            print(f"      - Size: {img['width']}x{img['height']}px")
                            print(f"      - Alt: {img['alt'][:50] if img['alt'] else 'N/A'}")

                    # Now check if detected logos can be validated against media library
                    if detection_info['learnedContainers']:
                        green_containers = [c for c in detection_info['learnedContainers'] if c['isGreenBorder']]
                        if green_containers:
                            print(f"\n🔍 VALIDATION CHECK:")
                            print(f"   Attempting to validate {len(green_containers)} green-bordered logo(s) against media library...")

                            # Try to get the media library (simulate what the script does)
                            try:
                                # This would open the Change Image popup
                                print(f"   ℹ️  Note: Filenames detected:")
                                for container in green_containers:
                                    filename = container['imageFilename']
                                    if filename:
                                        # Check if it's a query string URL
                                        if '?' in filename:
                                            clean_filename = filename.split('?')[0]
                                            print(f"      • {clean_filename} (has query params)")
                                        else:
                                            print(f"      • {filename}")
                
                else:
                    print(f"ℹ️  Not a template editor page")
            
            print(f"\n{'=' * 100}")
            print(f"✅ Inspection complete!")
            print(f"{'=' * 100}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(inspect_open_tabs())
