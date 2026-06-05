"""
Quick Start Examples for AI Integration

This script demonstrates how to use the AI components.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_integration.ai_assistant import AIAssistant
import json


def example_1_classify_template():
    """Example 1: Classify a template."""
    print("\n" + "="*60)
    print("Example 1: Template Classification")
    print("="*60 + "\n")
    
    assistant = AIAssistant()
    
    # Example template data
    template = {
        "name": "Test Template",
        "id": "test_123",
        "departments": ["SERVICE"],
        "detection": {
            "logo_tables_found": 2,
            "header_button_opacity": 1.0,
            "has_logos": True,
            "logo_count": 2,
            "logo_type": "resizable images"
        }
    }
    
    result = assistant.analyze_template(template)
    
    print("📊 Analysis Result:")
    print(json.dumps(result, indent=2))
    print(f"\n✅ Category: {result.get('category', 'Unknown')}")
    print(f"📈 Confidence: {result.get('confidence', 0):.2%}")


def example_2_analyze_log():
    """Example 2: Analyze a log file."""
    print("\n" + "="*60)
    print("Example 2: Log Analysis")
    print("="*60 + "\n")
    
    assistant = AIAssistant()
    
    # Find most recent log
    log_dir = '../logs'
    if os.path.exists(log_dir):
        logs = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if logs:
            latest_log = max(logs, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
            log_path = os.path.join(log_dir, latest_log)
            
            print(f"📄 Analyzing: {log_path}\n")
            
            result = assistant.diagnose_log(log_path)
            
            print("🔍 Diagnosis:")
            print(json.dumps(result, indent=2))
        else:
            print("❌ No log files found")
    else:
        print("❌ Log directory not found")


def example_3_generate_tests():
    """Example 3: Generate test suite."""
    print("\n" + "="*60)
    print("Example 3: Test Generation")
    print("="*60 + "\n")
    
    assistant = AIAssistant()
    
    # Example code change
    code_diff = """
    diff --git a/temp_logo_adding_FINAL.py b/temp_logo_adding_FINAL.py
    @@ -1450,6 +1450,10 @@
    
    +// FIX #8: New guardrail for something
    +if (logoTablesCount > MAX_LOGO_TABLES) {
    +    return { error: 'Too many logo tables' };
    +}
    """
    
    result = assistant.generate_tests_for_change(code_diff)
    
    print("📋 Test Suite Generated:")
    print(f"Risk Level: {result['test_suite']['risk_level']}")
    print(f"Templates to test: {result['test_suite']['total_templates']}")
    print(f"\nRationale:")
    for reason in result['test_suite']['rationale']:
        print(f"  - {reason}")


def example_4_batch_analysis():
    """Example 4: Batch analyze all templates."""
    print("\n" + "="*60)
    print("Example 4: Batch Template Analysis")
    print("="*60 + "\n")
    
    assistant = AIAssistant()
    
    # Load all templates
    with open('../template_metadata.json', 'r') as f:
        data = json.load(f)
        templates = data['templates']
    
    print(f"📊 Analyzing {len(templates)} templates...\n")
    
    # Analyze each template
    anomalies_found = 0
    low_confidence = []
    
    for template in templates[:5]:  # Just first 5 for demo
        result = assistant.analyze_template(template)
        
        if result.get('anomalies'):
            anomalies_found += 1
            print(f"⚠️  {template['name']}: {result['anomalies']}")
        
        if result.get('confidence', 1.0) < 0.7:
            low_confidence.append(template['name'])
    
    print(f"\n📈 Summary:")
    print(f"   Anomalies detected: {anomalies_found}")
    print(f"   Low confidence predictions: {len(low_confidence)}")
    if low_confidence:
        print(f"   Templates: {', '.join(low_confidence)}")


def main():
    """Run all examples."""
    print("\n🚀 AI Integration Quick Start Examples")
    print("="*60)
    
    examples = [
        ("Template Classification", example_1_classify_template),
        ("Log Analysis", example_2_analyze_log),
        ("Test Generation", example_3_generate_tests),
        ("Batch Analysis", example_4_batch_analysis)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n\n▶️  Running Example {i}: {name}")
        try:
            func()
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\n⏸️  Press Enter to continue...")
    
    print("\n\n✅ All examples completed!")


if __name__ == '__main__':
    main()
