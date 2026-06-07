#!/usr/bin/env python3
"""
Capture API calls on demand - YOU control when to start
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import sys


async def capture_on_demand():
    print('🔍 On-Demand API Capture')
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
                indicator = '✅' if count > 0 else '  '
                print(f'[{timestamp}] {indicator} data.count = {count}')
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print()
    print('Step 1: Going to templates list...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded', timeout=30000)
    print('✅ Page loaded')
    
    print()
    print('Step 2: Waiting for page to fully load (10 seconds)...')
    await asyncio.sleep(10)
    print('✅ Page ready')
    
    print()
    print('=' * 80)
    print('INSTRUCTIONS:')
    print('=' * 80)
    print()
    print('1. Go to the browser window')
    print('2. Click Department dropdown')
    print('3. Check Service checkbox')
    print('4. Check Parts checkbox')
    print('5. Come back here and press ENTER')
    print()
    print('Waiting for you to press ENTER...')
    
    # Wait for Enter key
    await asyncio.get_event_loop().run_in_executor(None, input)
    
    print()
    print('✅ Starting capture NOW!')
    print('─' * 80)
    capture_enabled = True
    
    # Give time for any pending API calls from your clicks
    await asyncio.sleep(10)
    
    capture_enabled = False
    print('─' * 80)
    print('✅ Capture stopped')
    print()
    
    if api_calls:
        filename = f'service_parts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump({'calls': api_calls, 'filter': 'Service + Parts'}, f, indent=2)
        
        print(f'✅ Saved to: {filename}')
        print()
        
        responses = [c for c in api_calls if c.get('type') == 'response']
        counts = [r['data_count'] for r in responses if r.get('data_count') is not None]
        count_gt_zero = [c for c in counts if c > 0]
        unique_counts = sorted(set(count_gt_zero), reverse=True)
        
        print('=' * 80)
        print('📊 RESULTS')
        print('=' * 80)
        print(f'Total API calls: {len(api_calls)//2}')
        print(f'APIs with count > 0: {len(count_gt_zero)}')
        print(f'Unique count values: {unique_counts}')
        print()
        if count_gt_zero:
            print('All count values:')
            print(f'  {count_gt_zero}')
    else:
        print('⚠️  No APIs captured')
        print('The filters may have been applied before you pressed Enter')
        print('Try again and press Enter BEFORE clicking the filters')
    
    await page.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(capture_on_demand())
