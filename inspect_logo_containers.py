#!/usr/bin/env python3
"""
Inspect Logo Containers in Service + Parts Templates
====================================================

Opens each template and inspects the exact logo container structure:
- Logo 1 LEFT/RIGHT containers
- Logo 2 LEFT/RIGHT containers
- Header LEFT/RIGHT containers
- Container positions and types
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_template_containers(template_id, template_name):
    """Inspect logo containers in a single template"""
    
    async with async_playwright() as p:
        # Connect to existing browser
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        page = await context.new_page()
        
        # Navigate to template
        url = f'https://preprodapp.tekioncloud.com/templates/edit/{template_id}'
        await page.goto(url)
        await asyncio.sleep(10)  # Wait for template to load
        
        # Inspect containers
        result = await page.evaluate("""
            () => {
                // Find all logo containers
                const logo1Left = document.querySelector('[data-test="logo1-left-container"]');
                const logo1Right = document.querySelector('[data-test="logo1-right-container"]');
                const logo2Left = document.querySelector('[data-test="logo2-left-container"]');
                const logo2Right = document.querySelector('[data-test="logo2-right-container"]');
                const headerLeft = document.querySelector('[data-test="header-left-container"]');
                const headerRight = document.querySelector('[data-test="header-right-container"]');
                
                // Alternative: search by class patterns
                const allContainers = document.querySelectorAll('[class*="logo"]');
                
                return {
                    logo_1_left: !!logo1Left,
                    logo_1_right: !!logo1Right,
                    logo_2_left: !!logo2Left,
                    logo_2_right: !!logo2Right,
                    header_left: !!headerLeft,
                    header_right: !!headerRight,
                    total_containers: [logo1Left, logo1Right, logo2Left, logo2Right, headerLeft, headerRight].filter(x => x).length,
                    all_logo_elements: allContainers.length
                };
            }
        """)
        
        await page.close()
        
        return {
            'name': template_name,
            'id': template_id,
            'containers': result
        }

async def main():
    # Load metadata
    with open('template_metadata.json', 'r') as f:
        data = json.load(f)
    
    templates = data.get('templates', [])
    
    print('🔍 INSPECTING LOGO CONTAINERS IN ALL TEMPLATES')
    print('=' * 100)
    print()
    
    results = []
    
    for i, template in enumerate(templates[:5], 1):  # Test with first 5
        name = template.get('name')
        template_id = template.get('id')
        
        print(f'[{i}/{len(templates)}] Inspecting: {name}...')
        
        try:
            result = await inspect_template_containers(template_id, name)
            results.append(result)
            
            # Print result
            c = result['containers']
            print(f'   Logo 1: L={c["logo_1_left"]} R={c["logo_1_right"]}')
            print(f'   Logo 2: L={c["logo_2_left"]} R={c["logo_2_right"]}')
            print(f'   Header: L={c["header_left"]} R={c["header_right"]}')
            print(f'   Total: {c["total_containers"]} containers')
            print()
            
        except Exception as e:
            print(f'   ❌ Error: {e}')
            print()
    
    # Save results
    with open('logo_container_inspection.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'✅ Results saved to: logo_container_inspection.json')

if __name__ == '__main__':
    asyncio.run(main())
