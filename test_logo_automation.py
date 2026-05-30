#!/usr/bin/env python3
"""
Test script for logo replacement automation
Tests individual components and full workflow
"""

import asyncio
import sys
from logo_replacement_automation import LogoReplacementAutomation, LogoReplacementConfig


async def test_connection():
    """Test browser connection"""
    print("\n" + "=" * 80)
    print("TEST 1: Browser Connection")
    print("=" * 80)
    
    config = LogoReplacementConfig(
        old_logo_media_id="6a0c6722864813539e4da7ae",
        new_logo_media_id="6a19132b6697f36de6236fb1",
        new_logo_name="Tilton.png"
    )
    
    automation = LogoReplacementAutomation(config)
    
    try:
        success = await automation.connect()
        
        if success:
            print("✅ Connection test PASSED")
            
            # Close connection
            if automation.playwright:
                await automation.playwright.stop()
            
            return True
        else:
            print("❌ Connection test FAILED")
            return False
    except Exception as e:
        print(f"❌ Connection test FAILED with exception: {e}")
        return False


async def test_detection():
    """Test logo detection"""
    print("\n" + "=" * 80)
    print("TEST 2: Logo Detection")
    print("=" * 80)
    
    config = LogoReplacementConfig(
        old_logo_media_id="6a0c6722864813539e4da7ae",
        new_logo_media_id="6a19132b6697f36de6236fb1",
        new_logo_name="Tilton.png"
    )
    
    automation = LogoReplacementAutomation(config)
    
    try:
        if not await automation.connect():
            print("❌ Could not connect to browser")
            return False
        
        state = await automation.detect_current_state()
        
        if state and 'totalImages' in state:
            print(f"✅ Detection test PASSED - Found {state['totalImages']} images")
            
            if automation.playwright:
                await automation.playwright.stop()
            
            return True
        else:
            print("❌ Detection test FAILED - Could not detect images")
            return False
            
    except Exception as e:
        print(f"❌ Detection test FAILED with exception: {e}")
        return False
    finally:
        if automation.playwright:
            await automation.playwright.stop()


async def test_full_workflow_dry_run():
    """Test full workflow without publishing"""
    print("\n" + "=" * 80)
    print("TEST 3: Full Workflow (Dry Run - No Publish)")
    print("=" * 80)
    
    config = LogoReplacementConfig(
        old_logo_media_id="6a0c6722864813539e4da7ae",
        new_logo_media_id="6a19132b6697f36de6236fb1",
        new_logo_name="Tilton.png"
    )
    
    automation = LogoReplacementAutomation(config)
    
    try:
        success = await automation.execute_full_workflow(
            center_align=True,
            enlarge=True,
            target_width=160,
            publish=False  # Dry run - don't publish
        )
        
        if success:
            print("✅ Full workflow test PASSED (dry run)")
            return True
        else:
            print("❌ Full workflow test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Full workflow test FAILED with exception: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LOGO REPLACEMENT AUTOMATION - TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Connection", test_connection),
        ("Detection", test_detection),
        ("Full Workflow (Dry Run)", test_full_workflow_dry_run)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    print("""
    Logo Replacement Automation - Test Suite
    
    This will run a series of tests to verify the automation works correctly.
    
    Prerequisites:
    1. Browser must be running with --remote-debugging-port=9223
    2. Template edit page must be open in browser
    3. Template should contain a logo that can be detected
    
    Press Enter to continue or Ctrl+C to cancel...
    """)
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
        sys.exit(0)
    
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
