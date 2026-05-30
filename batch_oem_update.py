#!/usr/bin/env python3
"""
Batch OEM ID Update Script
Processes all 192 users from oemexcel.csv
"""

import requests
import json
import csv
import time
from datetime import datetime

# Headers (Fresh from user)
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'applicationid': 'ARC_NA',
    'clientid': 'web',
    'content-type': 'application/json',
    'dealerid': '7616',
    'dnt': '1',
    'flattenedaecprogramsmap': '',
    'locale': 'en_US',
    'origin': 'https://preprodapp.tekioncloud.com',
    'original-tenantid': 'techmotors',
    'original-userid': 'fe3a3333-c9ad-49fd-bef7-79eacaddc1d5',
    'priority': 'u=1, i',
    'productids': 'ARC',
    'program': 'DEFAULT',
    'roleid': '7616_ISM_Admin',
    'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'subapplicationid': 'US',
    'tek-siteid': '-1_7616',
    'tekion-api-token': 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI0ZjQxYjRlZS1mZjYxLTQ4MjYtODUzMi02ZmQ5MTk5OGI3ZGUiLCJpYXQiOjE3Nzk3OTcwMDEsInN1YiI6IjRmNDFiNGVlLWZmNjEtNDgyNi04NTMyLTZmZDkxOTk4YjdkZSIsImlzcyI6IkxvZ2luU2VydmljZSIsInVubG9ja0FjY291bnQiOmZhbHNlLCJub3VuY2UiOiI2MDMyNzg3YS1kNjgxLTRjODQtOTBmYy0zYzI4NTNiMjM1ZDMiLCJvcmlnaW5hbFVzZXJJZCI6ImZlM2EzMzMzLWM5YWQtNDlmZC1iZWY3LTc5ZWFjYWRkYzFkNSIsIm9yaWdpbmFsVGVuYW50SWQiOiJ0ZWNobW90b3JzIiwidXNlcklkIjoiNGY0MWI0ZWUtZmY2MS00ODI2LTg1MzItNmZkOTE5OThiN2RlIiwiZW1haWwiOiJpc21AZHJlYW1tb3Rvcmdyb3VwbGxjLmNvbSIsImV4cCI6MTc3OTgwNDc3N30.TAB6tkO5j4HgMsfTAzWJdb735iqlcxjhRmQq99MJRjY',
    'tenantname': 'dreammotorgroupllc',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'userid': '4f41b4ee-ff61-4826-8532-6fd91998b7de',
}

# Base URLs
BASE_URL = "https://preprodapp.tekioncloud.com"
USER_ROLES_ENDPOINT = f"{BASE_URL}/api/userservice/u/v2/userandroles"
USER_SETTINGS_ENDPOINT = f"{BASE_URL}/api/userservice/u/user-access-settings"

# File paths
CSV_INPUT = "/Users/tlreddy/Documents/project-1-child/oemexcel.csv"
CSV_OUTPUT = "/Users/tlreddy/Documents/project-1-child/oemexcel_results.csv"

def fetch_all_users():
    """Fetch all active users from Tekion"""
    print("\n" + "="*80)
    print("FETCHING ALL USERS FROM TEKION")
    print("="*80)
    
    all_users = []
    start = 0
    page_size = 200
    
    while True:
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
        
        if response.status_code != 200:
            print(f"❌ Error fetching users: {response.status_code}")
            break
        
        data = response.json()
        users = data.get('data', {}).get('userAndRoleResponses', [])
        total_count = data.get('data', {}).get('count', 0)
        
        if not users:
            break
        
        all_users.extend(users)
        print(f"   Fetched {len(all_users)} / {total_count} users")
        
        if len(all_users) >= total_count:
            break
        
        start += page_size
    
    print(f"✅ Total users: {len(all_users)}\n")
    return all_users

