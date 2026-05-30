#!/usr/bin/env python3
"""
Demo script to update OEM ID for a single user: MRodriguez@mbcoralgables.com
This demonstrates the workflow before implementing the full batch process.
"""

import requests
import json
import sys

# Target user for demo
TARGET_EMAIL = "Dayron.Cejas@mbcoralgables.com"
NEW_OEM_ID = "UMB1203240"

# Headers (from PartsTab UNIFIED_HEADERS)
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en;q=0.9',
    'applicationid': 'ARC_NA',
    'clientid': 'web',
    'content-type': 'application/json',
    'dealerid': '7616',
    'dnt': '1',
    'flattenedaecprogramsmap': 'HMA::HMA_US_HYUNDAI_NEW',
    'locale': 'en_US',
    'origin': 'https://preprodapp.tekioncloud.com',
    'original-tenantid': 'techmotors',
    'original-userid': 'fe3a3333-c9ad-49fd-bef7-79eacaddc1d5',
    'priority': 'u=1, i',
    'productids': 'ARC',
    'program': 'DEFAULT',
    'roleid': '7616_ISM_Admin',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'subapplicationid': 'US',
    'tek-siteid': '-1_7616',
    'tekion-api-token': 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI0ZjQxYjRlZS1mZjYxLTQ4MjYtODUzMi02ZmQ5MTk5OGI3ZGUiLCJpYXQiOjE3Nzk3OTcwMDEsInN1YiI6IjRmNDFiNGVlLWZmNjEtNDgyNi04NTMyLTZmZDkxOTk4YjdkZSIsImlzcyI6IkxvZ2luU2VydmljZSIsInVubG9ja0FjY291bnQiOmZhbHNlLCJub3VuY2UiOiI2MDMyNzg3YS1kNjgxLTRjODQtOTBmYy0zYzI4NTNiMjM1ZDMiLCJvcmlnaW5hbFVzZXJJZCI6ImZlM2EzMzMzLWM5YWQtNDlmZC1iZWY3LTc5ZWFjYWRkYzFkNSIsIm9yaWdpbmFsVGVuYW50SWQiOiJ0ZWNobW90b3JzIiwidXNlcklkIjoiNGY0MWI0ZWUtZmY2MS00ODI2LTg1MzItNmZkOTE5OThiN2RlIiwiZW1haWwiOiJpc21AZHJlYW1tb3Rvcmdyb3VwbGxjLmNvbSIsImV4cCI6MTc3OTgwNDc3N30.TAB6tkO5j4HgMsfTAzWJdb735iqlcxjhRmQq99MJRjY',
    'tenantname': 'dreammotorgroupllc',
    'tracestate': 'es=s:1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'userid': '4f41b4ee-ff61-4826-8532-6fd91998b7de',
    'x-observe-rum-id': '00-58441366428656f83382cb21cbcfb044-67070cda1c0bf900-01'
}

# Base URLs
BASE_URL = "https://preprodapp.tekioncloud.com"
USER_ROLES_ENDPOINT = f"{BASE_URL}/api/userservice/u/v2/userandroles"
USER_SETTINGS_ENDPOINT = f"{BASE_URL}/api/userservice/u/user-access-settings"

