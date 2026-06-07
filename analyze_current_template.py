#!/usr/bin/env python3
"""
Analyze the current template in the browser
Learn DOM structure for new dealership
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def analyze_template():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        if not context.pages:
            print("❌ No pages found")
            return
        
        page = context.pages[0]
        
        # Get current URL and template info
        current_url = page.url
        print("=" * 100)
        print("🔍 ANALYZING CURRENT TEMPLATE")
        print("=" * 100)
        print(f"📍 URL: {current_url}")
        print()
        
        # Extract template ID from URL
        if 'templates/edit/' in current_url:
            template_id = current_url.split('templates/edit/')[-1].split('?')[0]
            print(f"📝 Template ID: {template_id}")
        
        print()
        print("=" * 100)
        print("📊 DOM STRUCTURE ANALYSIS")
        print("=" * 100)
        
        result = await page.evaluate("""
            () => {
                const analysis = {
                    allTables: [],
                    logoRelatedElements: [],
                    imageElements: [],
                    textTemplates: [],
                    dynamicLinks: []
                };
                
                // Analyze ALL tables
                const tables = Array.from(document.querySelectorAll('table'));
                analysis.allTables = tables.map((table, idx) => {
                    const firstRow = table.querySelector('tr');
                    const cells = firstRow ? Array.from(firstRow.querySelectorAll('td')) : [];
                    const rect = table.getBoundingClientRect();
                    
                    return {
                        index: idx,
                        columns: cells.length,
                        position: {
                            top: Math.round(rect.top + window.scrollY),
                            left: Math.round(rect.left)
                        },
                        size: {
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        hasImages: table.querySelector('img') !== null,
                        hasTextTemplate: table.querySelector('.TEXT_TEMPLATE') !== null,
                        hasImageComponent: table.querySelector('[class*="Image_imageComponent"]') !== null,
                        hasDynamicLinks: table.querySelector('.dynamic_tag_link') !== null,
                        textContent: table.textContent.substring(0, 100)
                    };
                });
                
                // Find all image elements
                const images = Array.from(document.querySelectorAll('img'));
                analysis.imageElements = images.map((img, idx) => {
                    const rect = img.getBoundingClientRect();
                    const parent = img.parentElement;
                    
                    return {
                        index: idx,
                        src: img.src.substring(0, 80) + '...',
                        alt: img.alt,
                        size: {
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        position: {
                            top: Math.round(rect.top + window.scrollY)
                        },
                        parentClass: parent ? parent.className : null,
                        isVisible: rect.width > 0 && rect.height > 0
                    };
                }).filter(img => img.isVisible && img.size.width > 50); // Filter small icons
                
                // Find TEXT_TEMPLATE elements
                const textTemplates = Array.from(document.querySelectorAll('.TEXT_TEMPLATE[contenteditable="true"]'));
                analysis.textTemplates = textTemplates.map((el, idx) => {
                    const rect = el.getBoundingClientRect();
                    const parent = el.parentElement;
                    const hasImage = el.querySelector('img') !== null;
                    
                    return {
                        index: idx,
                        id: el.id,
                        isEmpty: !hasImage && el.textContent.trim().length === 0,
                        hasImage: hasImage,
                        position: {
                            top: Math.round(rect.top + window.scrollY)
                        },
                        parentClass: parent ? parent.className.substring(0, 50) : null
                    };
                });
                
                // Find dynamic tag links
                const dynamicLinks = Array.from(document.querySelectorAll('.dynamic_tag_link'));
                analysis.dynamicLinks = dynamicLinks.map((link, idx) => ({
                    index: idx,
                    text: link.textContent.trim(),
                    href: link.getAttribute('href')
                }));
                
                return analysis;
            }
        """)
        
        # Print analysis
        print(f"\n📋 TABLES FOUND: {len(result['allTables'])}")
        print("-" * 100)
        
        # Group tables by column count
        tables_by_cols = {}
        for table in result['allTables']:
            cols = table['columns']
            if cols not in tables_by_cols:
                tables_by_cols[cols] = []
            tables_by_cols[cols].append(table)
        
        for cols in sorted(tables_by_cols.keys()):
            tables = tables_by_cols[cols]
            print(f"\n{cols}-COLUMN TABLES ({len(tables)} found):")
            for table in tables[:5]:  # Show first 5 of each
                print(f"  Table {table['index']}: pos={table['position']['top']}px, "
                      f"hasImages={table['hasImages']}, hasTextTemplate={table['hasTextTemplate']}, "
                      f"hasDynamicLinks={table['hasDynamicLinks']}")
                if table['textContent']:
                    preview = table['textContent'].replace('\n', ' ')[:60]
                    print(f"    Text: {preview}...")
        
        print(f"\n\n📷 IMAGES FOUND: {len(result['imageElements'])}")
        print("-" * 100)
        for img in result['imageElements'][:10]:  # Show first 10
            print(f"  Image {img['index']}: {img['size']['width']}x{img['size']['height']}px at {img['position']['top']}px")
            print(f"    Alt: {img['alt']}")
            print(f"    Src: {img['src']}")
        
        print(f"\n\n📝 TEXT_TEMPLATES FOUND: {len(result['textTemplates'])}")
        print("-" * 100)
        empty_templates = [t for t in result['textTemplates'] if t['isEmpty']]
        with_images = [t for t in result['textTemplates'] if t['hasImage']]
        
        print(f"  Empty: {len(empty_templates)}")
        print(f"  With Images: {len(with_images)}")
        
        for t in empty_templates[:5]:
            print(f"    Empty template: ID={t['id']}, pos={t['position']['top']}px")
        
        for t in with_images[:5]:
            print(f"    Template with image: ID={t['id']}, pos={t['position']['top']}px")
        
        print(f"\n\n🔗 DYNAMIC LINKS: {len(result['dynamicLinks'])}")
        print("-" * 100)
        for link in result['dynamicLinks']:
            print(f"  {link['text']}: {link['href']}")
        
        # Save full analysis to file
        timestamp = asyncio.get_event_loop().time()
        filename = f"template_analysis_{int(timestamp)}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n\n💾 Full analysis saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(analyze_template())
