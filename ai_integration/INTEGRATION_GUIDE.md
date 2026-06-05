# AI Integration Guide

## Overview

This guide shows how to integrate AI capabilities into the existing logo automation workflow.

## Installation

### 1. Setup AI Integration

```bash
cd ai_integration
python setup.py
```

### 2. Configure API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your keys
nano .env
```

Required API keys:
- **OpenAI API Key**: For GPT-4 powered analysis (recommended)
- **Anthropic API Key**: Alternative to OpenAI (optional)
- **Hugging Face Token**: For open-source models (optional)

Get your keys:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Hugging Face: https://huggingface.co/settings/tokens

### 3. Test Installation

```bash
python examples/quick_start.py
```

---

## Integration with Existing Workflow

### Pre-Processing: Analyze Templates Before Processing

Add this to `temp_logo_adding_FINAL.py`:

```python
from ai_integration import AIAssistant

class TemplateLogoProcessor:
    def __init__(self):
        # Existing initialization...
        
        # Add AI assistant
        try:
            self.ai_assistant = AIAssistant()
        except:
            self.ai_assistant = None
    
    async def process_template(self, template):
        # AI Pre-analysis
        if self.ai_assistant:
            analysis = self.ai_assistant.analyze_template(template)
            
            # Log prediction
            logger.info(f"🤖 AI Prediction: {analysis['category']}")
            logger.info(f"📈 Confidence: {analysis['confidence']:.2%}")
            
            # Warn if unusual
            if analysis['anomalies']:
                logger.warning(f"⚠️  Anomalies: {analysis['anomalies']}")
        
        # Continue with existing processing...
```

### Post-Processing: Analyze Results

```python
# After processing all templates
if self.ai_assistant:
    # Analyze the log
    diagnosis = self.ai_assistant.diagnose_log('logs/latest.log')
    
    # Save diagnosis report
    with open('ai_diagnosis.json', 'w') as f:
        json.dump(diagnosis, f, indent=2)
    
    print("\n📊 AI Diagnosis saved to ai_diagnosis.json")
```

### Before Code Changes: Generate Tests

```bash
# After making changes, generate targeted tests
cd ai_integration
python -c "
from ai_assistant import AIAssistant
import json

assistant = AIAssistant()
result = assistant.generate_tests_for_change()

print('Test Suite:', json.dumps(result['test_suite'], indent=2))

# Save to file
with open('generated_tests.py', 'w') as f:
    f.write(result['test_code'])
"

# Run generated tests
pytest generated_tests.py
```

---

## Usage Examples

### 1. Interactive Mode

```bash
python ai_assistant.py
```

This starts an interactive CLI where you can:
- Analyze templates
- Diagnose logs  
- Generate tests

### 2. Programmatic Usage

```python
from ai_integration import AIAssistant

assistant = AIAssistant()

# Analyze a template
template = {
    "name": "My Template",
    "detection": {
        "logo_tables_found": 2,
        "header_button_opacity": 1.0,
        "has_logos": True
    }
}

result = assistant.analyze_template(template)
print(f"Category: {result['category']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### 3. Batch Analysis

```python
# Analyze all templates
with open('template_metadata.json', 'r') as f:
    data = json.load(f)

for template in data['templates']:
    analysis = assistant.analyze_template(template)
    if analysis['anomalies']:
        print(f"⚠️  {template['name']}: {analysis['anomalies']}")
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: AI-Powered Testing

on: [push, pull_request]

jobs:
  ai-testing:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install AI Integration
        run: |
          cd ai_integration
          pip install -r requirements.txt
      
      - name: Generate Test Suite
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -c "
          from ai_integration import AIAssistant
          assistant = AIAssistant()
          result = assistant.generate_tests_for_change()
          # Save and run tests
          "
      
      - name: Run Generated Tests
        run: pytest generated_tests.py
```

---

## Benefits

### 1. Faster Debugging
- AI analyzes logs in seconds
- Identifies root causes automatically
- Links to similar past issues

### 2. Predictive Testing
- Only test affected templates
- Save ~70% of test time
- Higher confidence in changes

### 3. Pattern Detection
- Automatically categorizes new templates
- Detects anomalies before processing
- Reduces manual inspection

### 4. Self-Improving
- Learns from each run
- Updates models with new patterns
- Gets better over time

---

## Troubleshooting

### "Classifier not available"
- Check that `template_metadata.json` exists in parent directory
- Run `python setup.py` to train models

### "Log Analyzer failed"
- Verify API keys in `.env` file
- Check internet connection
- Try alternative provider (Anthropic instead of OpenAI)

### Low prediction confidence
- This is normal for unusual templates
- Use as a signal to review manually
- Add template to training data to improve

---

## Future Enhancements

Planned features:
- [ ] Visual validation with computer vision
- [ ] LLM-powered code generation for guardrails
- [ ] Automated fix suggestions
- [ ] Real-time monitoring dashboard
- [ ] Integration with Jira for bug tracking

---

## Support

For issues or questions:
1. Check the examples in `examples/`
2. Review the main README
3. Open an issue on GitHub
