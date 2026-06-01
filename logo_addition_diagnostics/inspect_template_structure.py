#!/usr/bin/env python3
"""
Template Page Structure Inspector
Shows EVERYTHING on the template edit page
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🔍 TEMPLATE PAGE STRUCTURE INSPECTOR")
    print("=" * 100)
    
    template_id = "667f0befd4964026ee7b6e46"  # RO Invoiced
    template_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            
            # Find tab
            pages = context.pages
            page = None
            for p in pages:
                if template_id in p.url:
                    page = p
                    break
            
            if not page:
                page = await context.new_page()
                await page.goto(template_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
            
            print(f"📄 Page: {page.url}\n")
            
            # Get comprehensive page structure
            structure = await page.evaluate("""
                () => {
                    const info = {
                        // All contenteditable elements
                        contenteditable_elements: [],
                        
                        // All elements with data-cell-identifier
                        cell_identifiers: [],
                        
                        // All TEXT_TEMPLATE elements
                        text_templates: [],
                        
                        // All iframes
                        iframes: [],
                        
                        // All elements containing "Logo" in attributes
                        logo_related: [],
                        
                        // Page structure
                        main_containers: []
                    };
                    
                    // 1. Contenteditable elements
                    document.querySelectorAll('[contenteditable="true"]').forEach((el, i) => {
                        const rect = el.getBoundingClientRect();
                        info.contenteditable_elements.push({
                            index: i + 1,
                            id: el.id,
                            className: el.className.substring(0, 80),
                            tagName: el.tagName,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: { width: rect.width, height: rect.height },
                            textContent: el.textContent.trim().substring(0, 50),
                            hasImages: el.querySelectorAll('img').length,
                            parentId: el.parentElement?.id,
                            parentClass: el.parentElement?.className.substring(0, 80)
                        });
                    });
                    
                    // 2. Elements with data-cell-identifier
                    document.querySelectorAll('[data-cell-identifier]').forEach((el, i) => {
                        const cellId = el.getAttribute('data-cell-identifier');
                        const rect = el.getBoundingClientRect();
                        info.cell_identifiers.push({
                            index: i + 1,
                            cellId: cellId,
                            id: el.id,
                            className: el.className.substring(0, 80),
                            visible: rect.width > 0 && rect.height > 0,
                            hasContentEditable: el.querySelector('[contenteditable="true"]') !== null,
                            textContent: el.textContent.trim().substring(0, 50)
                        });
                    });
                    
                    // 3. TEXT_TEMPLATE elements
                    document.querySelectorAll('.TEXT_TEMPLATE').forEach((el, i) => {
                        const rect = el.getBoundingClientRect();
                        info.text_templates.push({
                            index: i + 1,
                            id: el.id,
                            contentEditable: el.getAttribute('contenteditable'),
                            visible: rect.width > 0 && rect.height > 0,
                            rect: { width: rect.width, height: rect.height },
                            parentCellId: el.closest('[data-cell-identifier]')?.getAttribute('data-cell-identifier'),
                            hasImages: el.querySelectorAll('img').length,
                            textContent: el.textContent.trim().substring(0, 50)
                        });
                    });
                    
                    // 4. Iframes (template might be in iframe)
                    document.querySelectorAll('iframe').forEach((iframe, i) => {
                        const rect = iframe.getBoundingClientRect();
                        info.iframes.push({
                            index: i + 1,
                            id: iframe.id,
                            src: iframe.src?.substring(0, 100),
                            className: iframe.className,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: { width: rect.width, height: rect.height }
                        });
                    });
                    
                    // 5. Logo-related elements
                    document.querySelectorAll('*').forEach(el => {
                        const attrs = Array.from(el.attributes || []);
                        const hasLogo = attrs.some(attr => 
                            attr.value && attr.value.toString().toLowerCase().includes('logo')
                        );
                        
                        if (hasLogo) {
                            const rect = el.getBoundingClientRect();
                            info.logo_related.push({
                                tagName: el.tagName,
                                id: el.id,
                                className: el.className.substring(0, 80),
                                attributes: attrs.filter(a => a.value.toLowerCase().includes('logo')).map(a => ({
                                    name: a.name,
                                    value: a.value.substring(0, 100)
                                })),
                                visible: rect.width > 0 && rect.height > 0,
                                textContent: el.textContent.trim().substring(0, 50)
                            });
                        }
                    });
                    
                    // 6. Main containers
                    ['[class*="container"]', '[class*="editor"]', '[class*="template"]', '[role="main"]'].forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 200 && rect.height > 200) {
                                info.main_containers.push({
                                    selector: sel,
                                    id: el.id,
                                    className: el.className.substring(0, 100),
                                    rect: { width: rect.width, height: rect.height }
                                });
                            }
                        });
                    });
                    
                    return info;
                }
            """)
            
            # Print results
            print("=" * 100)
            print("📊 STRUCTURE ANALYSIS")
            print("=" * 100)
            
            print(f"\n1️⃣ CONTENTEDITABLE ELEMENTS ({len(structure['contenteditable_elements'])}):")
            for el in structure['contenteditable_elements'][:20]:
                visible = "👁️" if el['visible'] else "❌"
                has_img = f"🖼️ ({el['hasImages']})" if el['hasImages'] > 0 else ""
                print(f"   {el['index']}. {visible} {el['tagName']}.{el['className'][:40]} {has_img}")
                print(f"       ID: {el['id']}")
                print(f"       Parent: {el['parentClass'][:40]}")
                if el['textContent']:
                    print(f"       Text: {el['textContent']}")
            
            print(f"\n2️⃣ CELL IDENTIFIERS ({len(structure['cell_identifiers'])}):")
            for el in structure['cell_identifiers'][:30]:
                visible = "👁️" if el['visible'] else "❌"
                editable = "✏️" if el['hasContentEditable'] else ""
                print(f"   {el['index']}. {visible} {editable} {el['cellId']}")
                if el['textContent']:
                    print(f"       Text: {el['textContent']}")
            
            print(f"\n3️⃣ TEXT_TEMPLATE ELEMENTS ({len(structure['text_templates'])}):")
            for el in structure['text_templates'][:20]:
                visible = "👁️" if el['visible'] else "❌"
                has_img = f"🖼️ ({el['hasImages']})" if el['hasImages'] > 0 else ""
                print(f"   {el['index']}. {visible} {el['id']} {has_img}")
                print(f"       Cell: {el['parentCellId']}")
                print(f"       ContentEditable: {el['contentEditable']}")
                if el['textContent']:
                    print(f"       Text: {el['textContent']}")
            
            print(f"\n4️⃣ IFRAMES ({len(structure['iframes'])}):")
            for iframe in structure['iframes']:
                visible = "👁️" if iframe['visible'] else "❌"
                print(f"   {iframe['index']}. {visible} {iframe['id']}")
                print(f"       Src: {iframe['src']}")
                print(f"       Size: {iframe['rect']}")
            
            print(f"\n5️⃣ LOGO-RELATED ELEMENTS ({len(structure['logo_related'])}):")
            for el in structure['logo_related'][:30]:
                visible = "👁️" if el['visible'] else "❌"
                print(f"   {visible} {el['tagName']}.{el['className'][:40]}")
                for attr in el['attributes']:
                    print(f"       {attr['name']}: {attr['value']}")
            
            print(f"\n6️⃣ MAIN CONTAINERS ({len(structure['main_containers'])}):")
            for cont in structure['main_containers'][:10]:
                print(f"   {cont['selector']}")
                print(f"       ID: {cont['id']}")
                print(f"       Class: {cont['className']}")
                print(f"       Size: {cont['rect']}")
            
            # Save to JSON
            filename = f"template_structure_{template_id}.json"
            with open(filename, 'w') as f:
                json.dump(structure, f, indent=2)
            
            print(f"\n💾 Full structure saved to: {filename}")
            print("=" * 100)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
