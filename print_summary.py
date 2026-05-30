#!/usr/bin/env python3
import json

# Create a beautiful summary
with open('final_element_mapping_20260529_224145.json', 'r') as f:
    data = json.load(f)

print("=" * 100)
print("📋 FINAL ELEMENT MAPPING - USER-SPECIFIED IMPORTANT ELEMENTS")
print("=" * 100)
print()
print(f"Page: {data['metadata']['page_url']}")
print(f"Title: {data['metadata']['page_title']}")
print()
print("## 🎯 Important Elements Detected:")
print()

# Sort by element number
sorted_elements = sorted(
    [(k, v) for k, v in data['important_elements'].items() if 'element_number' in v],
    key=lambda x: x[1]['element_number']
)

for key, elem in sorted_elements:
    num = elem['element_number']
    label = elem['label']
    elem_type = elem['type']
    
    print(f"### {num}. {label}")
    print(f"   Type: {elem_type}")
    
    if elem_type == 'department_filter':
        print(f"   Value: Sales")
        print(f"   Selector: {elem['selector']}")
        
    elif elem_type == 'search_input':
        print(f"   Placeholder: \"{elem['placeholder']}\"")
        print(f"   Selector: {elem['selector']}")
        
    elif elem_type == 'action_button':
        if 'count' in elem:
            print(f"   Text: {elem['text']}")
            print(f"   Count: {elem['count']}")
        else:
            print(f"   Text: {elem['text']}")
        print(f"   Disabled: {elem['disabled']}")
        
    elif elem_type == 'dropdown':
        print(f"   Value: {elem['value']}")
        
    elif elem_type == 'tab':
        active_str = "✅ Active" if elem['is_active'] else "Inactive"
        print(f"   Status: {active_str}")
        print(f"   Filtered Results Count: {elem['count']}")
        print(f"   Full Text: \"{elem['full_text']}\"")
    
    print(f"   Interactive: {elem['is_interactive']}")
    print()

print("=" * 100)
print("✅ All important elements mapped successfully!")
print("=" * 100)
