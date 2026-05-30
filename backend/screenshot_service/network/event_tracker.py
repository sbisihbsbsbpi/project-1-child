"""
Network event tracking for browser automation.

Extracted from screenshot_service.py (lines 647-759)
Part of Week 2 refactoring.

Provides event handlers for capturing:
- HTTP requests (XHR, Fetch, WebSocket, Document)
- Responses (with body capture)
- Failed requests
- Request timing
"""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


def create_network_event_handlers():
    """
    Create network event handlers for capturing network activity.
    
    Returns a dict with:
    - log_request: Handler for request events
    - log_response: Handler for response events
    - log_request_failed: Handler for failed requests
    - log_request_finished: Handler for finished requests
    - network_events: List to collect events
    - api_responses: List to collect full API responses
    - start_time: Timestamp when tracking started
    
    Usage:
        handlers = create_network_event_handlers()
        page.on("request", handlers['log_request'])
        page.on("response", handlers['log_response'])
        # ... capture screenshots ...
        return handlers['network_events']
    """
    network_events = []
    api_responses = []  # ✅ NEW: Store full API responses for Network tab
    start_time = asyncio.get_event_loop().time()
    
    def log_request(request):
        if request.resource_type in ['xhr', 'fetch', 'document', 'websocket']:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # Try to get request body/post data
            post_data = None
            try:
                post_data = request.post_data
            except Exception:  # ✅ FIXED: Specific exception instead of bare except
                pass  # POST data not available for all request types
            
            network_events.append({
                'event': 'request',
                'type': request.resource_type,
                'method': request.method,
                'url': request.url,
                'timestamp': elapsed,
                'headers': dict(request.headers),
                'post_data': post_data
            })
    
    async def log_response(response):
        if response.request.resource_type in ['xhr', 'fetch']:  # ✅ Focus on API calls
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # ✅ NEW: Capture response body for Network tab
            response_body = None
            response_json = None
            try:
                # ✅ FIX: Use body() instead of text() - more reliable with CDP
                body_bytes = await response.body()
                response_body = body_bytes.decode('utf-8', errors='ignore')
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response_body)
                except Exception:  # ✅ FIXED: Specific exception instead of bare except
                    pass  # Not JSON, keep as text
            except Exception as e:
                # ✅ IMPROVEMENT: Only log if it's not a common CDP timing issue
                error_msg = str(e)
                if "No data found" not in error_msg and "No resource with given identifier" not in error_msg:
                    logger.warning("   ⚠️ Could not capture response body: %s", e)
            
            # Store basic event
            network_events.append({
                'event': 'response',
                'type': response.request.resource_type,
                'status': response.status,
                'statusText': response.status_text,
                'url': response.url,
                'timestamp': elapsed,
                'headers': dict(response.headers) if response.request.resource_type == 'document' else {}
            })
            
            # ✅ NEW: Store full API response for Network tab
            if response_json is not None:  # Only store if we got JSON
                api_responses.append({
                    'id': f"api_{len(api_responses)}_{int(elapsed * 1000)}",
                    'method': response.request.method,
                    'url': response.url,
                    'status': response.status,
                    'statusText': response.status_text,
                    'timestamp': elapsed,
                    'request_headers': dict(response.request.headers),
                    'response_headers': dict(response.headers),
                    'request_body': response.request.post_data,
                    'response_body': response_body,
                    'response_json': response_json,
                    'captured_at': asyncio.get_event_loop().time()
                })
    
    def log_request_failed(request):
        elapsed = asyncio.get_event_loop().time() - start_time
        network_events.append({
            'event': 'failed',
            'type': request.resource_type,
            'method': request.method,
            'url': request.url,
            'timestamp': elapsed,
            'failure': request.failure
        })
    
    def log_request_finished(request):
        if request.resource_type in ['xhr', 'fetch', 'document']:
            elapsed = asyncio.get_event_loop().time() - start_time
            network_events.append({
                'event': 'finished',
                'type': request.resource_type,
                'url': request.url,
                'timestamp': elapsed
            })
    
    return {
        'log_request': log_request,
        'log_response': log_response,
        'log_request_failed': log_request_failed,
        'log_request_finished': log_request_finished,
        'network_events': network_events,
        'api_responses': api_responses,  # ✅ NEW: Full API responses for Network tab
        'start_time': start_time
    }


__all__ = ["create_network_event_handlers"]
