#!/usr/bin/env python3
"""
Logo Updater with Proper Tab Management
Demonstrates single tab reuse pattern for updating logos across multiple templates
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


class TabManager:
    """Manages a single reusable tab for template updates"""
    
    def __init__(self, context):
        self.context = context
        self.working_tab = None
        self.initial_tab_count = len(context.pages)
    
    async def get_or_create_working_tab(self):
        """Find existing Tekion tab or create new one"""
        
        if self.working_tab and not self.working_tab.is_closed():
            return self.working_tab
        
        # Look for existing Tekion template tab
        for page in self.context.pages:
            if 'tekioncloud.com/templates' in page.url:
                self.working_tab = page
                print("✅ Found and reusing existing Tekion tab")
                return self.working_tab
        
        # Create new tab if none found
        self.working_tab = await self.context.new_page()
        print("✅ Created new working tab")
        return self.working_tab
    
    async def cleanup(self):
        """Close working tab and verify no tab leaks"""
        
        if self.working_tab and not self.working_tab.is_closed():
            await self.working_tab.close()
            print("✅ Closed working tab")
        
        final_tab_count = len(self.context.pages)
        leaked_tabs = final_tab_count - self.initial_tab_count
        
        if leaked_tabs > 0:
            print(f"⚠️  Warning: {leaked_tabs} tab(s) leaked!")
        else:
            print(f"✅ No tab leaks - clean exit")
        
        return leaked_tabs
    
    def get_tab_count(self):
        """Get current number of open tabs"""
        return len(self.context.pages)


async def find_template_logo(page):
    """Find the actual template logo (not UI elements)"""
    
    # Load ignore patterns
    with open('logo_ignore_list.json') as f:
        ignore_list = json.load(f)
    
    logo_info = await page.evaluate("""
        (ignorePatterns) => {
            function isIgnored(el) {
                if (ignorePatterns.ids.includes(el.id)) return true;
                const classes = el.className || '';
                for (const pattern of ignorePatterns.class_names) {
                    if (classes.includes(pattern)) return true;
                }
                for (const parentSelector of ignorePatterns.parent_selectors) {
                    if (el.closest(parentSelector)) return true;
                }
                return false;
            }
            
            const allImgs = document.querySelectorAll('img');
            
            for (const img of allImgs) {
                if (isIgnored(img)) continue;
                
                const src = img.src || '';
                
                // Look for S3 images or logo-related images
                if (src.includes('amazonaws.com') || 
                    src.toLowerCase().includes('logo') ||
                    src.toLowerCase().includes('nucar') ||
                    src.toLowerCase().includes('tilton')) {
                    
                    return {
                        found: true,
                        src: src,
                        alt: img.alt || '',
                        width: img.getBoundingClientRect().width,
                        height: img.getBoundingClientRect().height,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight
                    };
                }
            }
            
            return { found: false };
        }
    """, ignore_list['ignore_patterns'])
    
    return logo_info


async def replace_logo(page, old_logo_url, new_logo_url):
    """Replace the logo in the template"""
    
    result = await page.evaluate("""
        ({ oldUrl, newUrl }) => {
            const allImgs = document.querySelectorAll('img');
            
            for (const img of allImgs) {
                if (img.src === oldUrl) {
                    img.src = newUrl;
                    return { success: true, message: 'Logo replaced' };
                }
            }
            
            return { success: false, message: 'Logo not found' };
        }
    """, {"oldUrl": old_logo_url, "newUrl": new_logo_url})
    
    return result


async def batch_update_logos(template_ids, old_logo_url, new_logo_url):
    """
    Update logos across multiple templates using single tab reuse pattern
    """
    
    print("=" * 100)
    print("🎨 BATCH LOGO UPDATE - WITH TAB MANAGEMENT")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        # Connect to existing browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Initialize tab manager
        tab_mgr = TabManager(context)
        
        print(f"\n📊 Initial state:")
        print(f"   Total tabs open: {tab_mgr.get_tab_count()}")
        print(f"   Templates to process: {len(template_ids)}")
        print()
        
        # Get working tab
        working_tab = await tab_mgr.get_or_create_working_tab()
        await working_tab.bring_to_front()
        
        results = []
        
        # Process each template using the SAME tab
        for idx, template_id in enumerate(template_ids, 1):
            print("=" * 100)
            print(f"[{idx}/{len(template_ids)}] Processing: {template_id}")
            print("=" * 100)
            
            try:
                # Navigate to template (REUSING same tab)
                print(f"   Navigating to template...")
                await working_tab.goto(
                    f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}",
                    wait_until='networkidle',
                    timeout=30000
                )
                
                print(f"   Current tabs open: {tab_mgr.get_tab_count()}")  # Should stay constant!
                
                # Find logo
                print(f"   Searching for logo...")
                logo_info = await find_template_logo(working_tab)
                
                if logo_info['found']:
                    print(f"   ✅ Logo found: {logo_info['src'][:80]}")
                    print(f"   Size: {logo_info['width']:.0f}x{logo_info['height']:.0f}px")
                    
                    # Replace logo
                    print(f"   Replacing logo...")
                    replace_result = await replace_logo(working_tab, logo_info['src'], new_logo_url)
                    
                    if replace_result['success']:
                        print(f"   ✅ Logo replaced successfully")
                        results.append({'id': template_id, 'status': 'success'})
                    else:
                        print(f"   ❌ Failed to replace logo")
                        results.append({'id': template_id, 'status': 'replace_failed'})
                else:
                    print(f"   ⚠️  No logo found in template")
                    results.append({'id': template_id, 'status': 'no_logo'})
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({'id': template_id, 'status': 'error', 'error': str(e)})
        
        # Cleanup
        print("\n" + "=" * 100)
        print("🧹 CLEANUP")
        print("=" * 100)
        leaked = await tab_mgr.cleanup()
        
        # Summary
        print("\n" + "=" * 100)
        print("📊 SUMMARY")
        print("=" * 100)
        
        success = sum(1 for r in results if r['status'] == 'success')
        no_logo = sum(1 for r in results if r['status'] == 'no_logo')
        errors = sum(1 for r in results if r['status'] in ['error', 'replace_failed'])
        
        print(f"\nTotal processed: {len(template_ids)}")
        print(f"  ✅ Success: {success}")
        print(f"  ⚠️  No logo: {no_logo}")
        print(f"  ❌ Errors: {errors}")
        print(f"\nTab management:")
        print(f"  Tabs leaked: {leaked}")
        print(f"  Status: {'✅ Clean' if leaked == 0 else '⚠️  Leaked tabs!'}")
        
        return results


if __name__ == "__main__":
    # Example usage
    test_templates = [
        "CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS",
        "CPRA_REQUEST_COMPLETION_DATA_CORRECTION",
        "CPRA_REQUEST_COMPLETION_DATA_EXPORT"
    ]
    
    old_logo = "https://example.com/nucar-logo.png"
    new_logo = "https://example.com/tilton-logo.png"
    
    # Run batch update
    asyncio.run(batch_update_logos(test_templates, old_logo, new_logo))
