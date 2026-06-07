#!/usr/bin/env python3
"""
Background monitor - just watches ALL /u/search calls continuously
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def background_monitor():
    print('🔍 Background Monitor - Starting...')
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Use existing page
    pages = context.pages
    if pages:
        page = pages[0]
        print(f'✅ Monitoring: {page.url[:60]}...')
    else:
        print('⚠️  No pages open')
        await playwright.stop()
        return
    
    api_calls = []
    
    async def handle_request(request):
        url = request.url
        if '/u/search' in url:
            timestamp = datetime.now().strftime('%H:%M:%S')
            body = None
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except:
                    body = None
            api_calls.append({'timestamp': timestamp, 'type': 'request', 'url': url, 'body': body})
            print(f'[{timestamp}] → POST /u/search')
    
    async def handle_response(response):
        url = response.url
        if '/u/search' in url:
            timestamp = datetime.now().strftime('%H:%M:%S')
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
                print(f'[{timestamp}] {indicator} count={count}')
    
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print()
    print('✅ MONITORING ACTIVE')
    print('=' * 80)
    print('👉 Go click Service + Parts checkboxes NOW')
    print('👉 Press Ctrl+C when done')
    print('=' * 80)
    print()
    
    try:
        await asyncio.sleep(600)  # Monitor for 10 minutes
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    
    print()
    print('⏹️  Stopped')
    
    if api_calls:
        filename = f'background_capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump({'calls': api_calls}, f, indent=2)
        
        print(f'✅ Saved: {filename}')
        
        responses = [c for c in api_calls if c.get('type') == 'response']
        counts = [r['data_count'] for r in responses if r.get('data_count') is not None]
        count_gt_zero = [c for c in counts if c > 0]
        unique = sorted(set(count_gt_zero), reverse=True)
        
        print(f'Captured: {len(api_calls)//2} API calls')
        print(f'Count > 0: {len(count_gt_zero)} APIs')
        print(f'Unique counts: {unique}')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(background_monitor())
