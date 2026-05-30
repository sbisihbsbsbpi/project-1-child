#!/usr/bin/env python3
"""
Example Logo Replacement Configurations

This file contains example configurations for different logo replacement scenarios.
Copy and modify these examples for your specific use cases.
"""

from logo_replacement_automation import LogoReplacementConfig, LogoReplacementAutomation
import asyncio


# Example 1: Tilton Logo Replacement (Original)
TILTON_CONFIG = LogoReplacementConfig(
    old_logo_media_id="6a0c6722864813539e4da7ae",  # Old Nucar logo
    new_logo_media_id="6a19132b6697f36de6236fb1",  # Tilton logo
    new_logo_name="Tilton.png",
    chrome_debug_port=9223
)


# Example 2: Different Logo Replacement
# Replace with your actual media IDs
CUSTOM_LOGO_CONFIG = LogoReplacementConfig(
    old_logo_media_id="YOUR_OLD_LOGO_MEDIA_ID",
    new_logo_media_id="YOUR_NEW_LOGO_MEDIA_ID",
    new_logo_name="YourLogo.png",
    chrome_debug_port=9223
)


# Example 3: Multiple Logo Replacements
LOGO_REPLACEMENTS = [
    {
        "name": "Tilton Dealership",
        "config": LogoReplacementConfig(
            old_logo_media_id="6a0c6722864813539e4da7ae",
            new_logo_media_id="6a19132b6697f36de6236fb1",
            new_logo_name="Tilton.png"
        ),
        "options": {
            "center_align": True,
            "enlarge": True,
            "target_width": 160,
            "publish": True
        }
    },
    # Add more replacements here
    # {
    #     "name": "Another Dealership",
    #     "config": LogoReplacementConfig(...),
    #     "options": {...}
    # }
]


async def run_single_replacement(config, **options):
    """Run a single logo replacement"""
    print(f"\n{'=' * 80}")
    print(f"Running logo replacement...")
    print(f"{'=' * 80}\n")
    
    automation = LogoReplacementAutomation(config)
    success = await automation.execute_full_workflow(**options)
    
    return success


async def run_multiple_replacements(replacements):
    """Run multiple logo replacements sequentially"""
    results = []
    
    for idx, replacement in enumerate(replacements, 1):
        print(f"\n{'=' * 80}")
        print(f"REPLACEMENT {idx}/{len(replacements)}: {replacement['name']}")
        print(f"{'=' * 80}\n")
        
        automation = LogoReplacementAutomation(replacement['config'])
        success = await automation.execute_full_workflow(**replacement['options'])
        
        results.append({
            'name': replacement['name'],
            'success': success
        })
        
        if not success:
            print(f"\n⚠️  Replacement {idx} failed, continuing to next...\n")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}\n")
    
    for result in results:
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"{result['name']}: {status}")
    
    total_success = sum(1 for r in results if r['success'])
    print(f"\nTotal: {total_success}/{len(results)} successful")
    
    return results


# Example usage functions
async def example_tilton_replacement():
    """Example: Replace Nucar logo with Tilton logo"""
    return await run_single_replacement(
        TILTON_CONFIG,
        center_align=True,
        enlarge=True,
        target_width=160,
        publish=True
    )


async def example_custom_replacement():
    """Example: Custom logo replacement"""
    return await run_single_replacement(
        CUSTOM_LOGO_CONFIG,
        center_align=True,
        enlarge=True,
        target_width=200,  # Larger size
        publish=True
    )


async def example_replace_without_publish():
    """Example: Replace and format logo without publishing"""
    return await run_single_replacement(
        TILTON_CONFIG,
        center_align=True,
        enlarge=True,
        target_width=160,
        publish=False  # Don't publish, just preview
    )


async def example_replace_only():
    """Example: Just replace logo, no formatting"""
    return await run_single_replacement(
        TILTON_CONFIG,
        center_align=False,
        enlarge=False,
        publish=False
    )


async def example_multiple_replacements():
    """Example: Run multiple logo replacements"""
    return await run_multiple_replacements(LOGO_REPLACEMENTS)


if __name__ == "__main__":
    import sys
    
    print("""
    Logo Replacement Examples
    
    Available examples:
    1. Tilton logo replacement (full workflow)
    2. Custom logo replacement
    3. Replace without publishing
    4. Replace only (no formatting)
    5. Multiple replacements
    
    """)
    
    choice = input("Select example (1-5): ").strip()
    
    examples = {
        "1": example_tilton_replacement,
        "2": example_custom_replacement,
        "3": example_replace_without_publish,
        "4": example_replace_only,
        "5": example_multiple_replacements
    }
    
    if choice in examples:
        print(f"\nRunning example {choice}...\n")
        success = asyncio.run(examples[choice]())
        
        if success or (isinstance(success, list) and any(r['success'] for r in success)):
            print("\n✅ Example completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Example failed")
            sys.exit(1)
    else:
        print("Invalid choice")
        sys.exit(1)
