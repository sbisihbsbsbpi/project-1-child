#!/usr/bin/env python3
"""
Analyze user structure from Tekion API for store 7619 (MB Cutler Bay)
Target: Maria.Caso@mbcutlerbay.com
"""

import requests
import json

# API Endpoints
LIST_USERS_ENDPOINT = "https://preprodapp.tekioncloud.com/api/userservice/u/v2/userandroles"
USER_SETTINGS_ENDPOINT = "https://preprodapp.tekioncloud.com/api/userservice/u/user-access-settings"

# Headers for Store 7619 (MB Cutler Bay)
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'applicationid': 'ARC_NA',
    'clientid': 'web',
    'content-type': 'application/json',
    'dealerid': '7619',
    'dnt': '1',
    'flattenedaecprogramsmap': '',
    'locale': 'en_US',
    'origin': 'https://preprodapp.tekioncloud.com',
    'original-tenantid': 'techmotors',
    'original-userid': 'fe3a3333-c9ad-49fd-bef7-79eacaddc1d5',
    'priority': 'u=1, i',
    'productids': 'ARC',
    'program': 'DEFAULT',
    'referer': 'https://preprodapp.tekioncloud.com/core/user-setup',
    'roleid': '7619_ISM_Admin',
    'subapplicationid': 'US',
    'tek-siteid': '-1_7619',
    'tekion-api-token': 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI0ZjQxYjRlZS1mZjYxLTQ4MjYtODUzMi02ZmQ5MTk5OGI3ZGUiLCJpYXQiOjE3Nzk3OTcwMDEsInN1YiI6IjRmNDFiNGVlLWZmNjEtNDgyNi04NTMyLTZmZDkxOTk4YjdkZSIsImlzcyI6IkxvZ2luU2VydmljZSIsInVubG9ja0FjY291bnQiOmZhbHNlLCJub3VuY2UiOiI2MDMyNzg3YS1kNjgxLTRjODQtOTBmYy0zYzI4NTNiMjM1ZDMiLCJvcmlnaW5hbFVzZXJJZCI6ImZlM2EzMzMzLWM5YWQtNDlmZC1iZWY3LTc5ZWFjYWRkYzFkNSIsIm9yaWdpbmFsVGVuYW50SWQiOiJ0ZWNobW90b3JzIiwidXNlcklkIjoiNGY0MWI0ZWUtZmY2MS00ODI2LTg1MzItNmZkOTE5OThiN2RlIiwiZW1haWwiOiJpc21AZHJlYW1tb3Rvcmdyb3VwbGxjLmNvbSIsImV4cCI6MTc3OTgwNDc3N30.TAB6tkO5j4HgMsfTAzWJdb735iqlcxjhRmQq99MJRjY',
    'tenantname': 'dreammotorgroupllc',
    'userid': '4f41b4ee-ff61-4826-8532-6fd91998b7de'
}

# Try multiple users to find one with oemMappings
TARGET_EMAILS = [
    "Maria.Caso@mbcutlerbay.com",
    "Marc.Barratteau@mbcutlerbay.com",
    "Juan.Rodriguez@mbcutlerbay.com",
    "Roberto.llanes@mbcutlerbay.com"
]

TARGET_EMAIL = TARGET_EMAILS[0]  # Start with first

print("=" * 80)
print(f"ANALYZING USER STRUCTURE FOR: {TARGET_EMAIL}")
print(f"Store: 7619 (MB Cutler Bay)")
print("=" * 80)

# Step 1: Search for the user (try multiple approaches)
print("\n[STEP 1] Searching for user in user list...")

# First try: exact email search
search_payload = {
    "sort": [],
    "filters": [{"field": "active", "operator": "IN", "values": [True], "key": "active"}],
    "searchText": TARGET_EMAIL,
    "groupBy": [],
    "includeFields": [],
    "searchableFields": [],
    "excludeFields": [],
    "pageInfo": {"start": 0, "rows": 50}
}

response = requests.post(LIST_USERS_ENDPOINT, headers=HEADERS, json=search_payload)

