#!/usr/bin/env python3
"""
Automatically apply Service & Parts filters and capture API calls
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def auto_apply_filters_and_capture():
    """Apply filters automatically and capture API calls"""
    
    print('🔍 Auto Filter & API Capture')
    print('=' * 80)
    print()
    
    # Connect to existing browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]

    # Use existing page (don't create new one)
    pages = context.pages
    if pages:
        page = pages[0]
        print(f'✅ Using existing page: {page.url[:60]}...')
    else:
        page = await context.new_page()
        print('✅ Created new page')
    
    # Storage for API calls
    api_calls = []
    filter_applied = False
    
    # Track /u/search calls
    async def handle_request(request):
        url = request.url
        
        if '/u/search' in url and filter_applied:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Get request body
            body = None
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except:
                    body = request.post_data
            
            call_info = {
                'timestamp': timestamp,
                'type': 'request',
                'method': request.method,
                'url': url,
                'body': body
            }
            
            api_calls.append(call_info)
            
            print(f'[{timestamp}] → POST /u/search')
            
            # Show department filter
            if body and isinstance(body, dict):
                try:
                    filters = body.get('groupBy', [{}])[0].get('filters', [])
                    for f in filters[:1]:  # Just show first one
                        for af in f.get('andFilters', []):
                            if af.get('field') == 'departments':
                                depts = af.get('values', [])
                                print(f'           Departments: {depts}')
                                break
                except:
                    pass
    
    async def handle_response(response):
        url = response.url
        
        if '/u/search' in url and filter_applied:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Get response data
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
                print(f'[{timestamp}]      ← 200 data.count={count}', end='')
                if hits_count is not None and hits_count > 0:
                    print(f' ({hits_count} templates)', end='')
                print()
            else:
                print(f'[{timestamp}]      ← {response.status}')
    
    # Attach listeners
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    # Step 1: Check current page or navigate
    print()
    print('Step 1: Checking page...')
    current_url = page.url
    if '/templates/list' not in current_url:
        print(f'Current URL: {current_url}')
        print('Navigating to templates list...')
        await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                        wait_until='domcontentloaded',
                        timeout=30000)
        await asyncio.sleep(3)
        print('✅ Page loaded')
    else:
        print('✅ Already on templates list page')
        await asyncio.sleep(1)
    
    # Step 2: Find and click department dropdown
    print()
    print('Step 2: Opening department filter...')
    
    try:
        # Try multiple selectors
        selectors = [
            'div[class*="Select"]:has-text("Department")',
            'div[class*="select"]:has-text("Department")',
            '[placeholder*="Department"]',
            'input[placeholder*="Select"]',
            'div.Select-placeholder',
        ]
        
        dropdown_found = False
        for selector in selectors:
            try:
                await page.click(selector, timeout=2000)
                dropdown_found = True
                print(f'✅ Clicked dropdown using: {selector}')
                break
            except:
                continue
        
        if not dropdown_found:
            # Try finding by text
            print('Trying to find dropdown by examining page...')
            await page.screenshot(path='dropdown_debug.png')
            print('⚠️  Could not find dropdown, saved screenshot to dropdown_debug.png')
            raise Exception("Dropdown not found")
        
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f'⚠️  Error finding dropdown: {e}')
        print('Trying alternative approach...')
        
        # Alternative: Click anywhere that might be the dropdown
        await page.click('text="Department"', timeout=5000)
        await asyncio.sleep(1)
    
    # Step 3: Select Service
    print()
    print('Step 3: Selecting Service...')
    print('Starting API capture...')
    print('─' * 80)
    
    filter_applied = True  # Start capturing
    
    try:
        await page.click('text="Service"', timeout=5000)
        print('✅ Clicked Service')
        await asyncio.sleep(3)  # Wait for API calls
    except Exception as e:
        print(f'⚠️  Error clicking Service: {e}')
    
    # Step 4: Select Parts
    print()
    print('Step 4: Selecting Parts...')
    
    try:
        await page.click('text="Parts"', timeout=5000)
        print('✅ Clicked Parts')
        await asyncio.sleep(3)  # Wait for API calls
    except Exception as e:
        print(f'⚠️  Error clicking Parts: {e}')
    
    # Step 5: Wait for any final API calls
    print()
    print('Step 5: Waiting for API calls to complete...')
    await asyncio.sleep(3)
    
    print('─' * 80)
    print()
    print('✅ Filter application complete!')
    
    # Save results
    if api_calls:
        print()
        print('💾 Saving captured API calls...')
        
        # Separate requests and responses
        requests = [c for c in api_calls if c.get('type') == 'request']
        responses = [c for c in api_calls if c.get('type') == 'response']
        
        output = {
            'capture_date': datetime.now().isoformat(),
            'filters_applied': ['Service', 'Parts'],
            'total_calls': len(api_calls),
            'total_requests': len(requests),
            'total_responses': len(responses),
            'calls': api_calls
        }
        
        filename = f'service_parts_api_calls_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f'✅ Saved to: {filename}')
        print()
        
        # Summary
        print('=' * 80)
        print('📊 SUMMARY - Service & Parts Filters')
        print('=' * 80)
        print()
        print(f'Total /u/search requests: {len(requests)}')
        print(f'Total /u/search responses: {len(responses)}')
        print()
        
        # Show responses with count > 0
        print('Responses with data.count > 0:')
        count_responses = [r for r in responses if r.get('data_count') is not None]
        count_gt_zero = [r for r in count_responses if r.get('data_count', 0) > 0]
        
        if count_gt_zero:
            for i, r in enumerate(count_gt_zero, 1):
                count = r.get('data_count')
                hits = r.get('hits_returned', 0)
                print(f'  {i}. data.count = {count}', end='')
                if hits > 0:
                    print(f' ({hits} templates returned)', end='')
                print()
            print()
            print(f'✅ Found {len(count_gt_zero)} API calls with count > 0')
        else:
            print('  None found')
        
        print()
        
        # Show all count values
        if count_responses:
            counts = [r.get('data_count') for r in count_responses]
            unique_counts = sorted(set(counts), reverse=True)
            print(f'All data.count values: {counts}')
            print(f'Unique values: {unique_counts}')
            print()
            for count in unique_counts:
                occurrences = counts.count(count)
                print(f'  • count={count}: appeared {occurrences} time(s)')
    else:
        print()
        print('⚠️  No API calls captured')
        print('This might mean:')
        print('  - Filters were not applied correctly')
        print('  - API calls happened before monitoring started')
        print('  - Page uses different filter mechanism')
    
    await page.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(auto_apply_filters_and_capture())
