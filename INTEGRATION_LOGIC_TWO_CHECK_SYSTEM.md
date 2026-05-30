# 🔧 Integration Logic: Two-Check System for Logo Processing

## 📋 Overview

This document explains the **complete integration logic** for processing templates with and without logo containers, including the special handling for CPRA templates.

---

## 🎯 Problem Statement

**Current Behavior:**
- Scripts only process templates with logo warning icons
- Templates without logo containers are skipped
- **12 templates skipped**, including CPRA templates like:
  - `CPRA_REQUEST_COMPLETION_STOP_SELLING_AND_SHARING_DATA_WITH_3RD_PARTIES`
  - `CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS`
  - `CPRA_REQUEST_ACKNOWLEDGEMENT`
  - And others...

**Issue:**
These templates might need header addition but are currently being skipped.

---

## ✅ Solution: Two-Check System

### **Check #1: Detect Logo Containers (Warning Icons)**

```python
# Find logos with warnings
logos_info = await page.evaluate("""
    () => {
        const warnings = Array.from(
            document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb')
        );

        if (warnings.length === 0) return { found: false, count: 0 };

        warnings.forEach((icon, idx) => {
            const sortableItem = icon.closest('[class*="SortableItem"]');
            if (sortableItem) {
                sortableItem.setAttribute('data-logo-to-inspect', `logo-${idx + 1}`);
            }
        });

        return { found: true, count: warnings.length };
    }
""")

if logos_info['found']:
    # Process logo replacement normally
    for logo_idx in range(1, logos_info['count'] + 1):
        await replace_logo(page, logo_idx, "6a19132b6697f36de6236fb1")
```

### **Check #2A: Template ID Naming Convention (CPRA Check)**

When no logo containers are found, check if template uses **CPRA_ naming convention**:

```python
template_id = template_info['templateId']

# Check if CPRA template (naming convention)
is_cpra_template = template_id.startswith('CPRA_')

if is_cpra_template:
    logger.info(f"   ℹ️  CPRA template detected: {template_id}")
    # CPRA templates typically have no logo containers
    # Need to check if header addition is required
```

**Template ID Patterns:**

| Type | Example | Usage |
|------|---------|-------|
| Server-Generated | `667f0befd4964026ee7b6ea4` | Most service templates |
| Human-Readable (CPRA) | `CPRA_REQUEST_COMPLETION_...` | Data privacy templates |

### **Check #2B: Header Button State Check**

```python
# Check header button state
button_state = await page.evaluate("""
    () => {
        const btn = document.querySelector('#HEADER');
        if (!btn) return { found: false };

        const opacity = parseFloat(getComputedStyle(btn).opacity);
        return {
            found: true,
            opacity: opacity,
            isGrayed: opacity < 1.0,
            isActive: opacity === 1.0
        };
    }
""")

if button_state['isGrayed']:
    # opacity < 1.0 = Button is grayed
    # Template HAS header structure (just no logos with warnings)
    logger.info("   ℹ️  Template has header structure - skipping")
    return {'status': 'skipped', 'reason': 'Header exists'}

elif button_state['isActive']:
    # opacity = 1.0 = Button is active
    # Template has NO header structure - needs header added
    logger.info("   ➕ No header structure - adding header with logo")
    await add_header_with_logo(page)
```

**Button State Meanings:**

| Opacity | State | Meaning | Action |
|---------|-------|---------|--------|
| `< 1.0` | Grayed | Header structure exists | Skip (nothing to do) |
| `= 1.0` | Active | No header structure | Add header with logo |

---

## 🔧 Complete Header Addition Workflow

### **Step-by-Step Process:**

1. **Click #HEADER button** (wait for it to be active)
2. **Click "+ Add Header" placeholder**
3. **Select template** (radio button in modal)
4. **Click Insert button**
5. **Verify header added** (button becomes grayed again)

### **Code Implementation:**

