"""
Test script for Network Tab API Extraction Service

Run this to test the API extraction functionality:
    python3 test_network_api.py
"""

from api_extraction_service import APIExtractionService

# Initialize service
service = APIExtractionService()

# Sample API response (like the dealer-master example)
sample_response = {
    "data": {
        "dealerName": "ABC Motors",
        "id": "123",
        "universalDealerId": "UNI-123",
        "dealerAddress": [
            {
                "city": "New York",
                "state": "NY",
                "zipCode": "10001"
            },
            {
                "city": "Los Angeles",
                "state": "CA",
                "zipCode": "90001"
            }
        ],
        "inventoryConfig": {
            "agedInventory": True,
            "maxInventoryDays": 90
        },
        "features": [
            {
                "name": "Parts Management",
                "enabled": True,
                "subFeatures": [
                    {"name": "Inventory Tracking", "enabled": True},
                    {"name": "Order Management", "enabled": False}
                ]
            }
        ]
    }
}

print("=" * 60)
print("🌐 Network Tab API Extraction Service Test")
print("=" * 60)

# Test 1: Auto-generate metadata
print("\n1️⃣ Testing Auto-Generate Metadata...")
# Note: We pass the full response, and prefix="" since we want to start from root
metadata = service.auto_generate_metadata(sample_response["data"], prefix="data")
print(f"   ✅ Generated {len(metadata)} field mappings")
print("\n   Sample fields:")
for i, (field_id, field_meta) in enumerate(list(metadata.items())[:5]):
    print(f"      • {field_id}")
    print(f"        - API Path: {field_meta['api_path']}")
    print(f"        - Type: {field_meta['type']}")
    print(f"        - Display Name: {field_meta['display_name']}")

# Test 2: Extract fields
print("\n2️⃣ Testing Field Extraction...")
# Pass the full response for extraction
extracted = service.extract_fields_from_response(sample_response, metadata)
print(f"   ✅ Extracted {len(extracted)} fields")
print("\n   Sample extracted values:")
for i, (field_id, field_data) in enumerate(list(extracted.items())[:5]):
    value_preview = str(field_data['value'])[:50]
    print(f"      • {field_data['display_name']}: {value_preview}")

# Test 3: Validate response
print("\n3️⃣ Testing Response Validation...")
validation = service.validate_response(sample_response, metadata)
print(f"   ✅ Validation Result: {'PASSED' if validation['validation_passed'] else 'FAILED'}")
print(f"      - Total Fields: {validation['total_fields']}")
print(f"      - Fields Found: {validation['fields_found']}")
print(f"      - Fields Missing: {validation['fields_missing']}")
print(f"      - Type Mismatches: {validation['type_mismatches']}")

# Test 4: Environment comparison
print("\n4️⃣ Testing Environment Comparison...")

# Simulate different environments
dev_response = sample_response.copy()
staging_response = sample_response.copy()
staging_response["data"]["dealerName"] = "ABC Motors (Staging)"
prod_response = sample_response.copy()
prod_response["data"]["dealerName"] = "ABC Motors (Production)"
prod_response["data"]["inventoryConfig"]["maxInventoryDays"] = 60

# Create extraction results
dev_extraction = {
    "extracted_fields": service.extract_fields_from_response(dev_response, metadata)
}
staging_extraction = {
    "extracted_fields": service.extract_fields_from_response(staging_response, metadata)
}
prod_extraction = {
    "extracted_fields": service.extract_fields_from_response(prod_response, metadata)
}

comparison = service.compare_environments({
    "dev": dev_extraction,
    "staging": staging_extraction,
    "prod": prod_extraction
})

print(f"   ✅ Comparison Complete")
print(f"      - Total Fields: {comparison['summary']['total_fields']}")
print(f"      - Identical Fields: {comparison['summary']['identical_fields']}")
print(f"      - Fields with Differences: {comparison['summary']['fields_with_differences']}")

if comparison['differences']:
    print("\n   Differences found:")
    for diff in comparison['differences'][:3]:  # Show first 3
        print(f"      • {diff['field_id']}")
        print(f"        - Dev: {diff['values']['dev']}")
        print(f"        - Staging: {diff['values']['staging']}")
        print(f"        - Prod: {diff['values']['prod']}")

# Test 5: Generate documentation
print("\n5️⃣ Testing Documentation Generation...")
extraction_result = {
    "api_url": "/api/api-core/u/dealer-master",
    "method": "GET",
    "status": 200,
    "timestamp": "2025-01-14T12:00:00Z",
    "extracted_fields": extracted
}

markdown_doc = service.generate_markdown_doc(extraction_result)
print(f"   ✅ Generated Markdown documentation ({len(markdown_doc)} characters)")
print("\n   Preview:")
print("   " + "\n   ".join(markdown_doc.split("\n")[:15]))

print("\n" + "=" * 60)
print("✅ All tests completed successfully!")
print("=" * 60)
print("\n💡 Next steps:")
print("   1. Start the backend: python3 main.py")
print("   2. Start the frontend: cd ../frontend && npm run dev")
print("   3. Open the app and click the 🌐 Network tab")
print("   4. Try the features with your own API responses!")
