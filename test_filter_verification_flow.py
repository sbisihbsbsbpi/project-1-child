#!/usr/bin/env python3
"""
Test the complete filter verification flow:
1. Set to Sales only
2. Analyze
3. Change to Service & Parts
4. Analyze and compare
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'automation'))

from department_filter_automation import change_department_filter
from smart_department_filter_with_verification import change_department_with_verification


async def main():
    print("=" * 100)
    print("🧪 COMPLETE FILTER VERIFICATION TEST")
    print("=" * 100)
    print()
    
    # Step 1: Reset to Sales only
    print("=" * 100)
    print("STEP 1: RESET TO SALES ONLY")
    print("=" * 100)
    print()
    
    result1 = await change_department_filter(
        departments_to_select=['Sales'],
        departments_to_unselect=['Service', 'Parts'],
        wait_seconds=15
    )
    
    print(f"\n✅ Reset complete. Current selection: {result1['final_selection']}\n")
    
    # Step 2: Change to Service & Parts with full verification
    print("=" * 100)
    print("STEP 2: CHANGE TO SERVICE & PARTS (WITH VERIFICATION)")
    print("=" * 100)
    print()
    
    result2 = await change_department_with_verification(
        departments_to_select=['Service', 'Parts'],
        departments_to_unselect=['Sales'],
        wait_seconds=20
    )
    
    # Summary
    print("\n" + "=" * 100)
    print("📊 FINAL SUMMARY")
    print("=" * 100)
    print()
    
    if result2 and result2.get('comparison'):
        comp = result2['comparison']
        print(f"Filter Changed:     {'✅ YES' if comp['filter_changed'] else '❌ NO'}")
        print(f"Data Changed:       {'✅ YES' if comp['data_changed'] else '❌ NO'}")
        
        if comp.get('details', {}).get('tab_changes'):
            print(f"\nTab Count Changes:")
            for change in comp['details']['tab_changes']:
                print(f"  {change['tab']}: {change['before']} → {change['after']}")
        
        if comp.get('details', {}).get('table'):
            table = comp['details']['table']
            print(f"\nTable Changes:")
            print(f"  Before: {table['before_rows']} rows")
            print(f"  After:  {table['after_rows']} rows")
            print(f"  Delta:  {table['delta']}")
    
    print("\n" + "=" * 100)
    print("✅ TEST COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