```python
async def add_header_with_logo(page: Page) -> bool:
    """
    Add new header using discovered workflow.
    Returns True if successful, False otherwise.
    """
    try:
        # Step 1: Wait for #HEADER button to be active
        button_active = await wait_for_header_button_active(page)
        if not button_active:
            return False

        # Step 2: Click #HEADER button
        await page.evaluate('document.querySelector("#HEADER").click()')
        await asyncio.sleep(2)

        # Step 3: Click "+ Add Header" button

        add_header_btn = await page.query_selector('[data-add-header-btn="true"]')
        await add_header_btn.click()
        await asyncio.sleep(2)

        # Step 4: Verify popup opened
        popup_opened = await page.evaluate("""
            () => {
                const modal = document.querySelector('.ant-modal');
                if (!modal) return false;
                const title = modal.querySelector('.ant-modal-title');
                return title && title.textContent.includes('Insert Header');
            }
        """)
        if not popup_opened:
            return False

        # Step 5: Select first template (radio button)
        await page.evaluate("""
            () => {
                const modal = document.querySelector('.ant-modal');
                const radio = modal.querySelector('input[type="radio"]');
                if (radio) radio.click();
            }
        """)
        await asyncio.sleep(1)

        # Step 6: Click Insert button
        await page.evaluate("""
            () => {
                const modal = document.querySelector('.ant-modal');
                const buttons = modal.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.trim() === 'Insert') {
                        btn.click();
                        break;
                    }
                }
            }
        """)
        await asyncio.sleep(3)

        # Step 7: Verify header added (button should be grayed)
        header_added = await page.evaluate("""
            () => {
                const btn = document.querySelector('#HEADER');
                if (!btn) return false;
                const opacity = parseFloat(getComputedStyle(btn).opacity);
                return opacity < 1;  // Should be grayed
            }
        """)

        return header_added

    except Exception as e:
        logger.error(f"Error adding header: {e}")
        return False
```

**Source:** `parallel_logo_warning_updater.py` lines 661-831

---

## 📊 Complete Integration Logic (Pseudocode)

```python
async def process_template_tab(page, template_info, idx, total):
    """
    Process logos in a single template tab.
    Implements the two-check system.
    """

    template_id = template_info['templateId']
    template_name = template_info['title']

    logger.info(f"Processing {idx}/{total}: {template_name}")
    logger.info(f"Template ID: {template_id}")

    # ============================================================
    # CHECK #1: Look for logo containers (warning icons)
    # ============================================================
    logos_info = await page.evaluate("""
        () => {
            const warnings = Array.from(
                document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb')
            );

            if (warnings.length === 0) return { found: false, count: 0 };

            warnings.forEach((icon, idx) => {
                const sortableItem = icon.closest('[class*="SortableItem"]');
                if (sortableItem) {
                    sortableItem.setAttribute('data-logo-to-inspect', `logo-${idx + 1}`);
                }
            });

            return { found: true, count: warnings.length };
        }
    """)

    if logos_info['found']:
        # Has logo containers - process normally
        logger.info(f"   ✅ Found {logos_info['count']} logo(s) with warnings")

        logos_processed = 0
        for logo_idx in range(1, logos_info['count'] + 1):
            success = await replace_logo(page, logo_idx, "6a19132b6697f36de6236fb1")
            if success:
                logos_processed += 1

        return {
            'template': template_name,
            'id': template_id,
            'status': 'success',
            'logos_found': logos_info['count'],
            'logos_processed': logos_processed
        }

    # ============================================================
    # No logo containers detected - TWO MORE CHECKS NEEDED
    # ============================================================

    # CHECK #2A: Is this a CPRA template? (naming convention)
    is_cpra_template = template_id.startswith('CPRA_')

    if is_cpra_template:
        logger.info(f"   ℹ️  CPRA template detected: {template_id}")

    # CHECK #2B: Check header button state
    button_state = await page.evaluate("""
        () => {
            const btn = document.querySelector('#HEADER');
            if (!btn) return { found: false };

            const opacity = parseFloat(getComputedStyle(btn).opacity);
            return {
                found: true,
                opacity: opacity,
                isGrayed: opacity < 1.0,
                isActive: opacity === 1.0
            };
        }
    """)

    if not button_state['found']:
        logger.error("   ❌ #HEADER button not found")
        return {
            'template': template_name,
            'id': template_id,
            'status': 'error',
            'reason': 'Header button not found'
        }

    if button_state['isGrayed']:
        # Has header structure (just no logos with warnings)
        logger.info(f"   ℹ️  Header exists (opacity={button_state['opacity']}) - skipping")
        return {
            'template': template_name,
            'id': template_id,
            'status': 'skipped',
            'reason': 'Header exists, no logos with warnings'
        }

    elif button_state['isActive']:
        # No header structure - ADD header with logo
        logger.info(f"   ➕ No header (opacity={button_state['opacity']}) - adding header...")

        added = await add_header_with_logo(page)

        if added:
            logger.info("   ✅ Header added successfully")
            return {
                'template': template_name,
                'id': template_id,
                'status': 'success',
                'action': 'header_added'
            }
        else:
            logger.error("   ❌ Failed to add header")
            return {
                'template': template_name,
                'id': template_id,
                'status': 'failed',
                'reason': 'Header addition failed'
            }
```