def load_csv_data():
    """Load OEM data from CSV"""
    print("="*80)
    print("LOADING CSV DATA")
    print("="*80)
    
    oem_data = []
    with open(CSV_INPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            oem_data.append({
                'oemId': row['oemId'],
                'email': row['email'],
                'status': ''
            })
    
    print(f"✅ Loaded {len(oem_data)} rows from CSV\n")
    return oem_data

def get_oem_template(all_users, target_dealer_id):
    """Extract OEM template from first user with oemMappings for this dealer"""
    for user in all_users:
        if user.get('oemMappings'):
            for mapping in user['oemMappings']:
                if mapping.get('dealerId') == target_dealer_id and mapping.get('oemDetails'):
                    template = {
                        'dealerId': target_dealer_id,
                        'oem': mapping['oemDetails'][0].get('oem', 'benz'),
                        'make': mapping['oemDetails'][0].get('makeOverrides', [{}])[0].get('make', 'mercedesbenz'),
                        'makeOverrideDisabled': mapping['oemDetails'][0].get('makeOverrideDisabled', True)
                    }
                    return template

    # Fallback if no template found
    return {
        'dealerId': target_dealer_id,
        'oem': 'benz',
        'make': 'mercedesbenz',
        'makeOverrideDisabled': True
    }


def update_user_oem(user_id, new_oem_id, oem_template):
    """
    Update OEM ID for a single user with dealer ID verification.
    ONLY updates the mapping that matches HEADERS['dealerid'].
    """
    # GET current user data
    url = f"{USER_SETTINGS_ENDPOINT}/{user_id}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        raise Exception(f"GET failed: {response.status_code}")

    data = response.json()
    user = data.get('data', {}).get('user', {})

    # Get target dealer from headers
    target_dealer_id = HEADERS['dealerid']

    # CRITICAL: Search for mapping that matches current dealer
    dealer_mapping = None
    for mapping in user.get('oemMappings', []):
        if mapping.get('dealerId') == target_dealer_id:
            dealer_mapping = mapping
            break

    old_oem_id = None
    scenario = None

    if dealer_mapping:
        # FOUND: This user has a mapping for the current dealer
        old_oem_id = dealer_mapping['oemDetails'][0].get('oemId', '')

        # Check if this is NEW or EXISTING OEM ID
        has_complex_id = 'complexListId' in dealer_mapping

        if has_complex_id:
            # SCENARIO 1: EXISTING OEM ID - Preserve complexListId
            dealer_mapping['oemDetails'][0]['oemId'] = new_oem_id
            scenario = 'EXISTING'
        else:
            # SCENARIO 2: NEW OEM ID - Remove complexListId if present
            dealer_mapping['oemDetails'][0]['oemId'] = new_oem_id

            # Remove complexListId at oemMappings level
            if 'complexListId' in dealer_mapping:
                del dealer_mapping['complexListId']

            # Remove complexListId at oemDetails level
            if 'complexListId' in dealer_mapping['oemDetails'][0]:
                del dealer_mapping['oemDetails'][0]['complexListId']

            # Remove complexListId from makeOverrides
            if 'makeOverrides' in dealer_mapping['oemDetails'][0]:
                for override in dealer_mapping['oemDetails'][0]['makeOverrides']:
                    if 'complexListId' in override:
                        del override['complexListId']

            scenario = 'NEW'

    else:
        # NOT FOUND: This user doesn't have a mapping for current dealer
        # CREATE new mapping for this dealer

        # Ensure oemMappings array exists
        if not user.get('oemMappings'):
            user['oemMappings'] = []

        # Create new mapping using template
        new_mapping = {
            "dealerId": oem_template['dealerId'],
            "oemDetails": [
                {
                    "oem": oem_template['oem'],
                    "oemId": new_oem_id,
                    "makeOverrideDisabled": oem_template['makeOverrideDisabled'],
                    "makeOverrides": [
                        {
                            "make": oem_template['make'],
                            "oemId": None
                        }
                    ]
                }
            ]
        }

        # APPEND to existing mappings (preserves other dealers)
        user['oemMappings'].append(new_mapping)
        old_oem_id = None
        scenario = 'CREATED'

    # PUT updated user
    put_url = f"{USER_SETTINGS_ENDPOINT}/{user_id}"
    put_response = requests.put(put_url, headers=HEADERS, json={"saveUserRequest": user})

    if put_response.status_code not in [200, 201, 204]:
        raise Exception(f"PUT failed: {put_response.status_code}")

    return old_oem_id, scenario

def main():
    start_time = datetime.now()
    
    print("\n" + "🚀"*40)
    print("BATCH OEM ID UPDATE")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀"*40)
    
    # Load CSV
    oem_data = load_csv_data()

    # Fetch all Tekion users
    tekion_users = fetch_all_users()

    # Extract OEM template from existing users
    target_dealer_id = HEADERS['dealerid']
    print("\n" + "="*80)
    print(f"EXTRACTING OEM TEMPLATE FOR DEALER {target_dealer_id}")
    print("="*80)
    oem_template = get_oem_template(tekion_users, target_dealer_id)
    print(f"✅ Template extracted:")
    print(f"   dealerId: {oem_template['dealerId']}")
    print(f"   oem: {oem_template['oem']}")
    print(f"   make: {oem_template['make']}")
    print(f"   makeOverrideDisabled: {oem_template['makeOverrideDisabled']}")

    # Create email -> user mapping (case-insensitive)
    user_map = {u.get('email', '').lower(): u for u in tekion_users}

    # Process each row
    print("="*80)
    print("PROCESSING OEM UPDATES")
    print("="*80)

    for i, row in enumerate(oem_data):
        email = row['email'].lower()
        new_oemid = row['oemId']

        print(f"\n[{i+1}/{len(oem_data)}] {row['email']}")

        # Find user
        tekion_user = user_map.get(email)

        if not tekion_user:
            row['status'] = 'Email not found in Tekion'
            print(f"   ❌ Not found")
            continue

        if not new_oemid or new_oemid.strip() == '':
            row['status'] = 'Skipped - no oemId'
            print(f"   ⚠️ No OEM ID")
            continue

        try:
            user_id = tekion_user.get('id')
            old_oemid, scenario = update_user_oem(user_id, new_oemid, oem_template)
            row['status'] = 'Done'

            # Show the scenario type
            if scenario == 'CREATED':
                print(f"   ✅ Created ({scenario}): [NONE] → {new_oemid}")
            else:
                print(f"   ✅ Updated ({scenario}): {old_oemid} → {new_oemid}")
        except Exception as e:
            row['status'] = f'Error: {str(e)[:50]}'
            print(f"   ❌ Error: {str(e)[:50]}")

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    # Save results
    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)

    with open(CSV_OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['oemId', 'email', 'status'])
        writer.writeheader()
        writer.writerows(oem_data)

    print(f"✅ Results saved to: {CSV_OUTPUT}")

    # Summary
    success_count = sum(1 for r in oem_data if r['status'] == 'Done')
    fail_count = len(oem_data) - success_count

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total rows: {len(oem_data)}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()
