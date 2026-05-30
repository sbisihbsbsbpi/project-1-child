"""
Test script for API interception functionality

Run this to verify the API interception endpoints work:
    python3 test_api_interception.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("🌐 Testing API Interception Endpoints")
print("=" * 60)

# Test 1: Get intercepted APIs (should be empty initially)
print("\n1️⃣ Testing GET /api/network/intercepted-apis...")
try:
    response = requests.get(f"{BASE_URL}/api/network/intercepted-apis")
    result = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Count: {result.get('count', 0)}")
    print(f"   📋 APIs: {len(result.get('apis', []))}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Add a manual API
print("\n2️⃣ Testing POST /api/network/add-manual-api...")
try:
    test_api = {
        "url": "/api/test/dealer-master",
        "method": "GET",
        "status": 200,
        "response_json": {
            "data": {
                "dealerName": "Test Motors",
                "id": "TEST123",
                "dealerAddress": [
                    {
                        "city": "San Francisco",
                        "state": "CA",
                        "zipCode": "94102"
                    }
                ]
            }
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/network/add-manual-api",
        json=test_api
    )
    result = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📝 Message: {result.get('message')}")
    if result.get('api'):
        api = result['api']
        print(f"   🆔 API ID: {api.get('id')}")
        print(f"   🔗 URL: {api.get('url')}")
        print(f"   📊 Status: {api.get('status')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get intercepted APIs again (should have 1 now)
print("\n3️⃣ Testing GET /api/network/intercepted-apis (after adding)...")
try:
    response = requests.get(f"{BASE_URL}/api/network/intercepted-apis")
    result = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Count: {result.get('count', 0)}")

    if result.get('apis'):
        print(f"\n   📋 Intercepted APIs:")
        for i, api in enumerate(result['apis'][:3], 1):  # Show first 3
            print(f"      {i}. [{api.get('method')}] {api.get('url')} (Status: {api.get('status')})")
            if api.get('page_url'):
                print(f"         From: {api.get('page_url')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Test metadata generation with intercepted API
print("\n4️⃣ Testing metadata generation with intercepted API...")
try:
    # Get the first API
    response = requests.get(f"{BASE_URL}/api/network/intercepted-apis")
    result = response.json()

    if result.get('apis') and len(result['apis']) > 0:
        api = result['apis'][0]
        response_data = api.get('response_json', {})

        # Generate metadata
        metadata_response = requests.post(
            f"{BASE_URL}/api/network/generate-metadata",
            json={
                "data": response_data,
                "prefix": "data",
                "max_depth": 10
            }
        )

        metadata_result = metadata_response.json()
        print(f"   ✅ Status: {metadata_response.status_code}")
        print(f"   📊 Field Count: {metadata_result.get('field_count', 0)}")

        if metadata_result.get('metadata'):
            print(f"\n   📋 Sample Fields:")
            for i, (field_id, field_meta) in enumerate(list(metadata_result['metadata'].items())[:3], 1):
                print(f"      {i}. {field_id}")
                print(f"         - Display Name: {field_meta.get('display_name')}")
                print(f"         - Type: {field_meta.get('type')}")
    else:
        print("   ⚠️  No APIs available to test metadata generation")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Clear all APIs
print("\n5️⃣ Testing DELETE /api/network/intercepted-apis...")
try:
    response = requests.delete(f"{BASE_URL}/api/network/intercepted-apis")
    result = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📝 Message: {result.get('message')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Verify APIs are cleared
print("\n6️⃣ Testing GET /api/network/intercepted-apis (after clearing)...")
try:
    response = requests.get(f"{BASE_URL}/api/network/intercepted-apis")
    result = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Count: {result.get('count', 0)}")

    if result.get('count') == 0:
        print("   ✅ APIs successfully cleared!")
    else:
        print(f"   ⚠️  Expected 0 APIs, found {result.get('count')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ All API interception tests completed!")
print("=" * 60)
print("\n💡 Next steps:")
print("   1. Load a URL in Real Browser mode")
print("   2. Check Network tab for intercepted APIs")
print("   3. Select an API from the dropdown")
print("   4. Generate metadata automatically!")