---

## 📈 Expected Results After Integration

### **Before Integration:**
- ✅ Processed: 25 templates (with logo containers)
- ⚠️ Failed: 2 templates
- ℹ️ Skipped: **12 templates** (no logo containers)

### **After Integration:**
- ✅ Processed: 25 templates (logo replacement)
- ➕ Header Added: ~X templates (from the 12 skipped)
- ℹ️ Skipped: ~Y templates (already have header structure)
- ⚠️ Failed: 2 templates (manual fix needed)

---

## 🎓 Key Learnings

### **Template ID Field:**
- ✅ Always use `templateId` field (not `id`)
- ✅ `templateId` used in edit URLs: `/templates/edit/{templateId}`
- ✅ Two formats:
  - Server-generated: `667f0befd4964026ee7b6ea4`
  - Human-readable: `CPRA_REQUEST_COMPLETION_...`

### **Header Button States:**
- **Grayed (opacity < 1.0):** Header exists, cannot add another
- **Active (opacity = 1.0):** No header, can add one

### **Template Architecture Types:**
1. **With Container Structure:** Templates have pre-built logo slots
2. **Without Container Structure:** Need header component added manually

---

## 📝 Files Referenced

| File | Purpose |
|------|---------|
| `parallel_logo_warning_updater.py` | Complete header addition workflow (lines 661-831) |
| `TEKION_TEMPLATE_ARCHITECTURE_LEARNINGS.md` | Template architecture documentation |
| `TEMPLATE_ID_LEARNING.md` | Template ID field explanation |
| `process_opened_templates.py` | Current logo processing script (needs update) |
| `temp_logo_adding.py` | Alternative logo processing script |

---

## ✅ Next Steps

1. **Integrate** the two-check system into `process_opened_templates.py`
2. **Add** the `add_header_with_logo()` function
3. **Test** on CPRA templates without logo containers
4. **Verify** header button state detection works correctly
5. **Run** on all 39 Service & Parts templates
6. **Generate** updated report with header addition results

---

## 🔗 Related Documentation

- [Temp Final Script for Logo Adding](TEMP_FINAL_SCRIPT_FOR_LOGO_ADDING.md)
- [Template Architecture Learnings](TEKION_TEMPLATE_ARCHITECTURE_LEARNINGS.md)
- [Template ID Learning](TEMPLATE_ID_LEARNING.md)
- [Test Results Logic Update](TEST_RESULTS_LOGIC_UPDATE.md)

---

**Created:** 2026-05-31
**Author:** Automation Team
**Status:** 📋 Documentation Complete - Ready for Implementation

