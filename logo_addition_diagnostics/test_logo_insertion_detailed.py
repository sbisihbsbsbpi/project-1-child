#!/usr/bin/env python3
"""
Deep Diagnostic: Test logo insertion step-by-step
Shows exactly where the process fails
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🔬 DEEP LOGO INSERTION DIAGNOSTIC")
    print("=" * 100)
    
    template_id = "667f0befd4964026ee7b6e46"  # RO Invoiced
    logo_media_id = "667f0befd4964026ee7b6ea2"  # Tilton logo
    
    # Test with one of the CORRECT IDs
    test_container_id = "6f0b8570-c4dc-45bd-b746-40e3af9af3bb"  # Logo 1 LEFT
    container_name = "Logo 1 LEFT"
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            
            # Find the template tab
            pages = context.pages
            page = None
            for p in pages:
                if template_id in p.url:
                    page = p
                    break
            
            if not page:
                print(f"❌ Template tab not found. Please open: https://preprodapp.tekioncloud.com/templates/edit/{template_id}")
                return
            
            print(f"📄 Using page: {page.url}")
            print(f"🎯 Target container: {container_name} ({test_container_id})")
            print(f"🖼️  Logo Media ID: {logo_media_id}\n")
            
            # STEP 1: Verify container exists
            print("=" * 100)
            print("STEP 1: VERIFY CONTAINER EXISTS")
            print("=" * 100)
            
            target_selector = f'div.TEXT_TEMPLATE[id="{test_container_id}"][contenteditable="true"]'
            
            container_info = await page.evaluate(f"""
                () => {{
                    const selector = '{target_selector.replace("'", "\\'")}';
                    const el = document.querySelector(selector);
                    
                    if (!el) return {{ exists: false }};
                    
                    const rect = el.getBoundingClientRect();
                    return {{
                        exists: true,
                        id: el.id,
                        className: el.className,
                        visible: rect.width > 0 && rect.height > 0,
                        rect: {{ top: rect.top, left: rect.left, width: rect.width, height: rect.height }},
                        isEmpty: el.textContent.trim() === '' && !el.querySelector('img'),
                        html: el.innerHTML.substring(0, 200),
                        contentEditable: el.getAttribute('contenteditable')
                    }};
                }}
            """)
            
            if not container_info['exists']:
                print(f"❌ Container NOT FOUND with selector: {target_selector}")
                return
            
            print(f"✅ Container found!")
            print(f"   ID: {container_info['id']}")
            print(f"   Visible: {container_info['visible']}")
            print(f"   Empty: {container_info['isEmpty']}")
            print(f"   Rect: {container_info['rect']}")
            print(f"   ContentEditable: {container_info['contentEditable']}")
            
            if not container_info['visible']:
                print("   ⚠️  Container is HIDDEN (width=0) - may cause issues")
            
            # STEP 2: Try clicking the container
            print("\n" + "=" * 100)
            print("STEP 2: CLICK THE CONTAINER")
            print("=" * 100)
            
            click_success = False
            
            # Try 1: Force click
            print("Attempt 1: Force click...")
            try:
                await page.click(target_selector, force=True, timeout=5000)
                print("✅ Force click successful")
                click_success = True
            except Exception as e:
                print(f"❌ Force click failed: {e}")
                
                # Try 2: JavaScript click
                print("\nAttempt 2: JavaScript click...")
                try:
                    await page.evaluate(f"""
                        document.querySelector('{target_selector.replace("'", "\\'")}').click()
                    """)
                    print("✅ JavaScript click successful")
                    click_success = True
                except Exception as e2:
                    print(f"❌ JavaScript click failed: {e2}")
                    
                    # Try 3: Focus
                    print("\nAttempt 3: JavaScript focus...")
                    try:
                        await page.evaluate(f"""
                            const el = document.querySelector('{target_selector.replace("'", "\\'")}');
                            el.focus();
                        """)
                        print("✅ Focus successful")
                        click_success = True
                    except Exception as e3:
                        print(f"❌ Focus failed: {e3}")
            
            if not click_success:
                print("\n❌ ALL CLICK ATTEMPTS FAILED - Cannot proceed")
                return
            
            # Wait for toolbar
            print("\nWaiting 3 seconds for toolbar to appear...")
            await asyncio.sleep(3)
            
            # STEP 3: Search for toolbar and Insert Image button
            print("\n" + "=" * 100)
            print("STEP 3: SEARCH FOR INSERT IMAGE BUTTON")
            print("=" * 100)
            
            toolbar_search = await page.evaluate("""
                () => {
                    // Comprehensive search for insert image functionality
                    const results = {
                        insertImageButtons: [],
                        allToolbars: [],
                        allVisibleButtons: [],
                        dealerLogoButton: null,
                        mediaLibraryAccess: null
                    };
                    
                    // 1. Search for insert image button with multiple selectors
                    const insertSelectors = [
                        '.icon-insert-image',
                        '[aria-label*="insert" i][aria-label*="image" i]',
                        '[class*="insert"][class*="image"]',
                        '[title*="Insert Image" i]',
                        '[data-action="insert-image"]',
                        'button:has-text("Image")',
                        'i.icon-insert-image',
                        'span.icon-insert-image'
                    ];
                    
                    insertSelectors.forEach(sel => {
                        try {
                            const els = document.querySelectorAll(sel);
                            els.forEach(el => {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    results.insertImageButtons.push({
                                        selector: sel,
                                        ariaLabel: el.getAttribute('aria-label'),
                                        className: el.className.substring(0, 80),
                                        tagName: el.tagName,
                                        visible: true,
                                        rect: { top: rect.top, left: rect.left, width: rect.width, height: rect.height }
                                    });
                                }
                            });
                        } catch(e) {}
                    });
                    
                    // 2. Find all toolbars
                    const toolbarSels = ['[class*="toolbar"]', '[class*="editor-menu"]', '[role="toolbar"]'];
                    toolbarSels.forEach(sel => {
                        document.querySelectorAll(sel).forEach(tb => {
                            const rect = tb.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                results.allToolbars.push({
                                    selector: sel,
                                    className: tb.className.substring(0, 80),
                                    rect: { width: rect.width, height: rect.height },
                                    buttonCount: tb.querySelectorAll('button, [role="button"]').length
                                });
                            }
                        });
                    });
                    
                    // 3. All visible buttons (for debugging)
                    document.querySelectorAll('button').forEach(btn => {
                        const rect = btn.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            const text = btn.textContent.trim().substring(0, 30);
                            const ariaLabel = btn.getAttribute('aria-label');
                            if (text || ariaLabel) {
                                results.allVisibleButtons.push({
                                    text: text,
                                    ariaLabel: ariaLabel,
                                    className: btn.className.substring(0, 60)
                                });
                            }
                        }
                    });
                    
                    // 4. Check for DEALER_LOGO button (alternative insertion method)
                    const dealerLogoBtn = document.querySelector('[id="DEALER_LOGO"]');
                    if (dealerLogoBtn) {
                        const rect = dealerLogoBtn.getBoundingClientRect();
                        results.dealerLogoButton = {
                            found: true,
                            visible: rect.width > 0 && rect.height > 0,
                            rect: { width: rect.width, height: rect.height }
                        };
                    }
                    
                    return results;
                }
            """)
            
            print(f"\n📊 SEARCH RESULTS:")
            print(f"   Insert Image Buttons Found: {len(toolbar_search['insertImageButtons'])}")
            print(f"   Toolbars Found: {len(toolbar_search['allToolbars'])}")
            print(f"   Visible Buttons: {len(toolbar_search['allVisibleButtons'])}")

            if toolbar_search['insertImageButtons']:
                print(f"\n✅ FOUND INSERT IMAGE BUTTONS:")
                for i, btn in enumerate(toolbar_search['insertImageButtons'], 1):
                    print(f"   {i}. {btn['selector']}")
                    print(f"      Tag: {btn['tagName']}, Aria: {btn['ariaLabel']}")
                    print(f"      Rect: {btn['rect']}")
            else:
                print(f"\n❌ NO INSERT IMAGE BUTTONS FOUND")
                print(f"\n🔍 Available buttons (first 20):")
                for i, btn in enumerate(toolbar_search['allVisibleButtons'][:20], 1):
                    print(f"   {i}. {btn['text'] or btn['ariaLabel'] or 'No text'}")

            if toolbar_search['dealerLogoButton']:
                print(f"\n💡 DEALER_LOGO button found: {toolbar_search['dealerLogoButton']}")

            # STEP 4: Alternative - Try using DEALER_LOGO button
            if toolbar_search['dealerLogoButton'] and toolbar_search['dealerLogoButton']['visible']:
                print("\n" + "=" * 100)
                print("STEP 4: ALTERNATIVE - TRY DEALER_LOGO BUTTON")
                print("=" * 100)

                print("Clicking DEALER_LOGO button...")
                try:
                    await page.click('[id="DEALER_LOGO"]', timeout=5000)
                    print("✅ DEALER_LOGO button clicked")
                    await asyncio.sleep(2)

                    # Check if media library opened
                    media_lib = await page.evaluate("""
                        () => {
                            const modal = document.querySelector('[class*="modal"], [class*="dialog"], [role="dialog"]');
                            if (!modal) return { found: false };

                            const rect = modal.getBoundingClientRect();
                            return {
                                found: true,
                                visible: rect.width > 0 && rect.height > 0,
                                title: modal.querySelector('h1, h2, h3')?.textContent,
                                hasImages: modal.querySelectorAll('img').length
                            };
                        }
                    """)

                    if media_lib['found']:
                        print(f"✅ Media library/modal opened!")
                        print(f"   Title: {media_lib.get('title', 'N/A')}")
                        print(f"   Images: {media_lib.get('hasImages', 0)}")

                        # This is a viable insertion method!
                        print("\n💡 SOLUTION: Can use DEALER_LOGO button to insert logos!")
                    else:
                        print("❌ No modal/dialog appeared")

                except Exception as e:
                    print(f"❌ Failed to click DEALER_LOGO: {e}")

            # STEP 5: Summary and recommendations
            print("\n" + "=" * 100)
            print("📋 DIAGNOSTIC SUMMARY")
            print("=" * 100)

            print(f"\n✅ Container exists: YES")
            print(f"✅ Container clickable: {click_success}")
            print(f"❌ Insert Image button found: {len(toolbar_search['insertImageButtons']) > 0}")
            print(f"💡 DEALER_LOGO button available: {toolbar_search['dealerLogoButton'] is not None}")

            print("\n🎯 RECOMMENDATIONS:")

            if len(toolbar_search['insertImageButtons']) > 0:
                print("   1. Use standard insert image button (found in toolbar)")
            elif toolbar_search['dealerLogoButton']:
                print("   1. Use DEALER_LOGO button as alternative insertion method")
                print("   2. This button likely opens media library")
                print("   3. Select logo from media library")
            else:
                print("   1. Container is hidden (width=0) - may need to make visible first")
                print("   2. Try different editor interaction (double-click, etc.)")
                print("   3. Insert HTML directly into container")

            print("\n" + "=" * 100)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

