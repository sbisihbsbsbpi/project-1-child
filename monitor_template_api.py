#!/usr/bin/env python3
"""
Real-time API monitor for templates list page
Run this and manually interact with the page to see API calls
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


async def monitor_api_calls():
    """Monitor API calls in real-time"""
    
    print('🔍 Real-Time Template API Monitor')
    print('=' * 80)
    print()
    print('This script will monitor API calls while you interact with the page.')
    print('Instructions:')
    print('  1. Script will open/connect to the templates list page')
    print('  2. You manually apply filters as needed')
    print('  3. Script logs all API calls in real-time')
    print('  4. Press Ctrl+C when done')
    print()
    input('Press Enter to start monitoring...')
    print()
    
    # Connect to existing browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9223')
    context = browser.contexts[0]
    
    # Find existing page or create new one
    pages = context.pages
    if pages:
        page = pages[0]
        print(f'✅ Using existing page: {page.url[:60]}...')
    else:
        page = await context.new_page()
        print('✅ Created new page')
    
    # Storage for API calls
    api_calls = []
    
    # Track requests
    async def handle_request(request):
        url = request.url
        
        # Filter for relevant APIs
        if any(k in url for k in ['/search', '/template', '/api/', 'graphql']):
            timestamp = datetime.now().strftime('%H:%M:%S')
            method = request.method
            
            # Extract endpoint
            path_parts = url.split('/')[-3:]
            endpoint = '/'.join(path_parts).split('?')[0]
            
            # Get request body if POST
            body_preview = None
            if request.method == 'POST' and request.post_data:
                try:
                    body = json.loads(request.post_data)
                    body_preview = json.dumps(body, indent=2)[:200]
                except:
                    body_preview = request.post_data[:200]
            
            call_info = {
                'timestamp': timestamp,
                'method': method,
                'url': url,
                'endpoint': endpoint,
                'request_body': body_preview
            }
            
            api_calls.append(call_info)
            
            print(f'[{timestamp}] → {method:4s} /{endpoint}')
            if body_preview and 'department' in body_preview.lower():
                print(f'           Body: {body_preview}')
    
    # Track responses
    async def handle_response(response):
        url = response.url
        
        if any(k in url for k in ['/search', '/template', '/api/', 'graphql']):
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = response.status
            
            path_parts = url.split('/')[-3:]
            endpoint = '/'.join(path_parts).split('?')[0]
            
            # Try to get response data
            response_preview = None
            if status == 200:
                try:
                    data = await response.json()
                    # Look for template count
                    if isinstance(data, dict):
                        if 'templates' in data:
                            count = len(data.get('templates', []))
                            response_preview = f'{count} templates'
                        elif 'total' in data:
                            response_preview = f"total: {data['total']}"
                        elif 'count' in data:
                            response_preview = f"count: {data['count']}"
                except:
                    pass
            
            print(f'[{timestamp}] ← {status} /{endpoint}', end='')
            if response_preview:
                print(f' ({response_preview})', end='')
            print()
    
    # Attach listeners
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print()
    print('✅ Monitoring started!')
    print('=' * 80)
    print()
    print('Now manually:')
    print('  1. Navigate to https://preprodapp.tekioncloud.com/templates/list (if not there)')
    print('  2. Apply department filters')
    print('  3. Watch the API calls below')
    print()
    print('Press Ctrl+C when done')
    print()
    print('-' * 80)
    print()
    
    # Keep monitoring
    try:
        await asyncio.sleep(3600)  # Monitor for 1 hour
    except KeyboardInterrupt:
        print('\n\n⏹️  Monitoring stopped')
    
    # Save results
    if api_calls:
        print()
        print('💾 Saving API calls...')
        
        output = {
            'monitoring_date': datetime.now().isoformat(),
            'total_calls': len(api_calls),
            'calls': api_calls
        }
        
        filename = f'api_calls_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f'✅ Saved {len(api_calls)} API calls to: {filename}')
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(monitor_api_calls())
