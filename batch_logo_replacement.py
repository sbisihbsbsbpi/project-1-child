#!/usr/bin/env python3
"""
Batch Logo Replacement - Sequential Processing
Processes multiple templates sequentially without publishing for verification
"""

import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from logo_replacement_automation import LogoReplacementConfig, LogoReplacementAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'batch_logo_replacement_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def get_templates_from_list_page():
    """Get first 10 templates from the template list page"""
    logger.info("=" * 80)
    logger.info("📋 FETCHING TEMPLATE LIST")
    logger.info("=" * 80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find template list page
    list_page = None
    for page in context.pages:
        if 'templates/list' in page.url:
            list_page = page
            break
    
    if not list_page:
        logger.error("❌ Template list page not found")
        logger.error("Please navigate to: https://preprodapp.tekioncloud.com/templates/list")
        await playwright.stop()
        return []
    
    logger.info(f"✅ Found template list page: {list_page.url}")
    
    # Get template links
    templates = await list_page.evaluate("""
        () => {
            const templates = [];
            
            // Find all template rows/links
            const links = Array.from(document.querySelectorAll('a[href*="templates/edit"]'));
            
            for (let i = 0; i < Math.min(10, links.length); i++) {
                const link = links[i];
                const href = link.href;
                const templateId = href.split('templates/edit/')[1]?.split('?')[0];
                
                if (templateId) {
                    // Find template name
                    let name = link.innerText || link.textContent || '';
                    
                    // Try to find name in parent/surrounding elements
                    if (!name || name.length < 3) {
                        const parent = link.closest('tr, div, li');
                        if (parent) {
                            name = parent.innerText.split('\\n')[0] || '';
                        }
                    }
                    
                    templates.push({
                        id: templateId,
                        url: href,
                        name: name.substring(0, 100)
                    });
                }
            }
            
            return templates;
        }
    """)
    
    logger.info(f"Found {len(templates)} templates")
    for idx, template in enumerate(templates, 1):
        logger.info(f"  {idx}. {template['name'][:50]} (ID: {template['id']})")
    
    await playwright.stop()
    
    return templates


async def open_template_tabs(templates):
    """Open template tabs in browser"""
    logger.info("=" * 80)
    logger.info("🌐 OPENING TEMPLATE TABS")
    logger.info("=" * 80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    opened_count = 0
    
    for idx, template in enumerate(templates, 1):
        logger.info(f"Opening template {idx}/{len(templates)}: {template['name'][:50]}")
        
        try:
            # Open in new tab
            new_page = await context.new_page()
            await new_page.goto(template['url'])
            
            # Wait for page to load
            await asyncio.sleep(2.0)
            
            logger.info(f"  ✅ Opened: {template['url']}")
            opened_count += 1
            
        except Exception as e:
            logger.error(f"  ❌ Failed to open: {e}")
    
    logger.info(f"✅ Opened {opened_count}/{len(templates)} template tabs")
    
    await playwright.stop()
    
    return opened_count


async def process_templates_sequentially(
    config: LogoReplacementConfig,
    max_templates: int = 10,
    publish: bool = False
):
    """Process templates sequentially"""
    logger.info("=" * 80)
    logger.info("🔄 SEQUENTIAL LOGO REPLACEMENT - BATCH MODE")
    logger.info("=" * 80)
    logger.info(f"Max templates: {max_templates}")
    logger.info(f"Publish changes: {publish}")
    logger.info("=" * 80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find all template edit pages
    template_pages = []
    for page in context.pages:
        if 'templates/edit' in page.url and 'templates/list' not in page.url:
            title = await page.title()
            template_pages.append({
                'page': page,
                'url': page.url,
                'title': title
            })
    
    template_pages = template_pages[:max_templates]
    
    logger.info(f"Found {len(template_pages)} template tabs to process")
    
    if len(template_pages) == 0:
        logger.error("❌ No template edit pages found!")
        await playwright.stop()
        return []
    
    results = []
    
    for idx, template_info in enumerate(template_pages, 1):
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"TEMPLATE {idx}/{len(template_pages)}")
        logger.info("=" * 80)
        logger.info(f"Title: {template_info['title']}")
        logger.info(f"URL: {template_info['url'][:100]}")
        logger.info("=" * 80)
        
        # Create automation for this specific page
        automation = LogoReplacementAutomation(config)
        automation.page = template_info['page']
        automation.playwright = playwright
        automation.browser = browser
        
        try:
            # Detect state
            state = await automation.detect_current_state()
            
            # Process based on state
            if state.get('hasNewLogo') and not state.get('hasOldLogo'):
                logger.info("✅ Template already has new logo, skipping")
                results.append({
                    'template': template_info['title'],
                    'status': 'already_updated',
                    'success': True
                })
                continue
            
            # Execute workflow
            success = await automation.execute_full_workflow(
                center_align=True,
                enlarge=True,
                target_width=160,
                publish=publish  # Don't publish for verification
            )
            
            results.append({
                'template': template_info['title'],
                'status': 'success' if success else 'failed',
                'success': success
            })
            
        except Exception as e:
            logger.error(f"❌ Error processing template: {e}")
            results.append({
                'template': template_info['title'],
                'status': 'error',
                'success': False,
                'error': str(e)
            })
    
    # Don't stop playwright - keep tabs open for verification
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 BATCH PROCESSING SUMMARY")
    logger.info("=" * 80)
    
    for idx, result in enumerate(results, 1):
        status_icon = "✅" if result['success'] else "❌"
        logger.info(f"{idx}. {status_icon} {result['template'][:50]} - {result['status']}")
    
    successful = sum(1 for r in results if r['success'])
    logger.info("")
    logger.info(f"Total: {successful}/{len(results)} successful")
    logger.info("")
    logger.info("🔍 VERIFICATION MODE: All tabs kept open for manual verification")
    logger.info("   Please review each template in the browser tabs")
    logger.info("")
    
    return results


async def main():
    """Main execution"""
    config = LogoReplacementConfig(
        old_logo_media_id="6a0c6722864813539e4da7ae",
        new_logo_media_id="6a19132b6697f36de6236fb1",
        new_logo_name="Tilton.png"
    )
    
    # Process templates
    results = await process_templates_sequentially(
        config=config,
        max_templates=10,
        publish=False  # Don't publish - verification mode
    )
    
    return results


if __name__ == "__main__":
    results = asyncio.run(main())
