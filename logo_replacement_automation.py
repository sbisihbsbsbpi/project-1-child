#!/usr/bin/env python3
"""
Logo Replacement Automation Script
Automates the process of detecting and replacing logos in Tekion templates
"""

import asyncio
import logging
import json
from datetime import datetime
from playwright.async_api import async_playwright
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logo_replacement_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LogoReplacementConfig:
    """Configuration for logo replacement"""
    
    def __init__(
        self,
        old_logo_media_id: str,
        new_logo_media_id: str,
        new_logo_name: str,
        chrome_debug_port: int = 9223,
        template_url_pattern: str = "templates/edit"
    ):
        self.old_logo_media_id = old_logo_media_id
        self.new_logo_media_id = new_logo_media_id
        self.new_logo_name = new_logo_name
        self.chrome_debug_port = chrome_debug_port
        self.template_url_pattern = template_url_pattern
        
        logger.info("=" * 80)
        logger.info("Configuration initialized:")
        logger.info(f"  Old logo media ID: {old_logo_media_id}")
        logger.info(f"  New logo media ID: {new_logo_media_id}")
        logger.info(f"  New logo name: {new_logo_name}")
        logger.info(f"  Chrome debug port: {chrome_debug_port}")
        logger.info("=" * 80)


class LogoReplacementAutomation:
    """Main automation class for logo replacement"""
    
    def __init__(self, config: LogoReplacementConfig):
        self.config = config
        self.playwright = None
        self.browser = None
        self.page = None
        
    async def connect(self) -> bool:
        """Connect to browser via CDP"""
        try:
            logger.info("Connecting to browser...")
            self.playwright = await async_playwright().start()
            
            cdp_url = f"http://localhost:{self.config.chrome_debug_port}"
            logger.info(f"CDP URL: {cdp_url}")
            
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            logger.info(f"✅ Connected to browser")
            
            # Find template page
            context = self.browser.contexts[0]
            pages = context.pages
            
            logger.info(f"Found {len(pages)} open tabs")
            
            for idx, p in enumerate(pages, 1):
                url = p.url
                title = await p.title()
                logger.info(f"  Tab {idx}: {title} - {url[:80]}")
                
                if self.config.template_url_pattern in url:
                    self.page = p
                    logger.info(f"✅ Selected template tab: {title}")
                    break
            
            if not self.page:
                logger.error("❌ Template tab not found")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def detect_current_state(self) -> Dict:
        """Detect current logo state in template"""
        logger.info("=" * 80)
        logger.info("DETECTING CURRENT TEMPLATE STATE")
        logger.info("=" * 80)
        
        try:
            result = await self.page.evaluate(f"""
                () => {{
                    const OLD_ID = "{self.config.old_logo_media_id}";
                    const NEW_ID = "{self.config.new_logo_media_id}";
                    
                    const images = Array.from(document.querySelectorAll('img'));
                    const allImages = images.map((img, idx) => {{
                        const rect = img.getBoundingClientRect();
                        const src = img.src || '';
                        
                        return {{
                            index: idx,
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            position: {{
                                top: Math.round(rect.top),
                                left: Math.round(rect.left)
                            }},
                            hasOldLogo: src.includes(OLD_ID),
                            hasNewLogo: src.includes(NEW_ID),
                            mediaId: src.match(/([a-f0-9]{{24}})/) ? src.match(/([a-f0-9]{{24}})/)[1] : null
                        }};
                    }}).filter(img => img.width > 20 && img.height > 10);
                    
                    return {{
                        totalImages: allImages.length,
                        hasOldLogo: allImages.some(img => img.hasOldLogo),
                        hasNewLogo: allImages.some(img => img.hasNewLogo),
                        images: allImages
                    }};
                }}
            """)
            
            logger.info(f"Total images in template: {result['totalImages']}")
            logger.info(f"Old logo present: {result['hasOldLogo']}")
            logger.info(f"New logo present: {result['hasNewLogo']}")
            
            for img in result['images']:
                status = ""
                if img['hasOldLogo']:
                    status = " ← OLD LOGO (NEEDS REPLACEMENT)"
                elif img['hasNewLogo']:
                    status = " ← NEW LOGO (ALREADY UPDATED)"
                
                logger.info(
                    f"  Image {img['index']}: {img['width']}x{img['height']}px "
                    f"at ({img['position']['left']}, {img['position']['top']}){status}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Detection failed: {e}")
            return {}

    async def replace_logo(self) -> bool:
        """Execute the complete logo replacement workflow"""
        logger.info("=" * 80)
        logger.info("STARTING LOGO REPLACEMENT WORKFLOW")
        logger.info("=" * 80)

        try:
            # Step 1: Find and mark old logo
            logger.info("Step 1: Finding old logo...")

            logo_found = await self.page.evaluate(f"""
                () => {{
                    const OLD_ID = "{self.config.old_logo_media_id}";
                    const images = Array.from(document.querySelectorAll('img'));

                    for (const img of images) {{
                        if (img.src.includes(OLD_ID)) {{
                            img.setAttribute('data-old-logo', 'true');
                            img.style.outline = '5px solid red';

                            // Find container
                            let container = img.parentElement;
                            for (let i = 0; i < 5; i++) {{
                                if (!container) break;
                                const cls = container.className || '';
                                if (cls.includes('resizable') || cls.includes('imageComponent')) {{
                                    container.setAttribute('data-logo-container', 'true');
                                    container.style.outline = '5px solid orange';
                                    return true;
                                }}
                                container = container.parentElement;
                            }}

                            if (img.parentElement) {{
                                img.parentElement.setAttribute('data-logo-container', 'true');
                                img.parentElement.style.outline = '5px solid orange';
                                return true;
                            }}
                        }}
                    }}
                    return false;
                }}
            """)

            if not logo_found:
                logger.error("❌ Old logo not found in template")
                return False

            logger.info("✅ Old logo found and marked")

            # Step 2: Hover to reveal toolbar
            logger.info("Step 2: Hovering to reveal toolbar...")
            container = await self.page.query_selector('[data-logo-container="true"]')

            if not container:
                logger.error("❌ Logo container not found")
                return False

            await container.hover()
            await asyncio.sleep(1.5)
            logger.info("✅ Toolbar revealed")

            # Step 3: Click Change Image icon
            logger.info("Step 3: Clicking 'Change Image' icon...")

            change_clicked = await self.page.evaluate("""
                () => {
                    const btn = document.querySelector('[title="Change Image"]') ||
                               document.querySelector('[aria-label="icon-switch"]');
                    if (btn) {
                        btn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if not change_clicked:
                logger.error("❌ Change Image button not found")
                return False

            logger.info("✅ Change Image clicked")
            await asyncio.sleep(2.5)

            # Step 4: Verify Insert Files modal opened
            logger.info("Step 4: Verifying Insert Files modal...")

            modal_open = await self.page.evaluate("""
                () => {
                    return document.body.innerText.includes('Insert Files');
                }
            """)

            if not modal_open:
                logger.error("❌ Insert Files modal did not open")
                return False

            logger.info("✅ Insert Files modal is open")

            # Step 5: Find and click new logo
            logger.info(f"Step 5: Finding and clicking {self.config.new_logo_name}...")

            new_logo_clicked = await self.page.evaluate(f"""
                () => {{
                    const NEW_ID = "{self.config.new_logo_media_id}";
                    const images = Array.from(document.querySelectorAll('img'));

                    for (const img of images) {{
                        if (img.src.includes(NEW_ID)) {{
                            const parent = img.closest('div[class]');
                            if (parent) parent.click();
                            else img.click();
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)

            if not new_logo_clicked:
                logger.error(f"❌ {self.config.new_logo_name} not found in modal")
                return False

            logger.info(f"✅ Clicked {self.config.new_logo_name}")
            await asyncio.sleep(1.0)

            # Step 6: Click Insert button
            logger.info("Step 6: Clicking Insert button...")

            insert_clicked = await self.page.evaluate("""
                () => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    for (const btn of btns) {
                        if (btn.innerText === 'Insert') {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)

            if not insert_clicked:
                logger.error("❌ Insert button not found")
                return False

            logger.info("✅ Insert button clicked")
            await asyncio.sleep(2.0)

            # Step 7: Verify replacement
            logger.info("Step 7: Verifying logo replacement...")

            verification = await self.page.evaluate(f"""
                () => {{
                    const OLD_ID = "{self.config.old_logo_media_id}";
                    const NEW_ID = "{self.config.new_logo_media_id}";

                    const images = Array.from(document.querySelectorAll('img'));
                    const logos = images.filter(img => {{
                        const r = img.getBoundingClientRect();
                        return r.width > 50 && r.width < 300 && r.height > 10 && r.height < 150;
                    }});

                    return {{
                        hasNewLogo: logos.some(img => img.src.includes(NEW_ID)),
                        hasOldLogo: logos.some(img => img.src.includes(OLD_ID))
                    }};
                }}
            """)

            if verification['hasNewLogo'] and not verification['hasOldLogo']:
                logger.info("✅ Logo replacement successful!")
                logger.info(f"   Old logo removed, {self.config.new_logo_name} added")
                return True
            else:
                logger.warning("⚠️  Logo replacement verification inconclusive")
                logger.warning(f"   Has new logo: {verification['hasNewLogo']}")
                logger.warning(f"   Has old logo: {verification['hasOldLogo']}")
                return False

        except Exception as e:
            logger.error(f"❌ Logo replacement failed: {e}")
            return False

    async def center_align_logo(self) -> bool:
        """Center align the logo"""
        logger.info("=" * 80)
        logger.info("CENTER ALIGNING LOGO")
        logger.info("=" * 80)

        try:
            # Find new logo
            logo_found = await self.page.evaluate(f"""
                () => {{
                    const NEW_ID = "{self.config.new_logo_media_id}";
                    const images = Array.from(document.querySelectorAll('img'));

                    for (const img of images) {{
                        if (img.src.includes(NEW_ID)) {{
                            const rect = img.getBoundingClientRect();
                            if (rect.width < 200) {{
                                img.setAttribute('data-new-logo', 'true');

                                let container = img.parentElement;
                                for (let i = 0; i < 5; i++) {{
                                    if (!container) break;
                                    if ((container.className || '').includes('resizable')) {{
                                        container.setAttribute('data-new-logo-container', 'true');
                                        return true;
                                    }}
                                    container = container.parentElement;
                                }}

                                if (img.parentElement) {{
                                    img.parentElement.setAttribute('data-new-logo-container', 'true');
                                    return true;
                                }}
                            }}
                        }}
                    }}
                    return false;
                }}
            """)

            if not logo_found:
                logger.error("❌ New logo not found for alignment")
                return False

            logger.info("✅ New logo found")

            # Hover to reveal toolbar
            logger.info("Hovering to reveal alignment toolbar...")
            container = await self.page.query_selector('[data-new-logo-container="true"]')
            await container.hover()
            await asyncio.sleep(1.5)

            # Click center align
            logger.info("Clicking Center Align...")
            center_clicked = await self.page.evaluate("""
                () => {
                    const centerBtn = document.querySelector('[title="Center Align"]') ||
                                     document.querySelector('[aria-label="icon-center-align"]');
                    if (centerBtn) {
                        centerBtn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if center_clicked:
                logger.info("✅ Logo center aligned")
                await asyncio.sleep(1.0)
                return True
            else:
                logger.warning("⚠️  Center Align button not found")
                return False

        except Exception as e:
            logger.error(f"❌ Center alignment failed: {e}")
            return False

    async def enlarge_logo(self, target_width: int = 160) -> bool:
        """Enlarge the logo to specified width"""
        logger.info("=" * 80)
        logger.info(f"ENLARGING LOGO TO {target_width}px WIDTH")
        logger.info("=" * 80)

        try:
            result = await self.page.evaluate(f"""
                () => {{
                    const NEW_ID = "{self.config.new_logo_media_id}";
                    const targetWidth = {target_width};

                    const img = Array.from(document.querySelectorAll('img'))
                        .find(i => i.src.includes(NEW_ID) && i.getBoundingClientRect().width < 200);

                    if (!img) return {{ success: false, error: 'Logo not found' }};

                    const beforeRect = img.getBoundingClientRect();
                    const before = {{
                        width: Math.round(beforeRect.width),
                        height: Math.round(beforeRect.height)
                    }};

                    // Find container
                    let container = img.parentElement;
                    for (let i = 0; i < 5; i++) {{
                        if (!container) break;
                        if ((container.className || '').includes('resizable')) break;
                        container = container.parentElement;
                    }}

                    if (!container) container = img.parentElement;

                    // Set width
                    container.style.width = targetWidth + 'px';
                    container.style.maxWidth = targetWidth + 'px';

                    img.style.width = targetWidth + 'px';
                    img.style.maxWidth = targetWidth + 'px';
                    img.style.height = 'auto';

                    container.offsetHeight; // Force reflow

                    const afterRect = img.getBoundingClientRect();
                    const after = {{
                        width: Math.round(afterRect.width),
                        height: Math.round(afterRect.height)
                    }};

                    return {{
                        success: true,
                        before: before,
                        after: after
                    }};
                }}
            """)

            if result.get('success'):
                before = result['before']
                after = result['after']

                logger.info(f"Before: {before['width']}x{before['height']}px")
                logger.info(f"After: {after['width']}x{after['height']}px")

                if after['width'] > before['width']:
                    increase = after['width'] - before['width']
                    logger.info(f"✅ Logo enlarged by {increase}px width")
                    return True
                else:
                    logger.warning("⚠️  Logo size unchanged")
                    return False
            else:
                logger.error(f"❌ Enlargement failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            logger.error(f"❌ Enlargement failed: {e}")
            return False

    async def publish_changes(self) -> bool:
        """Publish the template changes (requires 2 clicks)"""
        logger.info("=" * 80)
        logger.info("PUBLISHING TEMPLATE CHANGES")
        logger.info("=" * 80)

        try:
            # First publish click
            logger.info("Step 1: Clicking PUBLISH (1st time)...")

            publish_btns = await self.page.query_selector_all('button:has-text("Publish")')

            main_publish = None
            for btn in publish_btns:
                box = await btn.bounding_box()
                if box and box['x'] > 100:  # Not at 0,0
                    main_publish = btn
                    logger.info(f"Found Publish button at ({int(box['x'])}, {int(box['y'])})")
                    break

            if not main_publish:
                logger.error("❌ Main Publish button not found")
                return False

            await main_publish.click()
            logger.info("✅ Clicked PUBLISH (1st time)")
            await asyncio.sleep(2.5)

            # Check if modal opened
            logger.info("Step 2: Checking for Publish Template modal...")

            modal_open = await self.page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    return modal && modal.getBoundingClientRect().width > 0;
                }
            """)

            logger.info(f"Modal open: {'✅ YES' if modal_open else '❌ NO'}")

            if not modal_open:
                logger.warning("⚠️  Publish modal did not open - changes might be auto-saved")
                return True

            # Analyze modal
            logger.info("Analyzing Publish Template modal...")

            modal_info = await self.page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    if (!modal) return null;

                    const inputs = Array.from(modal.querySelectorAll('input'))
                        .map(inp => ({
                            value: inp.value || '',
                            placeholder: inp.placeholder || ''
                        }));

                    const publishBtn = Array.from(modal.querySelectorAll('button'))
                        .find(btn => btn.innerText === 'Publish');

                    return {
                        inputs: inputs,
                        hasPublishBtn: publishBtn !== null
                    };
                }
            """)

            if modal_info:
                logger.info(f"Modal has {len(modal_info['inputs'])} input fields")
                logger.info(f"Modal has Publish button: {modal_info['hasPublishBtn']}")

            # Second publish click (in modal)
            logger.info("Step 3: Clicking PUBLISH in modal (2nd time)...")

            modal_publish = await self.page.query_selector('.ant-modal button:has-text("Publish")')

            if modal_publish:
                await modal_publish.click()
                logger.info("✅ Clicked PUBLISH in modal")
            else:
                # JavaScript fallback
                clicked = await self.page.evaluate("""
                    () => {
                        const modal = document.querySelector('.ant-modal');
                        if (modal) {
                            const btn = Array.from(modal.querySelectorAll('button'))
                                .find(b => b.innerText === 'Publish');
                            if (btn) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)

                if clicked:
                    logger.info("✅ Clicked PUBLISH via JavaScript")
                else:
                    logger.error("❌ Could not click modal Publish button")
                    return False

            await asyncio.sleep(3.0)

            # Verify modal closed
            logger.info("Step 4: Verifying publish completion...")

            modal_closed = await self.page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    return !modal || modal.getBoundingClientRect().width === 0;
                }
            """)

            logger.info(f"Modal closed: {'✅ YES' if modal_closed else '❌ NO'}")

            if modal_closed:
                logger.info("✅ Template changes published successfully!")
                return True
            else:
                logger.warning("⚠️  Modal still open - publish might have failed")
                return False

        except Exception as e:
            logger.error(f"❌ Publishing failed: {e}")
            return False

    async def execute_full_workflow(
        self,
        center_align: bool = True,
        enlarge: bool = True,
        target_width: int = 160,
        publish: bool = True
    ) -> bool:
        """Execute the complete logo replacement workflow"""
        logger.info("=" * 80)
        logger.info("EXECUTING FULL LOGO REPLACEMENT WORKFLOW")
        logger.info("=" * 80)
        logger.info(f"Options:")
        logger.info(f"  - Center align: {center_align}")
        logger.info(f"  - Enlarge: {enlarge} (target width: {target_width}px)")
        logger.info(f"  - Publish: {publish}")
        logger.info("=" * 80)

        try:
            # Step 1: Connect
            if not await self.connect():
                return False

            # Step 2: Detect current state
            state = await self.detect_current_state()

            if state.get('hasNewLogo') and not state.get('hasOldLogo'):
                logger.info("✅ New logo already present, old logo already removed!")
                logger.info("Skipping replacement, proceeding to alignment/enlargement if needed")
            elif state.get('hasOldLogo'):
                # Step 3: Replace logo
                if not await self.replace_logo():
                    logger.error("❌ Logo replacement failed")
                    return False
            else:
                logger.warning("⚠️  No logo detected - cannot proceed")
                return False

            # Step 4: Center align (optional)
            if center_align:
                if not await self.center_align_logo():
                    logger.warning("⚠️  Center alignment failed, continuing...")

            # Step 5: Enlarge (optional)
            if enlarge:
                if not await self.enlarge_logo(target_width):
                    logger.warning("⚠️  Enlargement failed, continuing...")

            # Step 6: Publish (optional)
            if publish:
                if not await self.publish_changes():
                    logger.error("❌ Publishing failed")
                    return False

            logger.info("=" * 80)
            logger.info("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            return False
        finally:
            if self.playwright:
                await self.playwright.stop()
                logger.info("Browser connection closed")


async def main():
    """Main entry point"""

    # Example configuration for Tilton logo replacement
    config = LogoReplacementConfig(
        old_logo_media_id="6a0c6722864813539e4da7ae",  # Old Nucar logo
        new_logo_media_id="6a19132b6697f36de6236fb1",  # Tilton logo
        new_logo_name="Tilton.png",
        chrome_debug_port=9223
    )

    automation = LogoReplacementAutomation(config)

    success = await automation.execute_full_workflow(
        center_align=True,
        enlarge=True,
        target_width=160,
        publish=True
    )

    if success:
        logger.info("🎉 Logo replacement automation completed successfully!")
        return 0
    else:
        logger.error("❌ Logo replacement automation failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
