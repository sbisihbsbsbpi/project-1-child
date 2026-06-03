#!/usr/bin/env python3
"""
Get complete list of all 40 Service & Parts template IDs and names
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logo_addition_diagnostics.temp_logo_adding_FINAL import TempLogoAdditionFinalService, logger

async def get_all_templates():
    """Fetch all Service & Parts templates and display in table format"""
    
    print("=" * 120)
    print("📋 FETCHING ALL SERVICE & PARTS TEMPLATES")
    print("=" * 120)
    print()
    
    service = TempLogoAdditionFinalService()
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            page = await context.new_page()
            
            # Navigate to templates list
            url = "https://preprodapp.tekioncloud.com/templates/list"
            logger.info(f"📍 Navigating to: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)
            
            # Apply filter using the service method
            logger.info("🎯 Applying Service & Parts filter...")
            templates = await service._apply_filter_and_capture(
                page=page,
                departments=['Service', 'Parts'],
                base_url="https://preprodapp.tekioncloud.com"
            )
            
            print()
            print(f"✅ Captured {len(templates)} templates")
            print()
            print("=" * 120)
            print("📊 ALL TEMPLATE IDS AND NAMES")
            print("=" * 120)
            print()
            
            # Print table header
            print(f"{'#':<5} {'Template ID':<50} {'Template Name':<50} {'Departments'}")
            print("-" * 120)
            
            # Print all templates
            for idx, template in enumerate(templates, 1):
                template_id = template.get('templateId', 'NO_ID')
                name = template.get('name', 'Unknown')
                depts = ', '.join(template.get('departments', []))
                
                # Truncate long values for display
                name_display = name[:47] + "..." if len(name) > 50 else name
                id_display = template_id[:47] + "..." if len(template_id) > 50 else template_id
                
                print(f"{idx:<5} {id_display:<50} {name_display:<50} {depts}")
            
            print()
            print("=" * 120)
            print()
            
            # Save full data to JSON
            output_file = 'all_template_ids_complete.json'
            output_data = [
                {
                    'index': idx,
                    'templateId': t.get('templateId'),
                    'name': t.get('name'),
                    'departments': t.get('departments', [])
                }
                for idx, t in enumerate(templates, 1)
            ]
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"📄 Full data saved to: {output_file}")
            print()
            
            await page.close()
            
    except Exception as e:
        logger.exception(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(get_all_templates())
