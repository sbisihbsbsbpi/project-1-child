#!/usr/bin/env python3
"""
Capture Service + Parts API by refreshing page and applying filters from scratch
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def capture_fresh():
    print('🔍 Fresh Service + Parts API Capture')
    print('=' * 80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Close existing pages and create fresh one
    for p in context.pages:
        try:
            await p.close()
        except:
            pass
    
    page = await context.new_page()
    
    api_calls = []
    filter_api_received = asyncio.Event()
    
    async def handle_request(request):
        if '/u/search' in request.url and request.post_data:
            try:
                body = json.loads(request.post_data)
                
                depts = None
                purpose = None
                filters = body.get('filters', [])
                for f in filters:
                    if f.get('field') == 'departments':
                        depts = f.get('values', [])
                    if f.get('field') == 'purposeSubType':
                        purpose = f.get('values', [])
                
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                # Check if this is Service + Parts
                is_service_parts = depts and 'SERVICE' in depts and 'PARTS' in depts
                
                if is_service_parts:
                    print()
                    print('🎯 SERVICE + PARTS REQUEST DETECTED!')
                    print('─' * 80)
                
                print(f'[{timestamp}] → Depts: {depts} | Purpose: {purpose}', end='')
                if is_service_parts:
                    print(' ← TARGET!')
                else:
                    print()
                
                api_calls.append({
                    'type': 'request',
                    'timestamp': timestamp,
                    'departments': depts,
                    'purpose': purpose,
                    'body': body,
                    'is_service_parts': is_service_parts
                })
            except:
                pass
    
    async def handle_response(response):
        if '/u/search' in response.url:
            try:
                data = await response.json()
                count = data.get('data', {}).get('count')
                hits = data.get('data', {}).get('hits', [])
                
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                # Check if this response is for Service + Parts request
                is_response_to_sp = False
                for call in reversed(api_calls):
                    if call.get('type') == 'request' and call.get('is_service_parts'):
                        is_response_to_sp = True
                        break
                    if call.get('type') == 'response':
                        break
                
                indicator = '✅' if count and count > 0 else '  '
                print(f'[{timestamp}] {indicator} ← count={count}, templates={len(hits)}', end='')
                
                if is_response_to_sp:
                    print(' ← SERVICE + PARTS RESPONSE!')
                    print('=' * 80)
                    filter_api_received.set()
                else:
                    print()
                
                api_calls.append({
                    'type': 'response',
                    'timestamp': timestamp,
                    'count': count,
                    'template_count': len(hits),
                    'is_service_parts_response': is_response_to_sp,
                    'full_data': data if is_response_to_sp else None
                })
            except:
                pass
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print('Step 1: Loading fresh page...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded', timeout=30000)
    print('✅ Page loaded (Sales default)')
    
    # Wait for initial load APIs to complete
    print('Waiting for initial API calls to complete...')
    await asyncio.sleep(5)
    
    print()
    print('=' * 80)
    print('Step 2: Applying Service + Parts Filter')
    print('=' * 80)
    print()
    
    try:
        # Open dropdown
        print('Opening dropdown...')
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)

        # Department mapping (same as main script)
        dept_map = {'Sales': 0, 'Service': 1, 'Parts': 2}

        # Uncheck all first
        print('Unchecking all departments...')
        for dept_name in ['Sales', 'Service', 'Parts']:
            await page.evaluate(f"""
                () => {{
                    const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map[dept_name]}];
                    if (cb && cb.checked) cb.click();
                }}
            """)
            await asyncio.sleep(0.3)

        print('All unchecked')
        await asyncio.sleep(0.5)

        # Check Service
        print('Checking Service...')
        await page.evaluate(f"""
            () => {{
                const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map['Service']}];
                if (cb && !cb.checked) cb.click();
            }}
        """)
        await asyncio.sleep(0.3)

        # Check Parts
        print('Checking Parts...')
        await page.evaluate(f"""
            () => {{
                const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map['Parts']}];
                if (cb && !cb.checked) cb.click();
            }}
        """)
        await asyncio.sleep(0.3)

        # Close dropdown - this triggers the API
        print()
        print('Closing dropdown - this will trigger the API call...')
        await page.keyboard.press('Escape')
        await asyncio.sleep(1)

        # Wait for the Service + Parts API response
        print('Waiting for Service + Parts API response...')
        try:
            await asyncio.wait_for(filter_api_received.wait(), timeout=10.0)
            print('✅ Service + Parts API captured!')
        except asyncio.TimeoutError:
            print('⚠️  Timeout - API may not have been triggered')
            # Wait a bit more
            await asyncio.sleep(3)
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    print('=' * 80)
    print('📊 RESULTS')
    print('=' * 80)
    print()
    
    # Find and display Service + Parts data
    sp_request = None
    sp_response = None
    
    for call in api_calls:
        if call.get('is_service_parts'):
            sp_request = call
        if call.get('is_service_parts_response'):
            sp_response = call
    
    if sp_request and sp_response:
        print('🎯 SERVICE + PARTS API CALL CAPTURED!')
        print()
        print('REQUEST:')
        print(f'  Timestamp: {sp_request.get("timestamp")}')
        print(f'  Departments: {sp_request.get("departments")}')
        print(f'  Purpose: {sp_request.get("purpose")}')
        print()
        print('RESPONSE:')
        print(f'  Timestamp: {sp_response.get("timestamp")}')
        print(f'  Count: {sp_response.get("count")}')
        print(f'  Templates returned: {sp_response.get("template_count")}')
        print()
        print('─' * 80)
        print('FULL REQUEST PAYLOAD:')
        print(json.dumps(sp_request.get('body'), indent=2))
    else:
        print('❌ Service + Parts API call not captured')
        print(f'   Requests captured: {len([c for c in api_calls if c.get("type") == "request"])}')
        print(f'   Service + Parts requests: {len([c for c in api_calls if c.get("is_service_parts")])}')
    
    # Save
    filename = f'service_parts_fresh_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump({
            'api_calls': api_calls,
            'service_parts_request': sp_request,
            'service_parts_response': sp_response
        }, f, indent=2)
    
    print()
    print(f'✅ Saved to: {filename}')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(capture_fresh())
