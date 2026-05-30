#!/usr/bin/env python3
"""
Check the actual template body JSON to understand logo placement
"""

import json

# Load the analysis file
with open('template_analysis_667f0befd4964026ee7b6ea4.json', 'r') as f:
    analysis = json.load(f)

print("=" * 100)
print("TEMPLATE BODY JSON ANALYSIS")
print("=" * 100)
print()

# The analysis doesn't save the full body - let's load from API verification file
try:
    with open('api_verification_20260530_005712.json', 'r') as f:
        api_data = json.load(f)
    
    # Find our template
    template = None
    for t in api_data.get('after', {}).get('hits', []):
        if t.get('templateId') == '667f0befd4964026ee7b6ea4':
            template = t
            break
    
    if template:
        print("✅ Found template in API data")
        print()
        
        # Check thumbnail
        if 'thumbnail' in template:
            print("📸 THUMBNAIL:")
            print(f"   Media ID: {template['thumbnail'].get('mediaId')}")
            print(f"   Name: {template['thumbnail'].get('name')}")
            print()
        
        # Parse body
        body_str = template.get('body')
        if body_str:
            body = json.loads(body_str) if isinstance(body_str, str) else body_str
            
            print(f"📄 BODY COMPONENTS: {len(body)} total")
            print()
            
            for idx, component in enumerate(body):
                comp_key = component.get('key', 'UNKNOWN')
                print(f"{idx + 1}. {comp_key}")
                
                # Check for logo/thumbnail references
                comp_html = str(component.get('componentProps', {}))
                
                if 'THUMBNAIL' in comp_html.upper():
                    print(f"   🎯 CONTAINS THUMBNAIL REFERENCE!")
                    print(f"   Component Props: {component.get('componentProps')}")
                
                if any(keyword in comp_html.upper() for keyword in ['LOGO', 'FOOTER', 'BRANDING']):
                    print(f"   📍 Potential logo location: {comp_key}")
                    html = component.get('componentProps', {}).get('html', '')
                    if html:
                        # Show first 200 chars of HTML
                        preview = html[:200] + '...' if len(html) > 200 else html
                        print(f"   HTML preview: {preview}")
                
                print()
        
        print("=" * 100)
        print("SEARCHING FOR THUMBNAIL_URL TEMPLATE VARIABLE")
        print("=" * 100)
        print()
        
        # Search entire body for {{THUMBNAIL_URL}}
        body_full_str = json.dumps(body, indent=2)
        if '{{THUMBNAIL_URL}}' in body_full_str:
            print("✅ FOUND {{THUMBNAIL_URL}} in body!")
            lines = body_full_str.split('\\n')
            for i, line in enumerate(lines):
                if 'THUMBNAIL_URL' in line:
                    print(f"   Line {i}: {line}")
        else:
            print("❌ No {{THUMBNAIL_URL}} found in body")
            print("   This means the thumbnail is injected by the email system outside the body HTML")
    
    else:
        print("❌ Template not found in API data")

except FileNotFoundError:
    print("❌ API verification file not found")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
