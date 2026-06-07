#!/usr/bin/env python3
"""
Analyze template using Tekion API
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def analyze_via_api():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        if not context.pages:
            print("❌ No pages found")
            return
        
        page = context.pages[0]
        
        # Get template ID from URL
        current_url = page.url
        template_id = None
        
        if 'templates/edit/' in current_url:
            template_id = current_url.split('templates/edit/')[-1].split('?')[0]
        
        if not template_id:
            print("❌ Not on a template edit page")
            print(f"Current URL: {current_url}")
            return
        
        print("=" * 100)
        print("📡 FETCHING TEMPLATE VIA API")
        print("=" * 100)
        print(f"Template ID: {template_id}")
        print()
        
        # Fetch template data via API
        template_data = await page.evaluate(f"""
            async () => {{
                try {{
                    const response = await fetch('/api/templates/{template_id}');
                    const data = await response.json();
                    return data;
                }} catch (error) {{
                    return {{ error: error.message }};
                }}
            }}
        """)
        
        if 'error' in template_data:
            print(f"❌ API Error: {template_data['error']}")
            return
        
        # Extract key information
        print("📋 TEMPLATE METADATA:")
        print("-" * 100)
        print(f"  Name: {template_data.get('name', 'Unknown')}")
        print(f"  Department: {template_data.get('department', 'Unknown')}")
        print(f"  Dealership ID: {template_data.get('dealershipId', 'Unknown')}")
        print(f"  Status: {template_data.get('status', 'Unknown')}")
        print(f"  Created: {template_data.get('createdAt', 'Unknown')}")
        print(f"  Updated: {template_data.get('updatedAt', 'Unknown')}")
        
        # Analyze template JSON structure
        template_json = template_data.get('templateJson', '{}')
        if isinstance(template_json, str):
            template_json = json.loads(template_json)
        
        print()
        print("🏗️  TEMPLATE STRUCTURE:")
        print("-" * 100)
        
        # Find all tables
        def find_elements(obj, element_type, path=""):
            elements = []
            if isinstance(obj, dict):
                if obj.get('type') == element_type:
                    elements.append({
                        'path': path,
                        'data': obj
                    })
                for key, value in obj.items():
                    elements.extend(find_elements(value, element_type, f"{path}.{key}"))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    elements.extend(find_elements(item, element_type, f"{path}[{i}]"))
            return elements
        
        # Find tables
        tables = find_elements(template_json, 'table')
        print(f"\n📊 TABLES: {len(tables)} found")
        
        for i, table in enumerate(tables[:10], 1):
            data = table['data']
            cols = len(data.get('columns', []))
            print(f"\n  Table {i}: {cols} columns")
            print(f"    Path: {table['path']}")
            
            # Analyze cells
            if 'cells' in data:
                cells = data['cells']
                print(f"    Cells: {len(cells)}")
                for cell_idx, cell in enumerate(cells[:5]):
                    if isinstance(cell, dict):
                        has_image = 'image' in str(cell) or 'Image' in str(cell.get('type', ''))
                        has_text = 'text' in str(cell).lower()
                        print(f"      Cell {cell_idx}: type={cell.get('type', 'unknown')}, hasImage={has_image}")
        
        # Find images
        images = find_elements(template_json, 'image')
        print(f"\n\n📷 IMAGES: {len(images)} found")
        for i, img in enumerate(images[:10], 1):
            data = img['data']
            print(f"  Image {i}:")
            print(f"    Media ID: {data.get('mediaId', 'none')}")
            print(f"    Width: {data.get('width', 'auto')}")
            print(f"    Alt: {data.get('alt', 'none')}")
        
        # Save full template data
        filename = f"template_api_data_{template_id}.json"
        with open(filename, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        print(f"\n\n💾 Full template data saved to: {filename}")
        
        return template_data

if __name__ == "__main__":
    asyncio.run(analyze_via_api())
