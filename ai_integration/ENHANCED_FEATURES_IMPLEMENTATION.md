# 🔧 Enhanced AI Features - Implementation Guide

**Purpose:** Add 5 new DOM-based features to improve AI accuracy from ~48% to ~85%+ on complex templates

---

## 📋 **Implementation Checklist**

- [ ] Step 1: Add feature extraction JavaScript
- [ ] Step 2: Update Python detection result handling
- [ ] Step 3: Update `pattern_classifier.py` feature extraction
- [ ] Step 4: Re-run detection on all 39 templates
- [ ] Step 5: Retrain AI model
- [ ] Step 6: Test on Consumer Scheduling OTP template

---

## 🔧 **Step 1: Add JavaScript Feature Extraction**

### **Location:** `temp_logo_adding_FINAL.py` → `_detect_logos_with_ai()` function

**Add this code AFTER the existing logo detection, BEFORE returning results:**

```javascript
// ============================================================================
// ENHANCED AI FEATURES - Template Complexity Analysis
// ============================================================================
debug.push('\\n=== ENHANCED AI FEATURE EXTRACTION ===');

const enhancedFeatures = {
    sortableItemCount: 0,
    totalTableCount: 0,
    nonLogoTableCount: 0,
    hasButtons: false,
    dynamicTagCount: 0
};

// Feature 1: Count sortable items (complexity indicator)
const sortableItems = document.querySelectorAll('[class*="SortableItem"]');
enhancedFeatures.sortableItemCount = sortableItems.length;
debug.push(`Sortable items: ${enhancedFeatures.sortableItemCount}`);

// Feature 2: Count all tables
const allTables = document.querySelectorAll('table');
enhancedFeatures.totalTableCount = allTables.length;
debug.push(`Total tables: ${enhancedFeatures.totalTableCount}`);

// Feature 3: Calculate non-logo tables
enhancedFeatures.nonLogoTableCount = enhancedFeatures.totalTableCount - logoTables.length;
debug.push(`Non-logo tables: ${enhancedFeatures.nonLogoTableCount}`);

// Feature 4: Check for buttons (CTA presence)
const buttons = document.querySelectorAll('button[type], a[class*="button"], [class*="Button"]');
enhancedFeatures.hasButtons = buttons.length > 0;
debug.push(`Has buttons: ${enhancedFeatures.hasButtons} (${buttons.length} found)`);

// Feature 5: Count dynamic tags (personalization level)
const dynamicTags = document.querySelectorAll('[data-tag-id], [class*="dynamic_tag"]');
enhancedFeatures.dynamicTagCount = dynamicTags.length;
debug.push(`Dynamic tags: ${enhancedFeatures.dynamicTagCount}`);

debug.push('\\nEnhanced features extraction complete');
```

**Then ADD to the return object:**

```javascript
return {
    // ... existing fields ...
    logoTablesCount: logoTables.length,
    warningsCount: warnings.length,
    
    // NEW: Enhanced AI features
    enhancedFeatures: enhancedFeatures,
    
    debug: debug
};
```

---

## 🐍 **Step 2: Update Python Detection Handling**

### **Location:** `temp_logo_adding_FINAL.py` → After `detection_result = await self._detect_logos_with_ai(page)`

**Add this code to extract and log enhanced features:**

```python
# Extract enhanced features for AI
enhanced_features = detection_result.get('enhancedFeatures', {})
if enhanced_features:
    logger.info(f"   📊 Template Complexity:")
    logger.info(f"      Sortable items: {enhanced_features.get('sortableItemCount', 0)}")
    logger.info(f"      Total tables: {enhanced_features.get('totalTableCount', 0)}")
    logger.info(f"      Non-logo tables: {enhanced_features.get('nonLogoTableCount', 0)}")
    logger.info(f"      Has buttons: {enhanced_features.get('hasButtons', False)}")
    logger.info(f"      Dynamic tags: {enhanced_features.get('dynamicTagCount', 0)}")
```

