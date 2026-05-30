"""
Screenshot filename generation utilities.

Extracted from screenshot_service.py (lines 6276-6434)
Part of Week 2 refactoring.

Provides intelligent filename generation with:
- PascalCase conversion
- Base URL subtraction
- Word transformation/removal
- Segment numbering for multi-part screenshots
"""

import re
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def to_pascal_case(text: str) -> str:
    """
    Convert text to PascalCase.
    
    Examples:
    - "autoPostingSettings" -> "AutoPostingSettings"
    - "auto-posting-settings" -> "AutoPostingSettings"
    - "auto_posting_settings" -> "AutoPostingSettings"
    - "_private" -> "Private" (removes leading symbols)
    - "-config" -> "Config" (removes leading symbols)
    """
    # First, handle camelCase by inserting space before capitals
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Split by separators (-, _, space)
    words = re.split(r'[-_\s]+', text)
    
    # Capitalize first letter of each word, filter out empty strings
    pascal_words = [word.capitalize() for word in words if word]
    
    result = ''.join(pascal_words)
    
    # Safety: Remove any leading non-alphanumeric characters
    result = re.sub(r'^[^a-zA-Z0-9]+', '', result)
    
    # If result is empty after cleanup, use default
    if not result:
        result = "Unnamed"
    
    return result


def generate_filename(
    url: str,
    base_url: str,
    words_to_remove: str,
    segment_index: int,
    total_segments: int
) -> str:
    """
    Generate filename based on base URL logic with PascalCase naming.
    
    Logic:
    - If base_url provided: subtract base_url from url, convert path to PascalCase filename
    - Remove specified words from path before conversion
    - Single segment: Module_Feature.png
    - Multiple segments: Module_Feature_001.png, Module_Feature_002.png, etc.
    - If no base_url: use domain + timestamp (old behavior)
    - Hash fragments (#): Removed by default, but preserved if '#' is in word transformations
    
    Examples:
    - base_url="https://example.com/", url="https://example.com/accounting/autoPostingSettings", segments=1
      -> "Accounting_AutoPostingSettings.png"
    - base_url="https://example.com/", url="https://example.com/dse-v2/scheduling/general", words_to_remove="dse-v2", segments=1
      -> "Scheduling_General.png"
    - base_url="https://example.com/", url="https://example.com/page#section", words_to_remove='[{"word":"#","replacement":" ","type":"space"}]'
      -> "Page_Section.png" (hash preserved and transformed)
    """
    if base_url and url.startswith(base_url):
        # Subtract base URL from full URL
        path = url[len(base_url):]
        
        # Remove leading/trailing slashes
        path = path.strip('/')
        
        # ✅ NEW: Check if '#' is in word transformations - if so, preserve hash fragments
        preserve_hash = False
        if words_to_remove:
            try:
                parsed = json.loads(words_to_remove)
                if isinstance(parsed, list):
                    # Check if any transformation targets '#'
                    preserve_hash = any(t.get("word") == "#" for t in parsed)
            except (json.JSONDecodeError, ValueError, TypeError):
                # Old format or invalid - check if '#' is in comma-separated string
                preserve_hash = '#' in words_to_remove
        
        # Remove fragments only if NOT preserving them
        if not preserve_hash and '#' in path:
            path = path.split('#')[0]
        
        # ✅ Apply word transformations (supports both old string format and new JSON array format)
        if words_to_remove:
            transformations = []
            
            # Try to parse as JSON array (new format)
            try:
                parsed = json.loads(words_to_remove)
                if isinstance(parsed, list):
                    # New format: [{"word": "dse-v2", "replacement": " ", "type": "space"}, ...]
                    transformations = parsed
                else:
                    # Fallback to old format
                    transformations = [{"word": w.strip(), "replacement": " ", "type": "space"}
                                     for w in words_to_remove.split(',') if w.strip()]
            except (json.JSONDecodeError, ValueError):
                # Old format: comma-separated string "dse-v2, .png, Accounting"
                transformations = [{"word": w.strip(), "replacement": " ", "type": "space"}
                                 for w in words_to_remove.split(',') if w.strip()]
            
            # Apply each transformation
            for transform in transformations:
                word = transform.get("word", "")
                replacement = transform.get("replacement", " ")
                
                if not word:
                    continue
                
                # Apply transformation (case-insensitive)
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                path = pattern.sub(replacement, path)
            
            # Clean up multiple slashes and spaces
            path = re.sub(r'/+', '/', path)  # Multiple slashes -> single slash
            path = re.sub(r'\s+', ' ', path)  # Multiple spaces -> single space
            path = path.strip('/ ')  # Remove leading/trailing slashes and spaces
        
        # If empty, use "Index"
        if not path:
            base_name = "Index"
        else:
            # Split path by / and convert each segment to PascalCase
            segments = path.split('/')
            pascal_segments = [to_pascal_case(segment) for segment in segments if segment]
            
            # Join with underscore
            base_name = '_'.join(pascal_segments)
        
        # Safety: Ensure base_name never starts with symbols
        base_name = re.sub(r'^[^a-zA-Z0-9]+', '', base_name)
        
        # If base_name is empty after cleanup, use default
        if not base_name:
            base_name = "Unnamed"
        
        # Generate filename based on segment count
        if total_segments == 1:
            # Single screenshot
            filename = f"{base_name}.png"
        else:
            # Multiple screenshots - add sequence number
            filename = f"{base_name}_{segment_index:03d}.png"
    else:
        # No base URL or URL doesn't match - use old behavior (domain + timestamp)
        domain = url.split("//")[1].split("/")[0].replace(":", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if total_segments == 1:
            filename = f"{domain}_{timestamp}.png"
        else:
            filename = f"{domain}_{segment_index:03d}_{timestamp}.png"
    
    return filename


__all__ = ["to_pascal_case", "generate_filename"]
