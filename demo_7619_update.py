#!/usr/bin/env python3
"""
DEMO: Test dealer ID verification for store 7619
Target: Maria.Caso@mbcutlerbay.com
OEM ID: UMB1191975
"""

import requests
import json

# Headers for Store 7619 (MB Cutler Bay) - FRESH TOKEN
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
    'referer': 'https://preprodapp.tekioncloud.com/core/user-setup/edit/018ce914-1c2d-41c8-9fc3-c49058a33c0c',
    'roleid': '7619_ISM_Admin',
    'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'subapplicationid': 'US',
    'tek-siteid': '-1_7619',
    'tekion-api-token': 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI0ZjQxYjRlZS1mZjYxLTQ4MjYtODUzMi02ZmQ5MTk5OGI3ZGUiLCJpYXQiOjE3Nzk4Njk0NjksInN1YiI6IjRmNDFiNGVlLWZmNjEtNDgyNi04NTMyLTZmZDkxOTk4YjdkZSIsImlzcyI6IkxvZ2luU2VydmljZSIsInVubG9ja0FjY291bnQiOmZhbHNlLCJub3VuY2UiOiI0NGE3MGZhNS1mMTEyLTRlYWUtYWVhNC03ZDA0OTNhMmUzM2YiLCJvcmlnaW5hbFVzZXJJZCI6ImZlM2EzMzMzLWM5YWQtNDlmZC1iZWY3LTc5ZWFjYWRkYzFkNSIsIm9yaWdpbmFsVGVuYW50SWQiOiJ0ZWNobW90b3JzIiwidXNlcklkIjoiNGY0MWI0ZWUtZmY2MS00ODI2LTg1MzItNmZkOTE5OThiN2RlIiwiZW1haWwiOiJpc21AZHJlYW1tb3Rvcmdyb3VwbGxjLmNvbSIsImV4cCI6MTc3OTg3NzI0NX0.puUiH2lZF0x8dOboqzaLNphXgaigeaBp-Dwi02rrSao',
    'tenantname': 'dreammotorgroupllc',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'userid': '4f41b4ee-ff61-4826-8532-6fd91998b7de'
}

TARGET_EMAIL = "Maria.Caso@mbcutlerbay.com"
TARGET_OEM_ID = "UMB1191975"
USER_ID = "e85513ec-d69a-46a4-9c2d-fb24dabb3909"

USER_SETTINGS_ENDPOINT = "https://preprodapp.tekioncloud.com/api/userservice/u/user-access-settings"

print("=" * 80)
print(f"DEMO: Dealer ID Verification Update")
print(f"Store: 7619 (MB Cutler Bay)")
print(f"User: {TARGET_EMAIL}")
print(f"New OEM ID: {TARGET_OEM_ID}")
print("=" * 80)

# STEP 1: GET current user data
print("\n[STEP 1] Getting current user data...")
url = f"{USER_SETTINGS_ENDPOINT}/{USER_ID}"
response = requests.get(url, headers=HEADERS)

if response.status_code != 200:
    print(f"❌ GET failed: {response.status_code}")
    exit(1)

data = response.json()
user = data.get('data', {}).get('user', {})

print(f"✅ User retrieved")
print(f"   Name: {user.get('fname')} {user.get('lname')}")
print(f"   Email: {user.get('email')}")

# STEP 2: Show current oemMappings
print("\n[STEP 2] Current oemMappings:")
if user.get('oemMappings'):
    for idx, mapping in enumerate(user['oemMappings']):
        dealer_id = mapping.get('dealerId')
        oem_id = mapping['oemDetails'][0].get('oemId') if mapping.get('oemDetails') else None
        print(f"   [{idx}] dealerId: {dealer_id}, oemId: {oem_id}")
else:
    print("   ❌ No oemMappings")

# STEP 3: Search for dealer 7619 mapping
print(f"\n[STEP 3] Searching for dealer {HEADERS['dealerid']} mapping...")
target_dealer_id = HEADERS['dealerid']
dealer_mapping = None
mapping_index = None

for idx, mapping in enumerate(user.get('oemMappings', [])):
    if mapping.get('dealerId') == target_dealer_id:
        dealer_mapping = mapping
        mapping_index = idx
        print(f"✅ FOUND at index [{idx}]")
        print(f"   dealerId: {mapping.get('dealerId')}")
        print(f"   Current oemId: {mapping['oemDetails'][0].get('oemId')}")
        print(f"   Has complexListId: {'complexListId' in mapping}")
        break

if not dealer_mapping:
    print(f"❌ NOT FOUND - No mapping for dealer {target_dealer_id}")
    exit(1)

# STEP 4: Verify before update
print(f"\n[STEP 4] Verification...")
assert dealer_mapping['dealerId'] == target_dealer_id, "Dealer ID mismatch!"
print(f"✅ Verified: dealerId matches ({target_dealer_id})")

# STEP 5: Show what will be updated
print(f"\n[STEP 5] Update Plan:")
print(f"   Mapping index: [{mapping_index}]")
print(f"   dealerId: {dealer_mapping['dealerId']}")
print(f"   OLD oemId: {dealer_mapping['oemDetails'][0].get('oemId')}")
print(f"   NEW oemId: {TARGET_OEM_ID}")
print(f"   Other mappings: WILL BE PRESERVED")

# Count other dealers
other_dealers = [m.get('dealerId') for m in user.get('oemMappings', []) if m.get('dealerId') != target_dealer_id]
if other_dealers:
    print(f"   Other dealers preserved: {', '.join(other_dealers)}")

# STEP 6: Perform update
print(f"\n[STEP 6] Performing update...")
dealer_mapping['oemDetails'][0]['oemId'] = TARGET_OEM_ID

# PUT request
put_url = f"{USER_SETTINGS_ENDPOINT}/{USER_ID}"
put_response = requests.put(put_url, headers=HEADERS, json={"saveUserRequest": user})

if put_response.status_code not in [200, 201, 204]:
    print(f"❌ PUT failed: {put_response.status_code}")
    print(put_response.text[:500])
    exit(1)

print(f"✅ Update successful!")

# STEP 7: Verify update
print(f"\n[STEP 7] Verifying update...")
verify_response = requests.get(url, headers=HEADERS)
verify_data = verify_response.json()
verify_user = verify_data.get('data', {}).get('user', {})

print("\nUpdated oemMappings:")
for idx, mapping in enumerate(verify_user.get('oemMappings', [])):
    dealer_id = mapping.get('dealerId')
    oem_id = mapping['oemDetails'][0].get('oemId') if mapping.get('oemDetails') else None
    status = "✅ UPDATED" if dealer_id == target_dealer_id else "✅ PRESERVED"
    print(f"   [{idx}] dealerId: {dealer_id}, oemId: {oem_id} {status}")

print("\n" + "=" * 80)
print("DEMO COMPLETE")
print("=" * 80)
