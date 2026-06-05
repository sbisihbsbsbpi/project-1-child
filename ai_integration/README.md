# AI Integration for Logo Automation

This module adds AI-powered capabilities to the logo automation system to detect and fix logic issues automatically.

## 🎯 Objectives

1. **Pattern Detection**: Automatically identify template categories and anomalies
2. **Smart Testing**: Generate targeted test cases based on code changes
3. **Log Analysis**: AI-powered root cause analysis from logs
4. **Visual Validation**: Computer vision for logo detection verification
5. **Code Suggestions**: LLM-powered guardrail generation

## 📦 Components

### 1. Template Pattern Classifier (`pattern_classifier.py`)
- Analyzes template DOM structures
- Classifies templates into categories
- Predicts expected logo table counts
- Flags structural anomalies

### 2. AI Log Analyzer (`log_analyzer.py`)
- Parses automation logs
- Identifies failure patterns
- Suggests fixes based on historical data
- Links to similar past issues

### 3. Test Generator (`test_generator.py`)
- Analyzes code changes
- Predicts affected templates
- Generates targeted test suites
- Estimates regression risk

### 4. Visual Validator (`visual_validator.py`)
- Screenshot-based logo detection
- Cross-validates with DOM detection
- Detects visual anomalies
- Confidence scoring

### 5. Guardrail Suggester (`guardrail_suggester.py`)
- LLM-powered code generation
- Suggests new guardrails for edge cases
- Validates generated code
- Integrates with existing logic

## 🚀 Quick Start

### Installation

```bash
cd ai_integration
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - OpenAI API key (for GPT-4)
   - Hugging Face token (for open-source models)

### Basic Usage

```python
from ai_integration.pattern_classifier import TemplateClassifier
from ai_integration.log_analyzer import AILogAnalyzer

# Classify a template
classifier = TemplateClassifier()
result = classifier.analyze_template(template_dom)
print(f"Category: {result['category']}")
print(f"Expected logos: {result['expected_logo_count']}")

# Analyze logs
analyzer = AILogAnalyzer()
diagnosis = analyzer.diagnose_failure('logs/temp_logo_automation_latest.log')
print(f"Root cause: {diagnosis['root_cause']}")
print(f"Suggested fix: {diagnosis['fix']}")
```

## 📊 Training Data

The system uses existing data:
- `template_metadata.json` (39 labeled templates)
- Detection logs from `logs/` directory
- Git commit history for fix patterns

## 🔧 Architecture

```
┌─────────────────────────────────────┐
│   Existing Logo Automation System   │
└─────────────────────────────────────┘
              ▲        │
              │        ▼
┌─────────────────────────────────────┐
│      AI Integration Layer           │
│  ┌─────────────────────────────┐   │
│  │  Pattern Classifier          │   │
│  │  Log Analyzer               │   │
│  │  Test Generator             │   │
│  │  Visual Validator           │   │
│  │  Guardrail Suggester        │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
              ▲        │
              │        ▼
┌─────────────────────────────────────┐
│    AI Models & APIs                 │
│  - OpenAI GPT-4                     │
│  - Scikit-learn (local)             │
│  - Hugging Face Transformers        │
└─────────────────────────────────────┘
```

## 📈 Roadmap

- [x] Project structure setup
- [ ] Template pattern classifier (Week 1-2)
- [ ] AI log analyzer (Week 1-2)
- [ ] Automated test generator (Week 3-4)
- [ ] Visual validation with CV (Week 5-8)
- [ ] LLM-powered guardrail suggester (Week 9-12)

## 🤝 Integration Points

### Pre-Processing Hook
```python
# Before template processing
ai_prediction = classifier.predict_template_structure(template)
if ai_prediction['confidence'] < 0.7:
    logger.warning(f"Unusual template structure detected: {ai_prediction['anomalies']}")
```

### Post-Processing Validation
```python
# After template processing
validation = visual_validator.validate_results(template_id, screenshot)
if not validation['passed']:
    logger.error(f"Visual validation failed: {validation['issues']}")
```

### Continuous Learning
```python
# After each run, update training data
trainer.add_example(template_id, detection_result, actual_outcome)
trainer.retrain_if_needed()
```

## 📚 Documentation

- [Pattern Classifier Guide](docs/pattern_classifier.md)
- [Log Analyzer Guide](docs/log_analyzer.md)
- [Test Generator Guide](docs/test_generator.md)
- [Visual Validator Guide](docs/visual_validator.md)
- [API Reference](docs/api_reference.md)

## 🔐 Security

- API keys stored in `.env` (gitignored)
- No sensitive data in training sets
- Model outputs validated before execution
- Code generation sandboxed

## 📞 Support

For issues or questions, see the main project README.
