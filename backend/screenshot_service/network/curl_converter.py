"""
Network event to cURL command converter.

Extracted from screenshot_service.py (lines 609-645)
Part of Week 2 refactoring.

Converts captured network events to cURL commands for:
- API replay
- Debugging
- Documentation
"""

import logging

logger = logging.getLogger(__name__)


def convert_network_events_to_curl(network_events: list) -> list:
    """
    Convert network events to cURL commands.
    
    Returns list of cURL command strings.
    
    Args:
        network_events: List of network event dictionaries
        
    Returns:
        List of cURL command strings
        
    Example:
        events = [{"event": "request", "type": "xhr", "url": "https://api.example.com/data", ...}]
        curls = convert_network_events_to_curl(events)
        # Returns: ["curl -X GET -H 'Accept: application/json' 'https://api.example.com/data'"]
    """
    curl_commands = []
    
    # Filter for request events only
    requests = [e for e in network_events if e.get('event') == 'request' and e.get('type') in ['xhr', 'fetch']]
    
    for req in requests:
        url = req.get('url', '')
        method = req.get('method', 'GET')
        headers = req.get('headers', {})
        post_data = req.get('post_data', '')
        
        # Build cURL command
        curl = f"curl -X {method}"
        
        # Add headers
        for key, value in headers.items():
            # Skip certain headers that shouldn't be in cURL
            if key.lower() not in ['host', 'content-length', 'connection', 'accept-encoding']:
                curl += f" -H '{key}: {value}'"
        
        # Add data if POST/PUT/PATCH
        if post_data and method in ['POST', 'PUT', 'PATCH']:
            # Escape single quotes in data
            escaped_data = post_data.replace("'", "'\\''")
            curl += f" -d '{escaped_data}'"
        
        # Add URL
        curl += f" '{url}'"
        
        curl_commands.append(curl)
    
    return curl_commands


__all__ = ["convert_network_events_to_curl"]
