#!/usr/bin/env python3
"""
Monitor API calls while you manually apply Service & Parts filters
SIMPLE VERSION - Just monitors, you click manually
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def monitor_while_you_click():
    """Monitor API calls while you manually click filters"""
    
    print('🔍 Service & Parts Filter - API Monitor')
    print('=' * 80)
    print()
    
    # Connect to existing browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Use existing page
    pages = context.pages
    if pages:
        page = pages[0]
        print(f'✅ Connected to browser')
        print(f'   Current page: {page.url[:70]}...')
    else:
        page = await context.new_page()
        print('✅ Created new page')
        await page.goto('https://preprodapp.tekioncloud.com/templates/list')
        await asyncio.sleep(3)
    
    print()
    
    # Storage for API calls
    api_calls = []
    
    # Track /u/search calls
    async def handle_request(request):
        url = request.url
        
        if '/u/search' in url:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Get request body
            body = None
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except:
                    body = request.post_data[:500]
            
            call_info = {
                'timestamp': timestamp,
                'type': 'request',
                'url': url,
                'body': body
            }
            
            api_calls.append(call_info)
            
            print(f'[{timestamp}] → POST /u/search')
            
            # Show departments
            if body and isinstance(body, dict):
                try:
                    filters = body.get('groupBy', [{}])[0].get('filters', [])
                    for f in filters[:1]:
                        for af in f.get('andFilters', []):
                            if af.get('field') == 'departments':
                                depts = af.get('values', [])
                                print(f'               Departments filter: {depts}')
                                break
                except:
                    pass
    
    async def handle_response(response):
        url = response.url
        
        if '/u/search' in url:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Get response
            count = None
            hits_count = None
            full_data = None
            try:
                if response.status == 200:
                    data = await response.json()
                    full_data = data
                    if 'data' in data:
                        count = data['data'].get('count')
                        hits = data['data'].get('hits', [])
                        hits_count = len(hits)
            except:
                pass
            
            call_info = {
                'timestamp': timestamp,
                'type': 'response',
                'status': response.status,
                'data_count': count,
                'hits_returned': hits_count,
                'full_response': full_data
            }
            
            api_calls.append(call_info)
            
            if count is not None:
                indicator = '✅' if count > 0 else '  '
                print(f'[{timestamp}] {indicator} ← data.count = {count}', end='')
                if hits_count and hits_count > 0:
                    print(f' ({hits_count} templates)', end='')
                print()
            else:
                print(f'[{timestamp}]    ← Status {response.status}')
    
    # Attach listeners
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print('✅ Monitoring ACTIVE!')
    print('=' * 80)
    print()
    print('📋 INSTRUCTIONS:')
    print('   1. Click on the Department dropdown')
    print('   2. Check "Service" checkbox')
    print('   3. Check "Parts" checkbox')
    print('   4. Wait 3-5 seconds for all API calls to finish')
    print('   5. Press Ctrl+C to stop and save')
    print()
    print('─' * 80)
    print('API CALLS (watching...):\n')
    
    # Monitor
    try:
        await asyncio.sleep(600)  # Monitor for 10 minutes
    except (KeyboardInterrupt, asyncio.CancelledError):
        print('\n')
        print('─' * 80)
        print('⏹️  Stopped monitoring')
    
    # Save
    if api_calls:
        print()
        print('💾 Saving...')
        
        requests = [c for c in api_calls if c.get('type') == 'request']
        responses = [c for c in api_calls if c.get('type') == 'response']
        
        output = {
            'capture_date': datetime.now().isoformat(),
            'note': 'Service & Parts filters applied manually',
            'total_calls': len(api_calls),
            'calls': api_calls
        }
        
        filename = f'service_parts_api_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f'✅ Saved to: {filename}')
        print()
        print('=' * 80)
        print('📊 SUMMARY')
        print('=' * 80)
        print(f'Total requests: {len(requests)}')
        print(f'Total responses: {len(responses)}')
        print()
        
        # Count analysis
        count_responses = [r for r in responses if r.get('data_count') is not None]
        if count_responses:
            counts = [r['data_count'] for r in count_responses]
            count_gt_zero = [c for c in counts if c > 0]
            
            print(f'APIs with data.count > 0: {len(count_gt_zero)}')
            if count_gt_zero:
                print('Values:')
                for i, r in enumerate([r for r in count_responses if r['data_count'] > 0], 1):
                    print(f'  {i}. count = {r["data_count"]}', end='')
                    if r.get('hits_returned', 0) > 0:
                        print(f' ({r["hits_returned"]} templates returned)', end='')
                    print()
            
            print()
            print(f'All count values: {counts}')
            print(f'Unique values: {sorted(set(counts), reverse=True)}')
    else:
        print('\n⚠️  No API calls captured')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(monitor_while_you_click())
