#!/usr/bin/env python3
"""
Go to templates list, wait, click Service, capture /search APIs only
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def capture_service_filter():
    """Navigate, click Service, capture search APIs"""
    
    print('🔍 Service Filter - API Capture')
    print('=' * 80)
    print()
    
    # Connect to browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Use existing page or create new
    pages = context.pages
    if pages:
        page = pages[0]
        print(f'✅ Using existing page')
    else:
        page = await context.new_page()
        print(f'✅ Created new page')
    
    # Storage for search API calls ONLY
    search_api_calls = []
    capture_enabled = False
    
    # Track ALL requests during capture to debug
    async def handle_request(request):
        if not capture_enabled:
            return

        url = request.url

        # Show ALL POST requests for debugging
        if request.method == 'POST':
            print(f'  DEBUG: POST to {url.split("/")[-3:]}')

        # Capture /u/search APIs
        if '/u/search' in url or '/templatestore' in url:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

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

            search_api_calls.append(call_info)
            print(f'[{timestamp}] ✅ CAPTURED → {request.method} /u/search')
    
    async def handle_response(response):
        if not capture_enabled:
            return

        url = response.url
        if '/u/search' in url or '/templatestore' in url:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
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
            
            search_api_calls.append(call_info)
            
            if count is not None:
                print(f'[{timestamp}] ✅ data.count = {count}', end='')
                if hits_count and hits_count > 0:
                    print(f' ({hits_count} templates)', end='')
                print()
            else:
                print(f'[{timestamp}] ← Status {response.status}')
    
    # Attach listeners
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    # Step 1: Go to link
    print('Step 1: Navigating to templates list...')
    await page.goto('https://preprodapp.tekioncloud.com/templates/list',
                    wait_until='domcontentloaded',
                    timeout=30000)
    print('✅ Page loaded')
    
    # Step 2: Wait for page to settle and clear any default filters
    print()
    print('Step 2: Waiting for page to settle (8 seconds)...')
    await asyncio.sleep(8)
    print('✅ Page ready')

    # Check if there's already a filter applied
    print()
    print('Checking current state...')
    try:
        current_text = await page.evaluate('document.body.innerText')
        if 'Service' in current_text:
            print('   Found "Service" text on page')
    except:
        pass
    
    # Step 3: Enable capture FIRST
    print()
    print('Step 3: Enabling API capture...')
    capture_enabled = True  # START CAPTURING
    print('✅ Capture enabled')

    # Step 4: Open department dropdown
    print()
    print('Step 4: Opening Department dropdown...')

    try:
        # Click "Department" or the dropdown
        await page.click('text="Department"', timeout=5000)
        await asyncio.sleep(1)
        print('✅ Opened dropdown')

        # Try to click "Clear All" if it exists
        try:
            await page.click('text="Clear All"', timeout=2000)
            await asyncio.sleep(1)
            print('✅ Cleared filters')
        except:
            print('   No Clear All button found (OK)')
    except Exception as e:
        print(f'⚠️  Could not open dropdown: {e}')

    # Step 5: Click Service
    print()
    print('Step 5: Clicking Service...')
    print('─' * 80)

    # Try to click Service using multiple strategies
    clicked = False

    # Strategy 1: Direct text click
    try:
        await page.click('text="Service"', timeout=3000)
        clicked = True
        print('✅ Clicked Service (direct text)')
    except:
        pass

    # Strategy 2: Find checkbox/option with Service
    if not clicked:
        try:
            await page.click('[type="checkbox"]:near(text="Service")', timeout=3000)
            clicked = True
            print('✅ Clicked Service (checkbox)')
        except:
            pass

    # Strategy 3: Evaluate JavaScript to click
    if not clicked:
        try:
            await page.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const serviceEl = elements.find(el => 
                        el.textContent.trim() === 'Service' && 
                        el.offsetParent !== null
                    );
                    if (serviceEl) {
                        serviceEl.click();
                        return true;
                    }
                    return false;
                }
            """)
            clicked = True
            print('✅ Clicked Service (JavaScript)')
        except:
            pass
    
    if not clicked:
        print('⚠️  Could not click Service automatically')
        print('Please click Service checkbox manually now...')
        await asyncio.sleep(10)  # Give time to click manually
    else:
        # Wait for API calls - increased wait time
        print()
        print('Waiting for API calls (8 seconds)...')
        await asyncio.sleep(8)
    
    print('─' * 80)
    
    # Step 4: Disable capture
    capture_enabled = False
    print()
    print('✅ Capture complete')
    
    # Save results
    if search_api_calls:
        print()
        print('💾 Saving captured /search API calls...')
        
        requests = [c for c in search_api_calls if c.get('type') == 'request']
        responses = [c for c in search_api_calls if c.get('type') == 'response']
        
        output = {
            'capture_date': datetime.now().isoformat(),
            'filter_applied': 'Service',
            'total_calls': len(search_api_calls),
            'total_requests': len(requests),
            'total_responses': len(responses),
            'calls': search_api_calls
        }
        
        filename = f'service_filter_api_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f'✅ Saved to: {filename}')
        print()
        
        # Summary
        print('=' * 80)
        print('📊 SUMMARY - Service Filter')
        print('=' * 80)
        print(f'Total /search requests: {len(requests)}')
        print(f'Total /search responses: {len(responses)}')
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
                    print(f'  {i}. data.count = {r["data_count"]}', end='')
                    if r.get('hits_returned', 0) > 0:
                        print(f' ({r["hits_returned"]} templates)', end='')
                    print()
            
            print()
            print(f'All count values: {counts}')
            print(f'Unique values: {sorted(set(counts), reverse=True)}')
        else:
            print('No count values captured')
    else:
        print()
        print('⚠️  No /search API calls captured')
        print('This might mean the filter did not trigger any searches')
    
    await page.close()
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(capture_service_filter())