if response.status_code != 200:
    print(f"❌ Search failed: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
users = data.get('data', {}).get('userAndRoleResponses', [])

# If not found, try without search text (get all users with correct filters)
if not users:
    print(f"   Not found with exact search, fetching all users...")
    # Use the correct payload format that works
    search_payload = {
        "sort": [],
        "filters": [{"field": "active", "operator": "IN", "values": [True], "key": "active"}],
        "searchText": "",
        "groupBy": [],
        "includeFields": [],
        "searchableFields": [],
        "excludeFields": [],
        "pageInfo": {"start": 0, "rows": 200}
    }
    response = requests.post(LIST_USERS_ENDPOINT, headers=HEADERS, json=search_payload)

    print(f"   Response status: {response.status_code}")

    data = response.json()
    print(f"   Response keys: {list(data.keys())}")
    print(f"   Data keys: {list(data.get('data', {}).keys())}")

    all_users = data.get('data', {}).get('userAndRoleResponses', [])
    total_count = data.get('data', {}).get('count', 0)

    print(f"   Total users in response: {len(all_users)}")
    print(f"   Total count from API: {total_count}")

    # Debug: print first page info
    page_info = data.get('data', {}).get('pageInfo', {})
    print(f"   Page info: {page_info}")

    # Find by email
    users = [u for u in all_users if u.get('email', '').lower() == TARGET_EMAIL.lower()]

    if not users:
        print(f"❌ User not found: {TARGET_EMAIL}")
        print(f"   Showing first 10 users with @mbcutlerbay.com:")
        cutler_users = [u for u in all_users if '@mbcutlerbay.com' in u.get('email', '').lower()]
        for u in cutler_users[:10]:
            print(f"      - {u.get('email')}")
        exit(1)

user_summary = users[0]
user_id = user_summary.get('id')
print(f"✅ User found!")
print(f"   ID: {user_id}")
print(f"   Email: {user_summary.get('email')}")
print(f"   Name: {user_summary.get('fname')} {user_summary.get('lname')}")

# Step 2: Get full user details
print("\n[STEP 2] Getting full user details...")
detail_url = f"{USER_SETTINGS_ENDPOINT}/{user_id}"
detail_response = requests.get(detail_url, headers=HEADERS)

if detail_response.status_code != 200:
    print(f"❌ GET failed: {detail_response.status_code}")
    print(detail_response.text)
    exit(1)

full_data = detail_response.json()
user = full_data.get('data', {}).get('user', {})

print(f"✅ Full user data retrieved")

# Step 3: Analyze the structure
print("\n" + "=" * 80)
print("USER STRUCTURE ANALYSIS")
print("=" * 80)

# Basic Info
print("\n[BASIC INFO]")
print(f"   ID: {user.get('id')}")
print(f"   Email: {user.get('email')}")
print(f"   First Name: {user.get('fname')}")
print(f"   Last Name: {user.get('lname')}")
print(f"   Active: {user.get('active')}")

# OEM Mappings Analysis
print("\n[OEM MAPPINGS]")
if not user.get('oemMappings'):
    print("   ❌ NO oemMappings field present")
    print("   → This user would need SCENARIO 3 (CREATE NEW)")
else:
    print("   ✅ oemMappings exists")
    oem_mappings = user['oemMappings']
    print(f"   → Array length: {len(oem_mappings)}")
    
    for idx, mapping in enumerate(oem_mappings):
        print(f"\n   [Mapping {idx}]")
        print(f"      dealerId: {mapping.get('dealerId')}")
        print(f"      complexListId: {mapping.get('complexListId', 'NOT PRESENT')}")
        
        if mapping.get('oemDetails'):
            print(f"      oemDetails: {len(mapping['oemDetails'])} item(s)")
            for detail_idx, detail in enumerate(mapping['oemDetails']):
                print(f"\n      [oemDetails {detail_idx}]")
                print(f"         oem: {detail.get('oem')}")
                print(f"         oemId: {detail.get('oemId')}")
                print(f"         oemName: {detail.get('oemName')}")
                print(f"         complexListId: {detail.get('complexListId', 'NOT PRESENT')}")
                print(f"         makeOverrideDisabled: {detail.get('makeOverrideDisabled')}")
                
                if detail.get('makeOverrides'):
                    print(f"         makeOverrides: {len(detail['makeOverrides'])} item(s)")
                    for override_idx, override in enumerate(detail['makeOverrides']):
                        print(f"            [{override_idx}] make: {override.get('make')}, oemId: {override.get('oemId')}, complexListId: {override.get('complexListId', 'NOT PRESENT')}")

# Determine scenario
print("\n" + "=" * 80)
print("SCENARIO DETERMINATION")
print("=" * 80)

if not user.get('oemMappings'):
    print("✅ SCENARIO 3: CREATE NEW oemMappings")
    print("   → User has no oemMappings field")
    print("   → Need to create entire structure")
elif user['oemMappings'][0].get('complexListId'):
    print("✅ SCENARIO 1: EXISTING with complexListId")
    print("   → User has oemMappings with complexListId")
    print("   → Update oemId and PRESERVE complexListId")
else:
    print("✅ SCENARIO 2: NEW without complexListId")
    print("   → User has oemMappings but NO complexListId")
    print("   → Update oemId and REMOVE any complexListId if present")

# Save full JSON for inspection
output_file = f"/Users/tlreddy/Documents/project-1-child/user_structure_{user_id}.json"
with open(output_file, 'w') as f:
    json.dump(user, f, indent=2)

print(f"\n✅ Full user JSON saved to: {output_file}")
print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
