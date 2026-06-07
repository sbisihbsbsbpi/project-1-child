#!/usr/bin/env python3
"""
Capture API calls when Service & Parts filters are applied
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def capture_filter_api_calls():
    """Monitor API calls in real-time during filter application"""
    
    print('🔍 API Call Monitor - Service & Parts Filter')
    print('=' * 80)
    print()
    
    # Connect to existing browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Get or create page
    pages = context.pages
    if pages:
        page = pages[0]
        print(f'✅ Using existing page')
    else:
        page = await context.new_page()
        print('✅ Created new page')
    
    print(f'   URL: {page.url[:80]}...')
    print()
    
    # Storage for API calls
    api_calls = []
    call_count = 0
    
    # Track /u/search calls specifically
    async def handle_request(request):
        nonlocal call_count
        url = request.url
        
        if '/u/search' in url:
            call_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Get request body
            body = None
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except:
                    body = request.post_data
            
            call_info = {
                'call_number': call_count,
                'timestamp': timestamp,
                'type': 'request',
                'method': request.method,
                'url': url,
                'body': body
            }
            
            api_calls.append(call_info)
            
            print(f'[{timestamp}] #{call_count:2d} → POST /u/search')
            
            # Try to show department filter from body
            if body and isinstance(body, dict):
                try:
                    # Navigate to department filter
                    filters = body.get('groupBy', [{}])[0].get('filters', [])
                    for f in filters:
                        for af in f.get('andFilters', []):
                            if af.get('field') == 'departments':
                                depts = af.get('values', [])
                                print(f'           Departments: {depts}')
                                break
                except:
                    pass
    
    async def handle_response(response):
        url = response.url
        
        if '/u/search' in url:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Get response data
            count = None
            hits_count = None
            try:
                if response.status == 200:
                    data = await response.json()
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
                'hits_returned': hits_count
            }
            
            api_calls.append(call_info)
            
            status_str = f'{response.status}'
            if count is not None:
                print(f'[{timestamp}]      ← {status_str} data.count={count}', end='')
                if hits_count is not None and hits_count > 0:
                    print(f' ({hits_count} templates returned)', end='')
                print()
            else:
                print(f'[{timestamp}]      ← {status_str}')
    
    # Attach listeners
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print()
    print('✅ Monitoring started!')
    print('=' * 80)
    print()
    print('INSTRUCTIONS:')
    print('1. Go to https://preprodapp.tekioncloud.com/templates/list (if not there)')
    print('2. Click on the Department dropdown')
    print('3. Check "Service" checkbox')
    print('4. Check "Parts" checkbox')
    print('5. Wait for API calls to complete (watch below)')
    print('6. Press Ctrl+C when all calls are done')
    print()
    print('─' * 80)
    print('API CALLS:')
    print('─' * 80)
    print()
    
    # Keep monitoring
    try:
        await asyncio.sleep(3600)  # Monitor for 1 hour max
    except KeyboardInterrupt:
        print()
        print()
        print('─' * 80)
        print('⏹️  Monitoring stopped')
        print('─' * 80)
    
    # Save and summarize
    if api_calls:
        print()
        print('💾 Saving captured data...')
        
        # Separate requests and responses
        requests = [c for c in api_calls if c.get('type') == 'request']
        responses = [c for c in api_calls if c.get('type') == 'response']
        
        output = {
            'capture_date': datetime.now().isoformat(),
            'total_calls': len(api_calls),
            'total_requests': len(requests),
            'total_responses': len(responses),
            'calls': api_calls
        }
        
        filename = f'filter_api_calls_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f'✅ Saved to: {filename}')
        print()
        
        # Summary
        print('=' * 80)
        print('📊 SUMMARY')
        print('=' * 80)
        print()
        print(f'Total /u/search requests: {len(requests)}')
        print(f'Total /u/search responses: {len(responses)}')
        print()
        
        # Show responses with count > 0
        print('Responses with data.count > 0:')
        count_gt_zero = [r for r in responses if r.get('data_count', 0) > 0]
        if count_gt_zero:
            for r in count_gt_zero:
                count = r.get('data_count')
                hits = r.get('hits_returned', 0)
                print(f'  • data.count = {count}', end='')
                if hits > 0:
                    print(f' ({hits} templates returned)', end='')
                print()
            print()
            print(f'✅ Found {len(count_gt_zero)} API calls with count > 0')
        else:
            print('  None found')
        print()
        
        # Show unique count values
        counts = [r.get('data_count') for r in responses if r.get('data_count') is not None]
        if counts:
            unique_counts = sorted(set(counts), reverse=True)
            print(f'Unique data.count values: {unique_counts}')
            print()
            for count in unique_counts:
                occurrences = counts.count(count)
                print(f'  • {count}: appeared {occurrences} time(s)')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(capture_filter_api_calls())
