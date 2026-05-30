# Logo Replacement Automation

Automated script for detecting and replacing logos in Tekion email templates using Playwright browser automation.

## Features

- ✅ **Robust Logo Detection** - Automatically detects old and new logos by media ID
- ✅ **Complete Replacement Workflow** - Hover, click, select, insert
- ✅ **Center Alignment** - Automatically centers the new logo
- ✅ **Logo Enlargement** - Scales logo to desired size
- ✅ **Two-Step Publishing** - Handles both publish clicks (main + modal confirmation)
- ✅ **Comprehensive Logging** - Detailed logs with timestamps to file and console
- ✅ **Error Handling** - Graceful error handling with informative messages
- ✅ **State Verification** - Verifies each step before proceeding

## Requirements

```bash
pip install playwright
playwright install chromium
```

## Setup

1. **Start Browser with Remote Debugging**

```bash
# For Brave Browser
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
  --remote-debugging-port=9223 &

# For Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 &
```

2. **Open the Template in Browser**
   - Navigate to the Tekion template you want to edit
   - Make sure the template edit page is open

## Usage

### Basic Usage

```python
import asyncio
from logo_replacement_automation import LogoReplacementAutomation, LogoReplacementConfig

async def replace_logo():
    config = LogoReplacementConfig(
        old_logo_media_id="6a0c6722864813539e4da7ae",  # Old logo ID
        new_logo_media_id="6a19132b6697f36de6236fb1",  # New logo ID
        new_logo_name="Tilton.png",
        chrome_debug_port=9223
    )
    
    automation = LogoReplacementAutomation(config)
    
    success = await automation.execute_full_workflow(
        center_align=True,   # Center align the logo
        enlarge=True,        # Enlarge the logo
        target_width=160,    # Target width in pixels
        publish=True         # Publish changes
    )
    
    return success

asyncio.run(replace_logo())
```

### Run the Script

```bash
python3 logo_replacement_automation.py
```

## Configuration Options

### LogoReplacementConfig

- **old_logo_media_id** (str) - Media ID of the logo to replace
- **new_logo_media_id** (str) - Media ID of the new logo
- **new_logo_name** (str) - Display name for the new logo
- **chrome_debug_port** (int) - CDP port (default: 9223)
- **template_url_pattern** (str) - URL pattern to match template page (default: "templates/edit")

### execute_full_workflow Options

- **center_align** (bool) - Center align the logo (default: True)
- **enlarge** (bool) - Enlarge the logo (default: True)
- **target_width** (int) - Target width in pixels (default: 160)
- **publish** (bool) - Publish changes (default: True)

## Workflow Steps

The automation executes the following steps:

1. **Connect** - Connect to browser via Chrome DevTools Protocol
2. **Detect State** - Analyze current logo state in template
3. **Replace Logo** (if old logo present):
   - Find old logo
   - Hover to reveal toolbar
   - Click "Change Image" icon
   - Select new logo from Insert Files modal
   - Click Insert button
   - Verify replacement
4. **Center Align** - Center the logo in its container
5. **Enlarge** - Resize logo to target width
6. **Publish** - Click Publish twice (main button + modal confirmation)

## Logging

Logs are written to both:
- **Console** - Real-time progress
- **File** - `logo_replacement_YYYYMMDD_HHMMSS.log`

Log levels:
- `INFO` - Normal workflow progress
- `WARNING` - Non-critical issues
- `ERROR` - Critical failures

## Example Log Output

```
2024-01-15 10:30:45 - INFO - ================================================================================
2024-01-15 10:30:45 - INFO - Configuration initialized:
2024-01-15 10:30:45 - INFO -   Old logo media ID: 6a0c6722864813539e4da7ae
2024-01-15 10:30:45 - INFO -   New logo media ID: 6a19132b6697f36de6236fb1
2024-01-15 10:30:45 - INFO -   New logo name: Tilton.png
2024-01-15 10:30:45 - INFO - ================================================================================
2024-01-15 10:30:46 - INFO - Connecting to browser...
2024-01-15 10:30:46 - INFO - ✅ Connected to browser
2024-01-15 10:30:46 - INFO - ✅ Selected template tab: Tekion Template Builder
2024-01-15 10:30:47 - INFO - Step 1: Finding old logo...
2024-01-15 10:30:47 - INFO - ✅ Old logo found and marked
...
2024-01-15 10:31:15 - INFO - ✅ WORKFLOW COMPLETED SUCCESSFULLY!
```

## Troubleshooting

### "Template tab not found"
- Make sure the template edit page is open in the browser
- Verify the URL contains "templates/edit"

### "Old logo not found"
- Check that the old_logo_media_id is correct
- Verify the logo exists in the template

### "New logo not found in modal"
- Ensure the new logo is uploaded to the media library
- Verify the new_logo_media_id is correct

### "Connection failed"
- Check that browser is running with `--remote-debugging-port=9223`
- Verify port 9223 is not blocked by firewall

## Advanced Usage

### Custom Workflow (Step-by-Step)

```python
automation = LogoReplacementAutomation(config)

# Connect manually
await automation.connect()

# Detect current state
state = await automation.detect_current_state()

# Replace logo only
await automation.replace_logo()

# Center align separately
await automation.center_align_logo()

# Enlarge separately
await automation.enlarge_logo(target_width=200)

# Publish separately
await automation.publish_changes()
```

## License

MIT License
