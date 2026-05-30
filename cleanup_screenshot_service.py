#!/usr/bin/env python3
"""
Cleanup Script for Screenshot Service
Removes unused features: Camoufox, Stealth, Network Tracking, Form Automation, Auth
Keeps: CDP, Segmented Capture, Auto Expand Dropdowns, Batch Processing
"""

import re

def cleanup_screenshot_service(input_file, output_file):
    """Remove unused features from screenshot_service.py"""
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    print("📊 Original file: {} lines".format(len(content.splitlines())))
    
    # Step 1: Remove Camoufox imports
    print("🗑️  Removing Camoufox imports...")
    content = re.sub(r'# Try to import Camoufox.*?CAMOUFOX_AVAILABLE = False\n', 
                     '', content, flags=re.DOTALL)
    
    # Step 2: Remove Patchright/Rebrowser imports (keep only standard Playwright)
    print("🗑️  Removing Patchright/Rebrowser imports...")
    content = re.sub(r'# ✅ Try to import Patchright.*?print\("   💡 For better stealth.*?\)\n',
                     'from playwright.async_api import async_playwright, Browser, Page, BrowserContext\n\n',
                     content, flags=re.DOTALL)
    
    # Step 3: Remove stealth-related imports
    print("🗑️  Removing stealth imports...")
    lines_to_remove = [
        'from playwright_stealth',
        'import ssl',
        'ssl._create_default_https_context'
    ]
    lines = content.splitlines()
    lines = [line for line in lines if not any(remove in line for remove in lines_to_remove)]
    content = '\n'.join(lines)
    
    # Step 4: Remove method definitions
    print("🗑️  Removing unused methods...")
    methods_to_remove = [
        '_apply_canvas_webgl_randomization',
        '_apply_cdp_detection_bypass',
        '_apply_audio_context_randomization',
        '_apply_behavioral_randomization',
        '_apply_all_stealth_enhancements',
        '_simulate_human_behavior',
        '_simulate_realistic_mouse_movement',
        '_simulate_realistic_scrolling',
        '_get_stealth_config',
        '_disable_navigator_webdriver',
        '_create_network_event_handlers',
        '_convert_network_events_to_curl',
        '_click_active_forms',
        '_capture_form_screenshots',
        '_click_elements_by_text',
        'save_auth_state',
        '_get_random_user_agent',
        '_get_random_viewport',
        '_add_random_delay',
        '_detect_browser_mode',
        '_load_url_click_config',
        '_find_url_config'
    ]
    
    for method in methods_to_remove:
        # Remove method definition and its body
        pattern = rf'    (async )?def {method}\(.*?\n(?:        .*\n)*?(?=    (async )?def |class |\Z)'
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    print("📊 Cleaned file: {} lines".format(len(content.splitlines())))
    print("📊 Removed: {} lines".format(len(open(input_file).readlines()) - len(content.splitlines())))
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Cleaned file saved to: {output_file}")

if __name__ == "__main__":
    cleanup_screenshot_service(
        'services/screenshot-service/screenshot_service.py.backup',
        'services/screenshot-service/screenshot_service_cleaned.py'
    )

