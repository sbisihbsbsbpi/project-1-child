#!/usr/bin/env python3
"""
Comprehensive Template Page Detection Script
Detects ALL elements, filters, and components on Tekion templates list page
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from template_page_detector import TemplatePageDetector
import json
from datetime import datetime


async def main():
    print("=" * 80)
    print("🔍 COMPREHENSIVE TEMPLATE PAGE DETECTION")
    print("=" * 80)
    print()
    
    detector = TemplatePageDetector()
    
    # Connect to existing browser via CDP
    print("🌐 Connecting to browser via CDP (localhost:9223)...")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser")
            print()
            
            # Run comprehensive detection
            results = await detector.detect_all(
                browser=browser,
                base_url="https://preprodapp.tekioncloud.com"
            )
            
            # Display Summary
            print("\n" + "=" * 80)
            print("📊 DETECTION SUMMARY")
            print("=" * 80)
            
            print(f"\n📄 PAGE INFO:")
            print(f"   Title: {results['page_info'].get('title', 'N/A')}")
            print(f"   URL: {results['page_info'].get('url', 'N/A')}")
            print(f"   Viewport: {results['page_info'].get('viewport', {})}")
            
            print(f"\n🎛️ FILTERS:")
            filters = results['filters']
            print(f"   Dropdowns: {len(filters.get('dropdowns', []))}")
            print(f"   Checkboxes: {len(filters.get('checkboxes', []))}")
            print(f"   Chips/Tags: {len(filters.get('chips', []))}")
            print(f"   Search Boxes: {len(filters.get('search_boxes', []))}")
            if filters.get('department_filter'):
                print(f"   Department: {filters['department_filter'].get('text', 'N/A')}")
            
            print(f"\n🖼️ UI ELEMENTS:")
            ui = results['ui_elements']
            print(f"   Buttons: {len(ui.get('buttons', []))}")
            print(f"   Links: {len(ui.get('links', []))}")
            print(f"   Tables: {len(ui.get('tables', []))}")
            print(f"   Images: {len(ui.get('images', []))}")
            
            print(f"\n📋 TEMPLATES:")
            templates = results['templates']
            print(f"   Total: {len(templates)}")
            if templates:
                print(f"   First template: {templates[0].get('name', 'Unknown')}")
                
                # Count by department
                dept_counts = {}
                for t in templates:
                    depts = ', '.join(sorted(t.get('departments', [])))
                    dept_counts[depts] = dept_counts.get(depts, 0) + 1
                
                print(f"\n   By Department:")
                for dept, count in sorted(dept_counts.items()):
                    print(f"     {dept}: {count}")
                
                # Count by type
                type_counts = {}
                for t in templates:
                    t_type = t.get('purposeSubType', 'Unknown')
                    type_counts[t_type] = type_counts.get(t_type, 0) + 1
                
                print(f"\n   By Type:")
                for t_type, count in sorted(type_counts.items()):
                    print(f"     {t_type}: {count}")
            
            print(f"\n🌐 API CALLS:")
            api = results['api_data']
            print(f"   Endpoints called: {len(api.get('endpoints', []))}")
            print(f"   HTTP Methods: {api.get('methods', {})}")
            print(f"   Domains: {len(api.get('domains', []))}")
            
            print(f"\n🖱️ INTERACTIONS:")
            interactions = results['interactions']
            print(f"   Clickable: {interactions.get('clickable', 0)}")
            print(f"   Editable: {interactions.get('editable', 0)}")
            print(f"   Draggable: {interactions.get('draggable', 0)}")
            
            print(f"\n📝 FORMS:")
            forms = results.get('forms', {})
            print(f"   Forms: {len(forms.get('forms', []))}")
            print(f"   Input fields: {len(forms.get('inputs', []))}")
            print(f"   Select dropdowns: {len(forms.get('selects', []))}")
            
            print(f"\n🧭 NAVIGATION:")
            nav = results.get('navigation', {})
            print(f"   Nav elements: {nav.get('nav_elements', 0)}")
            print(f"   Tabs: {nav.get('tabs', 0)}")
            print(f"   Pagination: {nav.get('pagination', 0)}")
            
            print(f"\n📐 LAYOUT:")
            layout = results.get('layout', {})
            print(f"   Containers: {layout.get('containers', 0)}")
            print(f"   Grids: {layout.get('grids', 0)}")
            print(f"   Flexbox: {layout.get('flexbox', 0)}")
            
            # Print detailed filters
            print("\n" + "=" * 80)
            print("🎛️ DETAILED FILTERS")
            print("=" * 80)
            
            if filters.get('checkboxes'):
                print("\n✅ Checkboxes:")
                for cb in filters['checkboxes'][:10]:  # Show first 10
                    status = "☑️ Checked" if cb.get('checked') else "⬜ Unchecked"
                    print(f"   {status}: {cb.get('label', 'N/A')}")
            
            if filters.get('chips'):
                print("\n🏷️ Active Filter Chips:")
                for chip in filters['chips']:
                    print(f"   {chip.get('text', 'N/A')}")
            
            # Print sample buttons
            print("\n" + "=" * 80)
            print("🔘 SAMPLE BUTTONS")
            print("=" * 80)
            
            for btn in ui.get('buttons', [])[:15]:  # Show first 15
                if btn.get('text'):
                    print(f"   {btn['text']}")
            
            print("\n" + "=" * 80)
            print("✅ DETECTION COMPLETE!")
            print("=" * 80)
            print(f"\n📄 Full results saved to JSON file")
            print(f"   Check: template_page_detection_*.json")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
