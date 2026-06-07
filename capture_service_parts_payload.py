#!/usr/bin/env python3
"""
Capture Service + Parts API payload and response
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def capture_payload():
    print('🔍 Capturing Service + Parts API Payload')
    print('=' * 80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    pages = context.pages
    
    if pages:
        page = pages[0]
    else:
        page = await context.new_page()
    
    api_data = []
    service_parts_found = False
    
    async def handle_request(request):
        nonlocal service_parts_found
        if '/u/search' in request.url and request.post_data:
            try:
                body = json.loads(request.post_data)
                
                # Check for Service + Parts
                filters = body.get('filters', [])
                for f in filters:
                    if f.get('field') == 'departments':
                        depts = f.get('values', [])
                        if 'SERVICE' in depts and 'PARTS' in depts:
                            service_parts_found = True
                            print()
                            print('🎯 FOUND SERVICE + PARTS REQUEST!')
                            print('=' * 80)
                            print()
                            print('📤 REQUEST PAYLOAD:')
                            print(json.dumps(body, indent=2))
                            print()
                            
                            api_data.append({
                                'type': 'request',
                                'timestamp': datetime.now().isoformat(),
                                'body': body
                            })
            except:
                pass
    
    async def handle_response(response):
        if service_parts_found and '/u/search' in response.url:
            try:
                data = await response.json()
                count = data.get('data', {}).get('count')
                hits = data.get('data', {}).get('hits', [])
                
                print('📥 RESPONSE:')
                print(f'   Status: {response.status}')
                print(f'   data.count: {count}')
                print(f'   Templates returned: {len(hits)}')
                
                if hits:
                    print()
                    print('   Template IDs:')
                    for h in hits[:10]:
                        print(f'      - {h.get("id")} | {h.get("name")}')
                    if len(hits) > 10:
                        print(f'      ... and {len(hits) - 10} more')
                
                print()
                print('=' * 80)
                
                api_data.append({
                    'type': 'response',
                    'timestamp': datetime.now().isoformat(),
                    'status': response.status,
                    'count': count,
                    'template_count': len(hits)
                })
            except Exception as e:
                print(f'Error parsing response: {e}')
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print('✅ Monitoring started')
    print()
    print('Step 1: Navigating to templates list...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded', timeout=30000)
    print('✅ Page loaded')
    await asyncio.sleep(3)
    
    print()
    print('Step 2: Applying Service + Parts filter...')
    
    try:
        # Click dropdown
        print('   - Opening dropdown...')
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)
        
        # Uncheck all
        print('   - Unchecking all departments...')
        for idx in range(3):  # Sales, Service, Parts
            try:
                checkbox = await page.query_selector(f'.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type({idx+1}) input')
                if checkbox:
                    is_checked = await checkbox.is_checked()
                    if is_checked:
                        await checkbox.click()
                        await asyncio.sleep(0.5)
            except:
                pass
        
        # Check Service (index 1)
        print('   - Checking Service...')
        service_checkbox = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(2) input')
        if service_checkbox:
            await service_checkbox.click()
            await asyncio.sleep(1)
            print('   ✅ Service checked')
        
        # Check Parts (index 2)
        print('   - Checking Parts...')
        parts_checkbox = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(3) input')
        if parts_checkbox:
            await parts_checkbox.click()
            await asyncio.sleep(1)
            print('   ✅ Parts checked')
        
        # Close dropdown
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(2)
        
        print()
        print('Waiting for API calls (5 seconds)...')
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f'❌ Error: {e}')
    
    if api_data:
        filename = f'service_parts_payload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(api_data, f, indent=2)
        print()
        print(f'✅ Saved to: {filename}')
    else:
        print()
        print('❌ No Service + Parts API calls captured')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(capture_payload())
