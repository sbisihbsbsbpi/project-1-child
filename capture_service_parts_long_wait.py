#!/usr/bin/env python3
"""
Capture Service + Parts API with LONG WAIT (4+ minutes)
The API response is SLOW - must wait for real data to load
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def capture_with_long_wait():
    print('🔍 Service + Parts API Capture (LONG WAIT - 4+ minutes)')
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
    service_parts_requests = []
    
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
                    print('🎯 SERVICE + PARTS REQUEST!')
                    print('─' * 80)
                    print(f'[{timestamp}] Departments: {depts} | Purpose: {purpose}')
                    service_parts_requests.append(len(api_calls))
                else:
                    print(f'[{timestamp}] → Depts: {depts}', end='')
                    if is_service_parts:
                        print(' ← TARGET')
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
                if service_parts_requests:
                    last_sp_req_idx = service_parts_requests[-1]
                    # Count responses since that request
                    responses_since = sum(1 for c in api_calls[last_sp_req_idx:] if c.get('type') == 'response')
                    # If this is one of the next few responses, it might be for S+P
                    if responses_since < 10:
                        is_response_to_sp = True
                
                indicator = '✅' if count and count > 0 else '  '
                
                if is_response_to_sp and count and count > 0:
                    print()
                    print('💥 SERVICE + PARTS RESPONSE WITH DATA!')
                    print('=' * 80)
                    print(f'[{timestamp}] COUNT = {count}, TEMPLATES = {len(hits)}')
                    print('=' * 80)
                else:
                    print(f'[{timestamp}] {indicator} ← count={count}')
                
                api_calls.append({
                    'type': 'response',
                    'timestamp': timestamp,
                    'count': count,
                    'template_count': len(hits),
                    'is_service_parts_response': is_response_to_sp,
                    'full_data': data if (is_response_to_sp and count and count > 0) else None
                })
            except Exception as e:
                print(f'Error parsing response: {e}')
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print('Step 1: Loading fresh page...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded', timeout=30000)
    print('✅ Page loaded (Sales default)')
    
    # Wait for initial load APIs to complete
    print('Waiting for initial API calls to complete (10 seconds)...')
    await asyncio.sleep(10)
    
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
        
        # Department mapping
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
        
        await asyncio.sleep(1)
        
        # Check Service
        print('Checking Service...')
        await page.evaluate(f"""
            () => {{
                const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map['Service']}];
                if (cb && !cb.checked) cb.click();
            }}
        """)
        await asyncio.sleep(0.5)
        
        # Check Parts
        print('Checking Parts...')
        await page.evaluate(f"""
            () => {{
                const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map['Parts']}];
                if (cb && !cb.checked) cb.click();
            }}
        """)
        await asyncio.sleep(0.5)
        
        # Close dropdown - this triggers the API
        print()
        print('Closing dropdown - triggering API calls...')
        await page.keyboard.press('Escape')
        print('✅ Dropdown closed')
        
        print()
        print('⏳ WAITING FOR SERVICE + PARTS API RESPONSE...')
        print('   This may take 4+ minutes for the data to load!')
        print('   Monitoring all API responses...')
        print()
        
        # Wait 5 minutes to capture the slow-loading response
        for i in range(30):  # 30 x 10 seconds = 5 minutes
            await asyncio.sleep(10)
            elapsed = (i + 1) * 10
            print(f'   ... {elapsed} seconds elapsed ...')
            
            # Check if we got a Service + Parts response with count > 0
            sp_responses = [c for c in api_calls if c.get('is_service_parts_response') and c.get('count', 0) > 0]
            if sp_responses:
                print(f'   ✅ Got Service + Parts response with count > 0!')
                break
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    print('=' * 80)
    print('📊 FINAL RESULTS')
    print('=' * 80)
    print()
    
    # Find Service + Parts data
    sp_requests = [c for c in api_calls if c.get('is_service_parts')]
    sp_responses = [c for c in api_calls if c.get('is_service_parts_response')]
    
    print(f'Service + Parts requests captured: {len(sp_requests)}')
    print(f'Potential responses: {len(sp_responses)}')
    print()
    
    if sp_requests:
        for i, req in enumerate(sp_requests, 1):
            print(f'REQUEST {i}:')
            print(f'  Timestamp: {req.get("timestamp")}')
            print(f'  Departments: {req.get("departments")}')
            print(f'  Purpose: {req.get("purpose")}')
            
            # Find best matching response
            req_idx = api_calls.index(req)
            for j in range(req_idx + 1, len(api_calls)):
                resp = api_calls[j]
                if resp.get('type') == 'response':
                    count = resp.get('count')
                    if count is not None:
                        indicator = '✅' if count > 0 else '  '
                        print(f'  {indicator} RESPONSE: count={count}, templates={resp.get("template_count")}')
                        if count > 0:
                            print()
                            print('  📤 REQUEST PAYLOAD:')
                            print(json.dumps(req.get('body'), indent=4)[:1000])
                        break
            print()
    
    # Save
    filename = f'service_parts_long_wait_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump({
            'api_calls': api_calls,
            'service_parts_requests': [c for c in api_calls if c.get('is_service_parts')],
            'service_parts_responses': [c for c in api_calls if c.get('is_service_parts_response')]
        }, f, indent=2)
    
    print(f'✅ Saved to: {filename}')
    print()
    print(f'Total API calls: {len(api_calls)}')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(capture_with_long_wait())