---

## 🤖 **Step 3: Update AI Classifier**

### **Location:** `ai_integration/pattern_classifier.py`

**Update the `_extract_features()` method:**

```python
def _extract_features(self, template: Dict) -> np.ndarray:
    """
    Extract numerical features from template metadata.
    
    Features (11 total):
    - Original 6 features (backward compatible)
    - Enhanced 5 features (new)
    """
    detection = template.get('detection', {})
    
    # Original 6 features
    original_features = [
        detection.get('logo_tables_found', 0),
        detection.get('header_button_opacity', 1.0),
        1 if detection.get('has_logos', False) else 0,
        detection.get('logo_count', 0),
        len(template.get('departments', [])),
        self._encode_logo_type(detection.get('logo_type'))
    ]
    
    # Enhanced 5 features
    enhanced_features = [
        detection.get('sortable_item_count', 0),
        detection.get('total_table_count', 0),
        detection.get('non_logo_table_count', 0),
        1 if detection.get('has_buttons', False) else 0,
        detection.get('dynamic_tag_count', 0)
    ]
    
    # Combine all features
    all_features = original_features + enhanced_features
    
    return np.array(all_features)
```

**Update the feature names list:**

```python
self.feature_names = [
    'logo_tables_found',
    'header_button_opacity',
    'has_logos',
    'logo_count',
    'department_count',
    'logo_type_encoded',
    # Enhanced features
    'sortable_item_count',
    'total_table_count',
    'non_logo_table_count',
    'has_buttons',
    'dynamic_tag_count'
]
```

---

## 🔄 **Step 4: Re-collect Training Data**

**Run detection on all templates to collect enhanced features:**

```bash
cd /Users/tlreddy/Documents/project-1-child
python3 logo_addition_diagnostics/temp_logo_adding_FINAL.py --all --no-publish --dry-run
```

**This will update `template_metadata.json` with new features for all 39 templates**

---

## 🎓 **Step 5: Retrain Model**

**Run the training script:**

```bash
cd /Users/tlreddy/Documents/project-1-child/ai_integration
python3 -c "
from pattern_classifier import TemplateClassifier

# This will automatically retrain with new features
classifier = TemplateClassifier()
print('✅ Model retrained with 11 features')
print(f'Feature count: {len(classifier.feature_names)}')
print(f'Training accuracy: {classifier.model_info[\"training_accuracy\"]:.2%}')
"
```

---

## ✅ **Step 6: Test on Complex Template**

**Run on Consumer Scheduling OTP:**

```bash
python3 logo_addition_diagnostics/temp_logo_adding_FINAL.py \
    --template-name "Consumer Scheduling OTP" \
    --no-publish
```

**Expected output (BEFORE enhancement):**
```
🤖 AI: Service/Parts - 4 Logo Tables (Confidence: 48%)
⚠️  AI detected anomalies: ['Low confidence (48.00%)']
```

**Expected output (AFTER enhancement):**
```
🤖 AI: Service OTP Template - Complex (Confidence: 87%)
📊 Template Complexity:
   Sortable items: 13
   Total tables: 15
   Non-logo tables: 11
   Has buttons: True
   Dynamic tags: 7
✅ High confidence prediction
```

---

## 📊 **Expected Improvements**

| Metric | Before | After |
|--------|--------|-------|
| **Features** | 6 | 11 |
| **Avg Confidence** | 65% | 85%+ |
| **Complex Template Confidence** | 48% | 87%+ |
| **Anomaly Detection Rate** | High (false positives) | Low (accurate) |
| **Training Accuracy** | 100% | 100% (maintained) |

---

## 🎯 **Success Criteria**

✅ All 39 templates have enhanced features in metadata  
✅ Model retrains successfully with 11 features  
✅ Consumer Scheduling OTP shows 85%+ confidence  
✅ No regression on simple templates  
✅ Anomaly detection only flags real edge cases
