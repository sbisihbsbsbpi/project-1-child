#!/usr/bin/env python3
"""
SIMPLE: Go to link, wait, enable capture, YOU click Service manually, capture APIs
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def simple_capture():
    print('🔍 Simple Service Filter Capture')
    print('=' * 80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
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
            print(f'[{timestamp}] ✅ → POST /u/search')
    
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
                print(f'[{timestamp}] ✅ data.count = {count}')
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print()
    print('Step 1: Going to templates list...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded', timeout=30000)
    print('✅ Page loaded')

    print()
    print('Step 2: ENABLING CAPTURE IMMEDIATELY')
    print('─' * 80)
    capture_enabled = True
    print('✅ Capture enabled')

    print()
    print('Step 3: Waiting 5 seconds for initial page load APIs...')
    await asyncio.sleep(5)
    print('✅ Initial APIs should have passed')
    print()
    print('Step 4: Ready for you to click filters')
    print('─' * 80)
    print()
    print('👉 NOW: Click the Department dropdown')
    print('👉 Check Service checkbox (watch for API calls)')
    print('👉 Check Parts checkbox (watch for more API calls)')
    print('👉 You have 40 seconds')
    print()
    print('─' * 80)
    print('API CALLS:')
    print()

    # Wait for you to click - increased to 40 seconds
    await asyncio.sleep(40)
    
    capture_enabled = False
    print()
    print('─' * 80)
    print('✅ Capture stopped')
    
    if api_calls:
        filename = f'service_parts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump({'calls': api_calls}, f, indent=2)
        
        print(f'✅ Saved to: {filename}')
        print()
        responses = [c for c in api_calls if c.get('type') == 'response']
        counts = [r['data_count'] for r in responses if r.get('data_count') is not None]
        count_gt_zero = [c for c in counts if c > 0]
        
        print(f'APIs captured: {len(api_calls)//2}')
        print(f'APIs with count > 0: {len(count_gt_zero)}')
        if count_gt_zero:
            print(f'Count values: {count_gt_zero}')
    else:
        print('⚠️  No APIs captured - you may not have clicked or APIs already completed')
    
    await page.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(simple_capture())
