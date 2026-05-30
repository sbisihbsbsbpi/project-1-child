#!/usr/bin/env python3
"""
Logo Addition Integration with Department Filter
=================================================

This module integrates the department filter automation with the logo addition service.
It allows you to:
1. Filter templates by department
2. Get the exact list of templates from API
3. Add logos to those specific templates

Author: Automation Team
Status: NEW - Integrating filter + logo addition
Created: 2026-05-29
"""

import asyncio
import sys
import os
from typing import List, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from department_filter_automation import change_department_filter, generate_edit_url


async def get_templates_by_department(
    departments: List[str],
    cdp_url: str = "http://localhost:9223"
) -> Dict:
    """
    Get templates for specific departments using API monitoring.
    
    Args:
        departments: List of departments to filter (e.g., ['Service', 'Parts'])
        cdp_url: Chrome DevTools Protocol URL
        
    Returns:
        dict: {
            'templates': List of template objects,
            'count': Total count,
            'departments': Departments selected,
            'edit_urls': List of edit URLs
        }
    """
    
    print("=" * 100)
    print("🔍 FETCHING TEMPLATES BY DEPARTMENT")
    print("=" * 100)
    print(f"Departments: {', '.join(departments)}")
    print("=" * 100)
    print()
    
    # Map to determine what to unselect
    all_departments = ['Sales', 'Service', 'Parts']
    to_unselect = [d for d in all_departments if d not in departments]
    
    # Use the department filter automation with API verification
    result = await change_department_filter(
        departments_to_select=departments,
        departments_to_unselect=to_unselect,
        wait_seconds=15,
        cdp_url=cdp_url
    )
    
    # Extract template data from API monitoring result
    # The function returns api_data directly with 'before' and 'after' keys
    if result and result.get('after'):
        after_data = result['after']
        templates = after_data.get('templates', [])
        
        # Generate edit URLs for all templates
        edit_urls = []
        for template in templates:
            template_id = template.get('templateId')
            if template_id:
                url = generate_edit_url(template_id)
                edit_urls.append({
                    'templateId': template_id,
                    'name': template.get('name'),
                    'url': url,
                    'departments': template.get('departments', [])
                })
        
        return {
            'templates': templates,
            'count': len(templates),
            'departments': departments,
            'edit_urls': edit_urls,
            'success': True
        }
    else:
        return {
            'templates': [],
            'count': 0,
            'departments': departments,
            'edit_urls': [],
            'success': False,
            'error': 'Failed to get API data'
        }