def step1_fetch_users():
    """Step 1: Fetch all users to find the target email"""
    print("\n" + "="*80)
    print("STEP 1: Fetching all users from Tekion")
    print("="*80)

    all_users = []
    start = 0
    page_size = 200

    try:
        while True:
            # Fetch with pagination (correct Tekion format)
            payload = {
                "sort": [],
                "filters": [{"field": "active", "operator": "IN", "values": [True], "key": "active"}],
                "searchText": "",
                "groupBy": [],
                "includeFields": [],
                "searchableFields": [],
                "excludeFields": [],
                "pageInfo": {"start": start, "rows": page_size}
            }

            response = requests.post(USER_ROLES_ENDPOINT, headers=HEADERS, json=payload)
            page_num = (start // page_size) + 1
            print(f"Page {page_num}: Status Code {response.status_code}")

            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                break

            data = response.json()
            users = data.get('data', {}).get('userAndRoleResponses', [])
            total_count = data.get('data', {}).get('count', 0)

            if not users:
                break

            all_users.extend(users)
            print(f"   Got {len(users)} users (Total so far: {len(all_users)} / {total_count})")

            # Check if we have all users
            if len(all_users) >= total_count:
                break

            start += page_size

        print(f"\n✅ Total users fetched: {len(all_users)}")

        # Show first few emails for debugging
        if len(all_users) > 0:
            print(f"\n📧 Sample emails:")
            for i, user in enumerate(all_users[:5]):
                print(f"   {i+1}. {user.get('email', 'N/A')}")

        # Find target user
        target_user = None
        for user in all_users:
            if user.get('email', '').lower() == TARGET_EMAIL.lower():
                target_user = user
                break
        
        if target_user:
            print(f"\n✅ Found target user:")
            print(f"   Email: {target_user.get('email')}")
            print(f"   ID: {target_user.get('id')}")
            print(f"   Name: {target_user.get('firstName')} {target_user.get('lastName')}")
            return target_user
        else:
            print(f"\n❌ Target email not found: {TARGET_EMAIL}")

            # Search for similar emails
            print(f"\n🔍 Searching for similar emails containing 'dayron' or 'cejas'...")
            matches = [u for u in all_users if 'dayron' in u.get('email', '').lower() or 'cejas' in u.get('email', '').lower()]
            if matches:
                print(f"   Found {len(matches)} similar emails:")
                for m in matches[:10]:
                    print(f"   - {m.get('email')}")
            else:
                print(f"   No similar emails found")

            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def step2_get_user_details(user_id):
    """Step 2: Get full user details including OEM mappings"""
    print("\n" + "="*80)
    print(f"STEP 2: Getting user details for ID: {user_id}")
    print("="*80)
    
    url = f"{USER_SETTINGS_ENDPOINT}/{user_id}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
        
        data = response.json()
        user = data.get('data', {}).get('user', {})
        
        print(f"\n✅ Retrieved user details")
        
        # Check OEM mappings
        oem_mappings = user.get('oemMappings', [])
        if not oem_mappings:
            print("❌ No oemMappings found")
            return None
        
        print(f"\n📊 Current OEM Mappings:")
        print(f"   Number of mappings: {len(oem_mappings)}")
        
        if oem_mappings and oem_mappings[0].get('oemDetails'):
            oem_details = oem_mappings[0]['oemDetails'][0]
            print(f"\n   Current OEM Details:")
            print(f"   - OEM: {oem_details.get('oem')}")
            print(f"   - OEM ID: {oem_details.get('oemId')}")
            print(f"   - OEM Name: {oem_details.get('oemName')}")
            if 'complexListId' in oem_details:
                print(f"   - Complex List ID: {oem_details.get('complexListId')}")
            if 'makeOverrides' in oem_details:
                print(f"   - Make Overrides: {len(oem_details.get('makeOverrides', []))} items")
        
        return user
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def step3_update_oem_id(user_id, user_data):
    """Step 3: Update the OEM ID"""
    print("\n" + "="*80)
    print(f"STEP 3: Updating OEM ID to: {NEW_OEM_ID}")
    print("="*80)
    
    # Update ONLY the oemId field
    old_oem_id = user_data['oemMappings'][0]['oemDetails'][0].get('oemId', '')
    user_data['oemMappings'][0]['oemDetails'][0]['oemId'] = NEW_OEM_ID
    
    print(f"\n🔄 Change:")
    print(f"   Old OEM ID: '{old_oem_id}'")
    print(f"   New OEM ID: '{NEW_OEM_ID}'")
    
    # PUT request with saveUserRequest wrapper
    url = f"{USER_SETTINGS_ENDPOINT}/{user_id}"
    payload = {
        "saveUserRequest": user_data
    }
    
    try:
        response = requests.put(url, headers=HEADERS, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ SUCCESS! OEM ID updated")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("\n" + "🚀"*40)
    print("OEM ID UPDATE DEMO")
    print(f"Target Email: {TARGET_EMAIL}")
    print(f"New OEM ID: {NEW_OEM_ID}")
    print("🚀"*40)
    
    # Step 1: Find user
    user = step1_fetch_users()
    if not user:
        print("\n❌ FAILED: Could not find user")
        sys.exit(1)
    
    user_id = user['id']
    
    # Step 2: Get user details
    user_data = step2_get_user_details(user_id)
    if not user_data:
        print("\n❌ FAILED: Could not get user details")
        sys.exit(1)
    
    # Step 3: Update OEM ID
    success = step3_update_oem_id(user_id, user_data)
    
    if success:
        print("\n" + "="*80)
        print("✅ DEMO COMPLETE - OEM ID SUCCESSFULLY UPDATED!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ DEMO FAILED - OEM ID NOT UPDATED")
        print("="*80)
        sys.exit(1)

if __name__ == "__main__":
    main()
