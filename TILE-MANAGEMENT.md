# 🎯 Tile Management System

## Overview

The Parts Tab now features a complete tile management system that allows you to customize, reorder, and manage tiles directly from the UI.

---

## ✨ Features

### 1. **Drag & Drop Reordering** 🔄
- **How:** Grab any tile by clicking and holding, then drag to reorder
- **Visual Feedback:** 
  - Dragged tile becomes semi-transparent
  - Drop target shows green highlight
  - Cursor changes to "grabbing" hand
- **Persistence:** Order is saved to localStorage automatically

### 2. **Delete Tiles** 🗑️
- **How:** Hover over any tile and click the 🗑️ button
- **Confirmation:** Shows confirmation dialog before deletion
- **Safety:** Deleted tiles can be restored later
- **Auto-select:** If you delete the currently selected tile, another tile is automatically selected

### 3. **Restore Deleted Tiles** ↩️
- **How:** Click the ⚙️ button in stats bar → See deleted tiles → Click "Restore"
- **Tracking:** All deleted tiles are tracked in localStorage
- **Full Restore:** Restores tile with all original configuration

### 4. **Reset to Defaults** 🔄
- **How:** Manage Tiles modal → "Reset to Defaults" button
- **Effect:** Restores all 8 original tiles in default order
- **Confirmation:** Asks for confirmation before resetting

### 5. **Export to Code** 📤
- **How:** Manage Tiles modal → "Export to Code" button
- **Output:** Generates TypeScript code for current configuration
- **Clipboard:** Automatically copies to clipboard
- **Instructions:** Shows where to paste the code

---

## 🎨 UI Elements

### **Stats Bar** (Top Left Panel)
```
Success: 3  |  Pending: 5  |  Failed: 0  |  ⚙️
                                          ↑
                                    Manage Tiles
```

### **Tile Item** (With Controls)
```
┌────────────────────────────────────────┐
│ ⋮⋮  📄  PDF Configuration         🗑️  │
│     Parts Module                        │
│     POST • ✅                           │
└────────────────────────────────────────┘
 ↑                                    ↑
Drag Handle                      Delete Button
```

### **Manage Tiles Modal**
- **Stats Section:** Shows active/deleted counts
- **Deleted Tiles List:** Shows all deleted tiles with restore buttons
- **Tips Section:** Helpful usage information
- **Actions:**
  - 🔄 Reset to Defaults
  - 📤 Export to Code
  - Close

---

## 💾 Data Storage

### **localStorage Keys:**
```typescript
'parts-tab-active-tiles'    // Array of active tile configurations
'parts-tab-deleted-tiles'   // Array of deleted tile IDs
'parts-tab-tile-bodies'     // Tile request bodies (existing)
```

### **Data Structure:**
```json
{
  "parts-tab-active-tiles": [
    {
      "id": "pdf-config",
      "name": "PDF Configuration",
      "icon": "📄",
      "method": "POST",
      "url": "https://...",
      "body": { ... }
    }
  ],
  "parts-tab-deleted-tiles": ["appt-notifications", "general-settings"]
}
```

---

## 🔧 Making Changes Permanent

### **Option 1: Export to Code (Recommended)**

1. **Customize your tiles:**
   - Reorder via drag & drop
   - Delete unwanted tiles
   - Test your configuration

2. **Export:**
   - Click ⚙️ → "Export to Code"
   - Code is copied to clipboard

3. **Apply to source:**
   - Open: `frontend/src/components/BusinessApps/PartsTab.tsx`
   - Find: Lines 30-247 (`const PARTS_TILES: PartsTile[] = [...]`)
   - Replace with clipboard content
   - Save file

4. **Result:**
   - Frontend auto-reloads with new defaults
   - All users get your configuration
   - Your customization becomes the new default

### **Option 2: Manual localStorage Management**

- **Export localStorage:** Browser DevTools → Application → localStorage
- **Share config:** Share the JSON with team members
- **Import:** They paste into their localStorage

---

## 🎯 Use Cases

### **Scenario 1: Remove Broken Tile**
```
1. Hover over broken tile
2. Click 🗑️ delete button
3. Confirm deletion
4. Tile is hidden but can be restored
```

### **Scenario 2: Prioritize Frequently Used Tiles**
```
1. Drag frequently-used tiles to the top
2. Less-used tiles move to bottom
3. Order persists across sessions
```

### **Scenario 3: Team Configuration**
```
1. Configure tiles for your team
2. Click ⚙️ → "Export to Code"
3. Update PartsTab.tsx
4. Commit to git
5. Team gets optimized configuration
```

### **Scenario 4: Accidentally Deleted Tile**
```
1. Click ⚙️ in stats bar
2. See deleted tile in list
3. Click "Restore" button
4. Tile reappears in list
```

---

## 📊 Default Tiles (8 Total)

1. **PDF Configuration** - Configure PDF templates
2. **OEM & Makes** - Manufacturer configuration
3. **General Settings** - Tax and shift settings
4. **Manufacturer** - Parts manufacturer settings
5. **Appointment Reminder** - Reminder notifications
6. **Appointment Notifications** - Email templates
7. **Parts Void Reason** - Void reason config
8. **Sync Priority Codes** - Auto-sync priority codes

---

## 🔒 Safety Features

1. **Confirmation Dialogs:**
   - Delete tile: "Are you sure?"
   - Reset to defaults: "This will restore all tiles"

2. **Reversible Actions:**
   - Deleted tiles tracked in localStorage
   - Can be restored anytime
   - Reset to defaults always available

3. **Auto-save:**
   - Every action saves to localStorage
   - No manual save needed
   - Survives page reloads

4. **Graceful Fallbacks:**
   - If localStorage fails, uses defaults
   - Missing tiles default to original config
   - No crashes from bad data

---

## 🎨 Visual States

| State | Visual Effect |
|-------|---------------|
| Normal | Dark background, transparent left border |
| Hover | Lighter background, blue left border, delete button visible |
| Active | Blue background, bright blue left border |
| Dragging | Semi-transparent, slightly smaller |
| Drop Target | Green left border, translated up |

---

**Last Updated:** 2026-05-26  
**Feature Status:** ✅ Fully Implemented
