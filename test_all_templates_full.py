#!/usr/bin/env python3
"""
Full automation test - Process all templates
"""

import asyncio
import sys
sys.path.insert(0, 'logo_addition_diagnostics')
from temp_logo_adding_FINAL import TempLogoAdditionFinalService
from playwright.async_api import async_playwright

async def main():
    print('=' * 100)
    print('🚀 RUNNING FULL AUTOMATION - All Templates')
    print('=' * 100)
    print()
    
    service = TempLogoAdditionFinalService()
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        
        # Get or create page
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate to templates list
        print('📍 Navigating to templates list...')
        await page.goto('https://preprodapp.tekioncloud.com/templates/list', 
                       wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)
        
        # Fetch templates via API
        print('📚 Fetching templates via API...')
        templates_response = await page.evaluate("""
            async () => {
                try {
                    const response = await fetch('https://preprodapp.tekioncloud.com/templatestore/api/v1/templates', {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        },
                        credentials: 'include'
                    });
                    
                    if (!response.ok) {
                        return { success: false, error: 'HTTP ' + response.status };
                    }
                    
                    const data = await response.json();
                    return { success: true, data: data };
                } catch (err) {
                    return { success: false, error: err.message };
                }
            }
        """)
        
        templates = []
        
        if not templates_response['success']:
            print(f"❌ API call failed: {templates_response.get('error')}")
            print()
            print('Using test template instead...')
            
            templates = [{
                'id': '6a0dc5fb62ae8d1a351df064',
                'name': 'Test Template - Service',
                'departments': ['Service'],
                'dealershipName': 'Alfa Romeo of Cincinnati'
            }]
        else:
            api_data = templates_response.get('data', {})
            all_templates = api_data.get('templates', []) or api_data.get('data', [])
            
            print(f'✅ Found {len(all_templates)} total templates')
            
            # Filter for Service/Parts (first 10)
            for t in all_templates[:10]:
                dept = t.get('department', '') or t.get('departments', [''])[0]
                if 'Service' in str(dept) or 'Parts' in str(dept):
                    templates.append({
                        'id': t.get('id') or t.get('_id'),
                        'name': t.get('name', 'Unknown'),
                        'departments': [dept] if isinstance(dept, str) else dept,
                        'dealershipName': t.get('dealershipName', 'Unknown Dealership')
                    })
            
            print(f'✅ Filtered to {len(templates)} Service/Parts templates')
        
        print()
        print('=' * 100)
        print(f'Processing {len(templates)} template(s)...')
        print('=' * 100)
        print()
        
        # Process each template
        for idx, template in enumerate(templates, 1):
            print()
            print('=' * 100)
            print(f'TEMPLATE {idx}/{len(templates)}: {template["name"]}')
            print('=' * 100)
            print(f'ID: {template["id"]}')
            print(f'Dealership: {template.get("dealershipName", "Unknown")}')
            print(f'Departments: {template.get("departments", [])}')
            print()
            
            # Open template in new tab
            template_page = await context.new_page()
            
            try:
                await template_page.goto(
                    f'https://preprodapp.tekioncloud.com/templates/edit/{template["id"]}',
                    wait_until='domcontentloaded',
                    timeout=30000
                )
                await asyncio.sleep(5)
                
                # Run detection
                print('🔍 Running detection and validation...')
                detection_result = await service._detect_logos(template_page)
                
                truly_dynamic = detection_result.get('trulyDynamic', {})
                detected_logos = truly_dynamic.get('detectedLogos', [])
                all_detected_count = detection_result.get('allDetectedLogosCount', 0)
                
                print(f'   Found {all_detected_count} real logo(s)')
                
                if detected_logos:
                    for logo_idx, logo in enumerate(detected_logos, 1):
                        filename = logo.get('imageFilename', 'N/A')
                        print(f'   Logo {logo_idx}: {filename}')
                else:
                    print('   ℹ️  No logos detected')
                
                print()
                print(f'✅ Template {idx} processed - Tab kept open')
                
            except Exception as e:
                print(f'❌ Error: {e}')
                import traceback
                traceback.print_exc()
        
        print()
        print('=' * 100)
        print('✅ AUTOMATION COMPLETE!')
        print('=' * 100)
        print()
        print(f'🔍 {len(templates)} template tab(s) kept open in Chrome')
        print('💡 Review each tab to verify logo detection')
        print('=' * 100)

if __name__ == "__main__":
    asyncio.run(main())
