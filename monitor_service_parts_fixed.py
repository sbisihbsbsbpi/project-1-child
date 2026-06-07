#!/usr/bin/env python3
"""
Monitor Service + Parts API with proper timing - wait for each API response
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def monitor_with_proper_timing():
    print('🔍 Service + Parts API Monitor (Fixed Timing)')
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
    
    api_calls = []
    response_event = None
    
    def create_response_event():
        return asyncio.Event()
    
    async def handle_request(request):
        if '/u/search' in request.url and request.post_data:
            try:
                body = json.loads(request.post_data)
                
                # Get departments
                depts = None
                purpose = None
                filters = body.get('filters', [])
                for f in filters:
                    if f.get('field') == 'departments':
                        depts = f.get('values', [])
                    if f.get('field') == 'purposeSubType':
                        purpose = f.get('values', [])
                
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                print(f'[{timestamp}] → REQUEST:')
                print(f'             Departments: {depts}')
                print(f'             Purpose: {purpose}')
                
                api_calls.append({
                    'type': 'request',
                    'timestamp': timestamp,
                    'departments': depts,
                    'purpose': purpose,
                    'body': body
                })
            except:
                pass
    
    async def handle_response(response):
        nonlocal response_event
        if '/u/search' in response.url:
            try:
                data = await response.json()
                count = data.get('data', {}).get('count')
                hits = data.get('data', {}).get('hits', [])
                
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                indicator = '✅' if count and count > 0 else '  '
                
                print(f'[{timestamp}] {indicator} ← RESPONSE: count={count}, templates={len(hits)}')
                print()
                
                api_calls.append({
                    'type': 'response',
                    'timestamp': timestamp,
                    'count': count,
                    'template_count': len(hits),
                    'full_data': data
                })
                
                # Signal that response received
                if response_event:
                    response_event.set()
            except:
                pass
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print('✅ Monitoring started')
    print()
    print('Step 1: Navigating to templates list...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded', timeout=30000)
    print('✅ Page loaded (Sales is checked by default)')
    
    # Wait for initial API calls to settle
    await asyncio.sleep(5)
    
    print()
    print('=' * 80)
    print('Step 2: Applying Department Filter with Proper Timing')
    print('=' * 80)
    print()
    
    try:
        # Open dropdown
        print('Opening dropdown...')
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)
        print()
        
        # Step 1: Uncheck Sales and WAIT for API
        print('STEP 1: Unchecking SALES...')
        print('─' * 80)
        response_event = create_response_event()
        
        sales_cb = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(1) input')
        if sales_cb and await sales_cb.is_checked():
            await sales_cb.click()
            print('Clicked Sales checkbox, waiting for API response...')
            
            try:
                await asyncio.wait_for(response_event.wait(), timeout=5.0)
                print('✅ API response received')
            except asyncio.TimeoutError:
                print('⚠️  Timeout waiting for API response')
        
        await asyncio.sleep(1)
        print()
        
        # Step 2: Check Service and WAIT for API
        print('STEP 2: Checking SERVICE...')
        print('─' * 80)
        response_event = create_response_event()
        
        service_cb = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(2) input')
        if service_cb:
            is_checked = await service_cb.is_checked()
            if not is_checked:
                await service_cb.click()
                print('Clicked Service checkbox, waiting for API response...')
                
                try:
                    await asyncio.wait_for(response_event.wait(), timeout=5.0)
                    print('✅ API response received')
                except asyncio.TimeoutError:
                    print('⚠️  Timeout waiting for API response')
        
        await asyncio.sleep(1)
        print()
        
        # Step 3: Check Parts and WAIT for API
        print('STEP 3: Checking PARTS...')
        print('─' * 80)
        response_event = create_response_event()
        
        parts_cb = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(3) input')
        if parts_cb:
            is_checked = await parts_cb.is_checked()
            if not is_checked:
                await parts_cb.click()
                print('Clicked Parts checkbox, waiting for API response...')
                
                try:
                    await asyncio.wait_for(response_event.wait(), timeout=5.0)
                    print('✅ API response received')
                except asyncio.TimeoutError:
                    print('⚠️  Timeout waiting for API response')
        
        await asyncio.sleep(1)
        print()
        
        # Step 4: Close dropdown and capture final state
        print('STEP 4: Closing dropdown...')
        print('─' * 80)
        response_event = create_response_event()
        
        await page.keyboard.press('Escape')
        print('Pressed Escape, waiting for final API response...')
        
        try:
            await asyncio.wait_for(response_event.wait(), timeout=5.0)
            print('✅ Final API response received')
        except asyncio.TimeoutError:
            print('⚠️  Timeout waiting for final API response')
        
        # Wait a bit more to catch any trailing API calls
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    print('=' * 80)
    print('📊 COMPLETE API CALL ANALYSIS')
    print('=' * 80)
    print()
    
    # Find Service + Parts calls
    print('Looking for Service + Parts API calls:')
    print()
    
    for i, call in enumerate(api_calls):
        if call.get('type') == 'request':
            depts = call.get('departments')
            if depts and 'SERVICE' in depts and 'PARTS' in depts:
                print(f'🎯 FOUND SERVICE + PARTS REQUEST!')
                print(f'   Timestamp: {call.get("timestamp")}')
                print(f'   Departments: {depts}')
                print(f'   Purpose: {call.get("purpose")}')
                print()
                
                # Find matching response
                for j in range(i+1, min(i+5, len(api_calls))):
                    if api_calls[j].get('type') == 'response':
                        resp = api_calls[j]
                        print(f'   ✅ RESPONSE:')
                        print(f'      Timestamp: {resp.get("timestamp")}')
                        print(f'      Count: {resp.get("count")}')
                        print(f'      Templates: {resp.get("template_count")}')
                        print()
                        break
    
    # Save
    filename = f'service_parts_fixed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump({'api_calls': api_calls}, f, indent=2)
    
    print(f'✅ Saved complete sequence to: {filename}')
    print()
    print(f'Total API calls captured: {len([c for c in api_calls if c.get("type") == "request"])}')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(monitor_with_proper_timing())
