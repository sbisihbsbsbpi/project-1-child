#!/usr/bin/env python3
"""
Fresh capture - open browser, apply Service + Parts, capture APIs
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def fresh_capture():
    print('🔍 Fresh Service + Parts Capture')
    print('=' * 80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Create NEW page
    page = await context.new_page()
    print('✅ New page created')
    
    api_calls = []
    capture_enabled = False
    
    async def handle_request(request):
        if not capture_enabled:
            return
        url = request.url
        if '/u/search' in url:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            body = None
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except:
                    body = request.post_data[:500]
            
            api_calls.append({'timestamp': timestamp, 'type': 'request', 'url': url, 'body': body})
            print(f'[{timestamp}] → POST /u/search')
            
            # Show departments if found
            if body and isinstance(body, dict):
                filters = body.get('filters', [])
                for f in filters:
                    if f.get('field') == 'departments':
                        print(f'           Departments: {f.get("values")}')
    
    async def handle_response(response):
        if not capture_enabled:
            return
        url = response.url
        if '/u/search' in url:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            count = None
            full_data = None
            try:
                if response.status == 200:
                    data = await response.json()
                    full_data = data
                    if 'data' in data:
                        count = data['data'].get('count')
            except:
                pass
            
            api_calls.append({'timestamp': timestamp, 'type': 'response', 'status': response.status,
                            'data_count': count, 'full_response': full_data})
            
            if count is not None:
                indicator = '✅' if count > 0 else '   '
                print(f'[{timestamp}] {indicator} count = {count}')
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print()
    print('Step 1: Navigating to templates list...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded', timeout=30000)
    print('✅ Page loaded')
    
    print()
    print('Step 2: Waiting for page to settle (8 seconds)...')
    await asyncio.sleep(8)
    print('✅ Ready')
    
    print()
    print('Step 3: Opening Department dropdown...')
    try:
        # Try to click Department
        await page.click('text="Department"', timeout=5000)
        await asyncio.sleep(1)
        print('✅ Dropdown opened')
    except Exception as e:
        print(f'⚠️  Could not open dropdown: {e}')
        print('Please open it manually')
    
    print()
    print('Step 4: ENABLING CAPTURE NOW')
    print('─' * 80)
    capture_enabled = True
    print()
    print('👉 PLEASE MANUALLY:')
    print('   1. Check Service checkbox')
    print('   2. Check Parts checkbox')
    print('   3. Wait for API calls below')
    print()
    print('You have 30 seconds...')
    print('─' * 80)
    print()
    
    # Wait 30 seconds for manual clicks
    await asyncio.sleep(30)
    
    capture_enabled = False
    print('─' * 80)
    print()
    print('✅ Capture complete')
    
    if api_calls:
        filename = f'fresh_service_parts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump({'calls': api_calls, 'filter': 'Service + Parts'}, f, indent=2)
        
        print(f'✅ Saved: {filename}')
        print()
        
        responses = [c for c in api_calls if c.get('type') == 'response']
        counts = [r['data_count'] for r in responses if r.get('data_count') is not None]
        count_gt_zero = [c for c in counts if c > 0]
        unique = sorted(set(count_gt_zero), reverse=True)
        
        print('=' * 80)
        print('📊 RESULTS')
        print('=' * 80)
        print(f'Total API calls: {len(api_calls)//2}')
        print(f'APIs with count > 0: {len(count_gt_zero)}')
        print(f'Unique count values: {unique}')
        print()
        print(f'All counts: {counts}')
        
        # Find Service + Parts calls
        print()
        print('Service + Parts specific calls:')
        for call in api_calls:
            if call.get('type') == 'request':
                body = call.get('body')
                if body and isinstance(body, dict):
                    filters = body.get('filters', [])
                    for f in filters:
                        if f.get('field') == 'departments':
                            depts = f.get('values', [])
                            if 'SERVICE' in depts and 'PARTS' in depts:
                                print(f'  ✅ Found Service + Parts call')
                                # Find its response
                                idx = api_calls.index(call)
                                for i in range(idx+1, min(idx+5, len(api_calls))):
                                    if api_calls[i].get('type') == 'response':
                                        cnt = api_calls[i].get('data_count')
                                        print(f'     Response count: {cnt}')
                                        break
    else:
        print('⚠️  No APIs captured')
    
    await page.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(fresh_capture())
