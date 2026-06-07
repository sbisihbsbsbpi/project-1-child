#!/usr/bin/env python3
"""
Monitor ALL API calls in sequence when applying Service + Parts filter
Shows the complete flow: uncheck Sales → check Service → check Parts
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def monitor_sequence():
    print('🔍 Monitoring COMPLETE API Call Sequence')
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
    call_num = 0
    
    async def handle_request(request):
        nonlocal call_num
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
                
                call_num += 1
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                print(f'[{timestamp}] REQUEST #{call_num}:')
                print(f'             Departments: {depts}')
                print(f'             Purpose: {purpose}')
                
                api_calls.append({
                    'type': 'request',
                    'num': call_num,
                    'timestamp': timestamp,
                    'departments': depts,
                    'purpose': purpose,
                    'body': body
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
                indicator = '✅' if count and count > 0 else '  '
                
                print(f'[{timestamp}] {indicator} RESPONSE: count={count}, templates={len(hits)}')
                print()
                
                api_calls.append({
                    'type': 'response',
                    'timestamp': timestamp,
                    'count': count,
                    'template_count': len(hits)
                })
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
    await asyncio.sleep(3)
    
    print()
    print('=' * 80)
    print('Step 2: Applying Department Filter')
    print('=' * 80)
    print()
    
    try:
        # Click dropdown
        print('Opening dropdown...')
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)
        
        print()
        print('UNCHECKING SALES...')
        print('─' * 80)
        # Uncheck Sales
        sales_cb = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(1) input')
        if sales_cb and await sales_cb.is_checked():
            await sales_cb.click()
            await asyncio.sleep(2)  # Wait for API
        
        print()
        print('CHECKING SERVICE...')
        print('─' * 80)
        # Check Service
        service_cb = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(2) input')
        if service_cb:
            await service_cb.click()
            await asyncio.sleep(2)  # Wait for API
        
        print()
        print('CHECKING PARTS...')
        print('─' * 80)
        # Check Parts
        parts_cb = await page.query_selector('.ant-checkbox-group .ant-checkbox-wrapper:nth-of-type(3) input')
        if parts_cb:
            await parts_cb.click()
            await asyncio.sleep(2)  # Wait for API
        
        print()
        print('Closing dropdown and waiting for final API calls...')
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(3)
        
    except Exception as e:
        print(f'❌ Error: {e}')
    
    print()
    print('=' * 80)
    print('📊 COMPLETE SEQUENCE SUMMARY')
    print('=' * 80)
    print()
    
    # Analyze
    requests = [c for c in api_calls if c.get('type') == 'request']
    responses = [c for c in api_calls if c.get('type') == 'response']
    
    print(f'Total requests: {len(requests)}')
    print(f'Total responses: {len(responses)}')
    print()
    
    # Show the sequence
    print('Call-by-call breakdown:')
    print()
    req_idx = 0
    for call in api_calls:
        if call.get('type') == 'request':
            req_idx += 1
            print(f'{req_idx}. REQUEST: Depts={call.get("departments")} | Purpose={call.get("purpose")}')
        else:
            count = call.get('count')
            indicator = '✅' if count and count > 0 else '  '
            print(f'   {indicator} RESPONSE: count={count}')
            print()
    
    # Save
    filename = f'api_sequence_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump({'sequence': api_calls}, f, indent=2)
    
    print(f'✅ Saved to: {filename}')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(monitor_sequence())
