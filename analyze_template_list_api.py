#!/usr/bin/env python3
"""
Analyze API calls before and after applying filters on templates list page
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def analyze_template_list_api():
    """Analyze API calls before and after filter"""
    
    print('🔍 Template List API Analyzer')
    print('=' * 80)
    print()
    
    # Connect to existing browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Create new page
    page = await context.new_page()
    
    # Storage for captured API calls
    captured_calls = []
    
    # Capture API requests and responses
    async def handle_request(request):
        url = request.url
        
        # Only track relevant API calls
        if any(keyword in url for keyword in ['/api/', '/search', '/template', 'graphql']):
            call_info = {
                'timestamp': datetime.now().isoformat(),
                'type': 'request',
                'method': request.method,
                'url': url,
                'headers': dict(request.headers) if request.headers else {},
                'post_data': request.post_data
            }
            captured_calls.append(call_info)
            print(f'→ {request.method} {url.split("?")[0].split("/")[-2:][-2:]}')
    
    async def handle_response(response):
        url = response.url
        
        if any(keyword in url for keyword in ['/api/', '/search', '/template', 'graphql']):
            try:
                # Get response data
                if response.status == 200:
                    try:
                        data = await response.json()
                        preview = json.dumps(data)[:200]
                    except:
                        preview = '[Not JSON]'
                else:
                    preview = f'[Status: {response.status}]'
                
                call_info = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'response',
                    'method': response.request.method,
                    'url': url,
                    'status': response.status,
                    'preview': preview
                }
                captured_calls.append(call_info)
                print(f'← {response.status} {url.split("?")[0].split("/")[-2:][-2:]}')
                
            except Exception as e:
                print(f'  Error capturing response: {e}')
    
    # Attach listeners
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    # PHASE 1: Load page (before filter)
    print('\n📍 PHASE 1: Loading templates list (no filter)')
    print('-' * 80)
    
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded',
                    timeout=30000)
    
    await asyncio.sleep(5)  # Wait for initial API calls
    
    before_filter_count = len(captured_calls)
    print(f'\n✅ Captured {before_filter_count} API calls before filter')
    
    # PHASE 2: Apply filter
    print('\n📍 PHASE 2: Manually apply the filter')
    print('-' * 80)
    print()
    print('⏸️  PAUSED - Please manually apply the filter:')
    print('   1. Click on the Department dropdown')
    print('   2. Select "Service"')
    print('   3. Wait for the templates to reload')
    print()
    print('Press Enter when you have applied the filter...')
    print()

    # Wait for user to press Enter
    try:
        input()
        print('✅ Continuing with API capture after filter...')
        await asyncio.sleep(2)  # Give time for any pending API calls
    except KeyboardInterrupt:
        print('\n⚠️  Cancelled by user')
    
    after_filter_count = len(captured_calls) - before_filter_count
    print(f'\n✅ Captured {after_filter_count} API calls after filter')
    
    # Save results
    print('\n💾 Saving results...')
    
    output = {
        'analysis_date': datetime.now().isoformat(),
        'total_calls': len(captured_calls),
        'before_filter_calls': before_filter_count,
        'after_filter_calls': after_filter_count,
        'calls': captured_calls
    }
    
    with open('api_analysis_templates_list.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print('✅ Saved to: api_analysis_templates_list.json')
    
    # Print summary
    print('\n' + '=' * 80)
    print('📊 SUMMARY')
    print('=' * 80)
    
    # Group calls by endpoint
    endpoints = {}
    for call in captured_calls:
        endpoint = call['url'].split('?')[0].split('/')[-1]
        if endpoint not in endpoints:
            endpoints[endpoint] = []
        endpoints[endpoint].append(call)
    
    print(f'\nUnique endpoints called: {len(endpoints)}')
    for endpoint, calls in sorted(endpoints.items(), key=lambda x: len(x[1]), reverse=True):
        print(f'  • {endpoint}: {len(calls)} calls')
    
    print('\n✅ Analysis complete!')
    
    await page.close()
    await browser.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(analyze_template_list_api())
