#!/usr/bin/env python3
"""
Switch to SERVICE Department in Tekion Templates
Properly clicks the Ant Design dropdown and selects SERVICE
"""

import asyncio
from playwright.async_api import async_playwright

async def switch_to_service():
    print("🔄 Switching to SERVICE Department\n")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find or open template list page
    page = None
    for p in context.pages:
        if 'templates/list' in p.url:
            page = p
            break
    
    if not page:
        print("Opening templates list page...")
        page = await context.new_page()
        await page.goto("https://preprodapp.tekioncloud.com/templates/list", wait_until='domcontentloaded')
        await asyncio.sleep(3)
    
    print("✅ Using template list page\n")
    
    # Step 1: Click the dropdown trigger
    print("📋 Step 1: Opening department dropdown...")
    
    clicked = await page.evaluate("""
        () => {
            const trigger = document.querySelector('.ant-dropdown-trigger');
            if (trigger) {
                trigger.click();
                return true;
            }
            return false;
        }
    """)
    
    if not clicked:
        print("❌ Could not find dropdown trigger")
        await playwright.stop()
        return False
    
    print("   ✅ Dropdown opened\n")
    await asyncio.sleep(0.8)
    
    # Step 2: Click on "Service" option
    print("🎯 Step 2: Clicking on 'Service' option...")

    service_clicked = await page.evaluate("""
        () => {
            // Use the exact class we found: css-1oiby7b-option or any option class
            const options = document.querySelectorAll('[class*="css-"][class*="-option"]');

            const serviceOption = Array.from(options).find(opt =>
                opt.textContent.trim() === 'Service' &&
                opt.offsetParent !== null
            );

            if (serviceOption) {
                console.log('Clicking Service option:', serviceOption);
                serviceOption.click();
                return true;
            }
            return false;
        }
    """)
    
    if not service_clicked:
        print("❌ Could not find Service option")
        await playwright.stop()
        return False
    
    print("   ✅ Clicked on Service\n")
    await asyncio.sleep(1.5)
    
    # Step 3: Verify the change
    print("✔️  Step 3: Verifying department changed...")
    
    current_dept = await page.evaluate("""
        () => {
            const trigger = document.querySelector('.ant-dropdown-trigger');
            if (trigger) {
                const text = trigger.textContent.trim();
                // Extract department name from the text
                if (text.includes('Service')) return 'Service';
                if (text.includes('Sales')) return 'Sales';
                if (text.includes('Parts')) return 'Parts';
                return text;
            }
            return 'Unknown';
        }
    """)
    
    print(f"   Current department: {current_dept}\n")
    
    if current_dept == 'Service':
        print("🎉 SUCCESS! Department is now SERVICE!")
        await playwright.stop()
        return True
    else:
        print(f"⚠️  Department shows: {current_dept} (expected Service)")
        await playwright.stop()
        return False

if __name__ == "__main__":
    success = asyncio.run(switch_to_service())
    exit(0 if success else 1)