async def add_logos_to_filtered_templates(
    departments: List[str],
    logo_media_id: str = "6a19132b6697f36de6236fb1",
    logo_width: int = 160,
    max_templates: Optional[int] = None,
    cdp_url: str = "http://localhost:9223",
    base_url: str = "https://preprodapp.tekioncloud.com",
    keep_tabs_open: bool = True
):
    """
    Filter templates by department and add logos to them.

    Args:
        departments: List of departments to filter
        logo_media_id: Media ID of the logo to add
        logo_width: Width of the logo in pixels
        max_templates: Maximum number of templates to process (None = all)
        cdp_url: Chrome DevTools Protocol URL
        base_url: Base URL of the Tekion application
        keep_tabs_open: Whether to keep browser tabs open after processing

    Returns:
        dict: Results of logo addition operation
    """

    from template_logo_addition_service import TemplateLogoAdditionService
    import uuid

    print("=" * 100)
    print("🎨 LOGO ADDITION WITH DEPARTMENT FILTER")
    print("=" * 100)
    print(f"Target Departments: {', '.join(departments)}")
    print(f"Logo Media ID: {logo_media_id}")
    print(f"Logo Width: {logo_width}px")
    print("=" * 100)
    print()

    # Step 1: Get templates by department
    print("STEP 1: Fetching templates...")
    print("-" * 100)

    template_data = await get_templates_by_department(departments, cdp_url)

    if not template_data['success']:
        print("❌ Failed to fetch templates")
        return template_data

    templates = template_data['templates']
    print(f"✅ Found {len(templates)} templates")
    print()

    # Apply limit if specified
    if max_templates and max_templates < len(templates):
        templates = templates[:max_templates]
        print(f"⚠️  Limiting to first {max_templates} templates")
        print()

    # Step 2: Display templates that will be processed
    print("STEP 2: Templates to process:")
    print("-" * 100)
    for i, template in enumerate(templates, 1):
        template_id = template.get('templateId')
        name = template.get('name')
        depts = ', '.join(template.get('departments', []))
        url = generate_edit_url(template_id)

        print(f"{i:2d}. {name[:60]:<60}")
        print(f"    Template ID: {template_id}")
        print(f"    Edit URL: {url}")
        print(f"    Departments: {depts}")
        print()

    print("=" * 100)
    print(f"📊 Total: {len(templates)} templates will be processed")
    print("=" * 100)
    print()

    # Step 3: Initialize logo addition service
    print("STEP 3: Adding logos to templates...")
    print("-" * 100)
    print()

    service = TemplateLogoAdditionService()
    job_id = f"dept_filter_{uuid.uuid4().hex[:8]}"

    # Create job with the filtered templates
    job = service.create_job(
        job_id=job_id,
        base_url=base_url,
        max_rows=len(templates),
        custom_limit=len(templates),
        keep_tabs_open=keep_tabs_open,
        logo_media_id=logo_media_id,
        logo_width=logo_width
    )

    print(f"🆔 Job ID: {job_id}")
    print()

    # Process the templates directly (skip API fetching since we already have them)
    try:
        # We'll process templates manually using the service
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()

            service.add_log(job_id, "🚀 Starting logo addition to filtered templates", "info")
            service.jobs[job_id]['status'] = 'running'

            # Process each template
            for idx, template in enumerate(templates, 1):
                await service._process_template(job_id, context, template, idx, len(templates))

                # Update progress
                service.jobs[job_id]['processed'] = idx

            service.jobs[job_id]['status'] = 'completed'
            service.add_log(job_id, "", "info")
            service.add_log(job_id, "=" * 80, "info")
            service.add_log(job_id, "✅ All templates processed!", "success")
            service.add_log(job_id, f"   Total: {service.jobs[job_id]['processed']}", "info")
            service.add_log(job_id, f"   Successful: {service.jobs[job_id]['successful']}", "success")
            service.add_log(job_id, f"   Failed: {service.jobs[job_id]['failed']}", "error" if service.jobs[job_id]['failed'] > 0 else "info")
            service.add_log(job_id, "=" * 80, "info")

        # Get final results
        final_job = service.jobs[job_id]

        return {
            'success': True,
            'job_id': job_id,
            'departments': departments,
            'templates_found': len(template_data['templates']),
            'templates_processed': final_job['processed'],
            'successful': final_job['successful'],
            'failed': final_job['failed'],
            'results': final_job['results'],
            'logs': final_job['logs']
        }

    except Exception as e:
        service.jobs[job_id]['status'] = 'failed'
        service.add_log(job_id, f"❌ Error: {str(e)}", "error")

        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'job_id': job_id,
            'error': str(e),
            'logs': service.jobs[job_id]['logs']
        }


async def main():
    """Example usage"""

    print("=" * 100)
    print("🎨 LOGO ADDITION WITH DEPARTMENT FILTER - FULL INTEGRATION")
    print("=" * 100)
    print()
    print("This will:")
    print("  1. Filter templates by department (Service & Parts)")
    print("  2. Get exact template list from API")
    print("  3. Add logos to each template")
    print()

    # Confirm before proceeding
    print("⚠️  WARNING: This will modify templates!")
    print()
    response = input("Continue? (y/N): ")

    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    print()
    print("=" * 100)
    print("🚀 STARTING LOGO ADDITION")
    print("=" * 100)
    print()

    # Add logos to Service & Parts templates
    result = await add_logos_to_filtered_templates(
        departments=['Service', 'Parts'],
        logo_media_id="6a19132b6697f36de6236fb1",  # Tilton.png
        logo_width=160,
        max_templates=3,  # Limit to 3 for safety
        keep_tabs_open=False  # Close tabs after processing
    )

    print()
    print("=" * 100)
    print("📊 FINAL RESULTS")
    print("=" * 100)

    if result.get('success'):
        print(f"✅ Job ID: {result.get('job_id')}")
        print(f"🔍 Departments: {', '.join(result.get('departments', []))}")
        print(f"📋 Templates found: {result.get('templates_found')}")
        print(f"⚙️  Templates processed: {result.get('templates_processed')}")
        print(f"✅ Successful: {result.get('successful')}")
        print(f"❌ Failed: {result.get('failed')}")
        print()

        # Show detailed results
        if result.get('results'):
            print("=" * 100)
            print("📝 DETAILED RESULTS")
            print("=" * 100)
            for r in result['results']:
                status = "✅" if r['success'] else "❌"
                print(f"{status} {r['name']}")
                print(f"   Template ID: {r['templateId']}")
                if r['success']:
                    print(f"   Message: {r['message']}")
                else:
                    print(f"   Error: {r.get('error', 'Unknown')}")
                print()
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")

    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
