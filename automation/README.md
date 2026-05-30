# Tekion Templates Automation Library

**Status:** ✅ Active Development
**Last Updated:** 2026-05-29
**Platform:** Tekion CRM - Templates Module

## Overview

This automation library provides step-by-step automation solutions for the Tekion Templates page at `https://preprodapp.tekioncloud.com/templates/list`.

## Features

### ✅ Completed Automations

1. **Department Filter Automation** (`department_filter_automation.py`)
   - Select/unselect departments (Sales, Service, Parts)
   - Uses existing Chrome browser via CDP
   - Waits for page updates
   - Verified working on 2026-05-29

2. **Clear Filters Automation** (`clear_filters_automation.py`)
   - Click Clear button to reset all filters
   - Resets department filter to "Select..."
   - Updates all tab counts
   - Verified working on 2026-05-29

### 🚧 Planned Automations

3. Tab Selection (Email, Text, Live Chat)
4. Template Search
5. Template Creation
6. Logo Addition (existing feature integration)
7. Logo Removal (existing feature integration)
8. Bulk Operations

## Installation

### Prerequisites

```bash
# Python 3.8+
python3 --version

# Install Playwright
pip install playwright
playwright install chromium

# Or use existing backend dependencies
cd backend
pip install -r requirements.txt
```

### Setup

1. **Start Chrome with CDP:**
   ```bash
   # Mac/Linux
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9223 --user-data-dir=/tmp/chrome-debug

   # Or use Brave
   /Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --remote-debugging-port=9223
   ```

2. **Login to Tekion:**
   - Navigate to: https://preprodapp.tekioncloud.com/templates/list
   - Complete authentication
   - Keep the browser open

## Usage

### Department Filter Automation

```python
from automation.department_filter_automation import change_department_filter
import asyncio

# Example 1: Select Service & Parts, Unselect Sales
result = await change_department_filter(
    departments_to_select=['Service', 'Parts'],
    departments_to_unselect=['Sales'],
    wait_seconds=20
)

print(result['final_selection'])  # Output: "Service, Parts"
```

**Command Line:**
```bash
cd automation
python3 department_filter_automation.py
```

**Parameters:**
- `departments_to_select` (list): Departments to check
  - Options: `['Sales', 'Service', 'Parts']`
- `departments_to_unselect` (list): Departments to uncheck
- `wait_seconds` (int): Wait time after change (default: 20)
- `cdp_url` (str): Chrome DevTools Protocol URL (default: http://localhost:9223)

**Returns:**
```python
{
    'status': 'success',  # or 'failed', 'error'
    'initial_selection': 'Sales',
    'final_selection': 'Service, Parts',
    'message': 'Successfully changed departments to: Service, Parts',
    'timestamp': '2026-05-29T22:58:45.123456'
}
```


### Clear Filters Automation

```python
from automation.clear_filters_automation import click_clear_button
import asyncio

# Click Clear button to reset all filters
result = await click_clear_button(wait_seconds=5)

print(result['department_filter'])  # Output: "Select..."
print(result['clicked'])            # Output: True
```

**Command Line:**
```bash
cd automation
python3 clear_filters_automation.py
```

**Parameters:**
- `wait_seconds` (int): Wait time after clicking (default: 5)
- `cdp_url` (str): Chrome DevTools Protocol URL (default: http://localhost:9223)

**Returns:**
```python
{
    'status': 'success',  # or 'failed', 'error'
    'clicked': True,
    'department_filter': 'Select...',
    'tabs': ['Email (40)', 'Text (1)', 'Live Chat (3)'],
    'message': 'Successfully clicked Clear button and filters reset',
    'timestamp': '2026-05-29T23:10:35.123456'
}
```


## Architecture

```
automation/
├── README.md                           # This file
├── department_filter_automation.py     # Department filter module
├── __init__.py                         # Package initialization
└── utils/                              # Shared utilities (future)
    ├── cdp_connector.py               # CDP connection helper
    ├── page_finder.py                 # Page detection
    └── wait_helpers.py                # Smart waiting functions
```

## Key Learnings & Best Practices

### 1. **Use Existing CDP Connection**
✅ **DO:** Connect to existing browser
❌ **DON'T:** Create new browser instances or tabs

```python
browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
context = browser.contexts[0]
```

### 2. **Find Correct Page**
✅ **DO:** Check for exact URL pattern
❌ **DON'T:** Assume first tab is correct

```python
for page in context.pages:
    if '/templates/list' in page.url and '/edit/' not in page.url:
        templates_page = page
        break
```

### 3. **Use Reliable Selectors**
✅ **DO:** Use data-test attributes and checkboxes
❌ **DON'T:** Rely on text matching alone

```python
checkboxes = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')
```

### 4. **Wait Appropriately**
✅ **DO:** Add delays between actions
❌ **DON'T:** Execute actions too quickly

```python
await page.click('.dropdown')
await asyncio.sleep(2)  # Wait for dropdown to load
```

### 5. **Verify Results**
✅ **DO:** Check final state
❌ **DON'T:** Assume success without verification

```python
final = await page.evaluate("() => document.querySelector('.filter').innerText")
```

## Detected Page Elements

### Department Filter
- **Selector:** `.ant-dropdown-trigger`
- **Inner ID:** `#departments`
- **Data Attribute:** `data-test-id="-departments-selectedValues"`
- **Options:** Sales (index 0), Service (index 1), Parts (index 2)

### Tabs
- **Selector:** `[role="tab"]`
- **Types:** Email, Text, Live Chat
- **Attribute:** `aria-selected="true"` for active tab

### Search Boxes
- **Selector:** `input[placeholder*="Search"]`
- **Count:** 2 (global and local search)

### Action Buttons
- Drafts (0)
- Archive (0)
- Actions (dropdown)
- New Template (primary button)

## Troubleshooting

### Issue: "Backend not reachable"
**Solution:** Start the backend server
```bash
cd backend
python3 main.py
```

### Issue: "Page not found"
**Solution:** Navigate to templates page manually in browser

### Issue: "Checkboxes not clicking"
**Solution:** Increase wait time after opening dropdown

## Future Enhancements

- [ ] Add tab selection automation
- [ ] Add template search automation
- [ ] Add bulk template operations
- [ ] Create integration with existing logo tools
- [ ] Add error recovery and retry logic
- [ ] Create video recording of automation
- [ ] Add headless mode support

## Contributing

When adding new automation:
1. Create a new module in `automation/`
2. Document all selectors used
3. Add usage examples
4. Test thoroughly
5. Update this README

## License

Internal use only - Tekion Automation Project
