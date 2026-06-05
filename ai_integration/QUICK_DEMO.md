# Quick Demo - AI Integration

## Installation (5 minutes)

```bash
cd ai_integration

# Install dependencies
pip3 install -r requirements.txt

# Or install minimal set
pip3 install scikit-learn numpy pandas
```

## Demo 1: Train the Pattern Classifier

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '..')
from ai_integration.pattern_classifier import TemplateClassifier

print("🤖 Training AI model on your 39 templates...")
classifier = TemplateClassifier()
print("\n✅ Training complete!")
EOF
```

Expected output:
```
🤖 Training template classifier...
✅ Training accuracy: 100.00%
📊 Trained on 39 templates
🏷️  Categories: 6
```

## Demo 2: Classify a Template

```bash
python3 << 'EOF'
import sys
import json
sys.path.insert(0, '..')
from ai_integration.pattern_classifier import TemplateClassifier

# Load classifier
classifier = TemplateClassifier()

# Example template
template = {
    "name": "Test Template",
    "departments": ["SERVICE"],
    "detection": {
        "logo_tables_found": 2,
        "header_button_opacity": 1.0,
        "has_logos": True,
        "logo_count": 2,
        "logo_type": "resizable images"
    }
}

# Predict
result = classifier.predict(template)

print("\n📊 Prediction Results:")
print(f"Category: {result['category']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Anomalies: {result['anomalies']}")
print(f"\nFeatures analyzed:")
print(json.dumps(result['features'], indent=2))
EOF
```

## Demo 3: Analyze a Log (Pattern-Based)

```bash
python3 << 'EOF'
import sys
import json
sys.path.insert(0, '..')
from ai_integration.log_analyzer import AILogAnalyzer

# Create analyzer (works without API key)
analyzer = AILogAnalyzer()

# Find latest log
import os
log_dir = '../logs'
if os.path.exists(log_dir):
    logs = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if logs:
        latest = max(logs, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
        log_path = os.path.join(log_dir, latest)
        
        print(f"🔍 Analyzing: {latest}\n")
        
        result = analyzer.diagnose_failure(log_path)
        
        print(f"Analysis Type: {result['analysis_type']}")
        print(f"Errors Found: {result['errors_found']}")
        
        if result.get('patterns_matched'):
            print("\n🎯 Issues Detected:")
            for error in result['patterns_matched'][:3]:
                print(f"\n  Template: {error['template']}")
                print(f"  Type: {error['error_type']}")
                print(f"  Cause: {error['cause']}")
                print(f"  Fix: {error['fix']}")
        
        print(f"\n💡 Suggestions:")
        for suggestion in result.get('suggestions', []):
            print(f"  - {suggestion}")
    else:
        print("No logs found")
else:
    print("Log directory not found")
EOF
```

## Demo 4: Generate Tests

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '..')
from ai_integration.test_generator import TestGenerator

generator = TestGenerator()

# Simulate a code change
code_diff = """
@@ -1450,6 +1450,10 @@
 
 // FIX #1: STATE SYNCHRONIZATION
 const globalLogoRowsWithContent = new Set();
+
+// NEW: Additional guardrail
+if (logoTablesCount > MAX_LOGO_TABLES) {
+    return { error: 'Too many logo tables' };
+}
"""

print("🔍 Analyzing code change impact...\n")

# Analyze impact
impact = generator.analyze_code_change(code_diff)

print(f"Affects detection: {impact['affects_detection']}")
print(f"Affects guardrails: {impact['affects_guardrails']}")
print(f"Risk level: {impact['risk_level']}")
print(f"Affected categories: {len(impact['affected_categories'])}")

# Generate tests
test_suite = generator.generate_test_suite(impact)

print(f"\n📋 Test Suite:")
print(f"Total templates to test: {test_suite['total_templates']}")
print(f"Risk level: {test_suite['risk_level']}")
print(f"\nRationale:")
for reason in test_suite['rationale']:
    print(f"  - {reason}")
EOF
```

## Demo 5: Interactive Mode

```bash
python3 ai_assistant.py
```

Then try:
1. Analyze a template
2. Diagnose a log
3. Generate tests

## With OpenAI API (Optional)

If you have an OpenAI API key:

```bash
# Add to .env
echo "OPENAI_API_KEY=your_key_here" >> .env

# Run AI-powered log analysis
python3 << 'EOF'
import sys
sys.path.insert(0, '..')
from ai_integration.ai_assistant import AIAssistant

assistant = AIAssistant()

# This will use GPT-4 for deep analysis
result = assistant.diagnose_log('../logs/latest.log')

print(result['ai_analysis'])
EOF
```

## Troubleshooting

### "No module named sklearn"
```bash
pip3 install scikit-learn
```

### "No module named openai"
```bash
pip3 install openai
# Or skip - pattern-based analysis works without it
```

### "template_metadata.json not found"
```bash
# Make sure you're in the ai_integration directory
cd ai_integration
# The file should be one level up
ls ../template_metadata.json
```

## Next Steps

1. ✅ Run these demos to see AI in action
2. ✅ Review `INTEGRATION_GUIDE.md` for integration
3. ✅ Add OpenAI key for advanced features (optional)
4. ✅ Customize for your workflow

Enjoy! 🚀
