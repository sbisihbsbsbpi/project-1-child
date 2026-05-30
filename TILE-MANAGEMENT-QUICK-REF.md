# 🚀 Tile Management - Quick Reference

## Visual Guide

### **Tile Controls**
```
┌──────────────────────────────────────┐
│ ⋮⋮ = Drag Handle (move up/down)     │
│ 🗑️ = Delete Button (hover to see)   │
│ ⚙️ = Manage Tiles (in stats bar)     │
└──────────────────────────────────────┘
```

---

## Actions

| Action | Steps | Shortcut |
|--------|-------|----------|
| **Reorder** | Click & drag tile up/down | Drag ⋮⋮ |
| **Delete** | Hover → Click 🗑️ → Confirm | - |
| **Restore** | ⚙️ → Find tile → Click "Restore" | - |
| **Manage** | Click ⚙️ in stats bar | - |
| **Reset All** | ⚙️ → "Reset to Defaults" | - |
| **Export** | ⚙️ → "Export to Code" | - |

---

## localStorage Data

```json
{
  "parts-tab-active-tiles": [
    /* Array of active tile objects */
  ],
  "parts-tab-deleted-tiles": [
    "tile-id-1",
    "tile-id-2"
  ]
}
```

---

## Export to Code

**Steps:**
1. ⚙️ → "Export to Code"
2. Code auto-copied to clipboard
3. Open: `frontend/src/components/BusinessApps/PartsTab.tsx`
4. Replace lines 30-247
5. Save → Auto-reload

**Generated Code Format:**
```typescript
const PARTS_TILES: PartsTile[] = [
  { id: '...', name: '...', ... },
  // ... your custom order
];
```

---

## Visual States

| State | Look |
|-------|------|
| **Normal** | Dark background, no left border |
| **Hover** | Lighter, blue left border, 🗑️ visible |
| **Active** | Blue background, bright border |
| **Dragging** | 50% opacity, smaller |
| **Drop Target** | Green border, moved up |

---

## Default Tiles (8)

1. 📄 PDF Configuration
2. 🏭 OEM & Makes  
3. ⚙️ General Settings
4. 🏢 Manufacturer
5. 🔔 Appointment Reminder
6. 📧 Appointment Notifications
7. 🚫 Parts Void Reason
8. ⚡ Sync Priority Codes

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Tiles missing | Click ⚙️ → "Reset to Defaults" |
| Can't drag | Check if cursor shows "grab" hand |
| Delete doesn't work | Hover to reveal 🗑️ button |
| Changes lost on reload | Check browser localStorage is enabled |
| Export clipboard empty | Try again, check browser permissions |

---

## Keyboard/Mouse

- **Grab:** Click and hold on tile
- **Drag:** Move mouse while holding
- **Drop:** Release mouse button
- **Cancel Drag:** Press ESC (or drag outside)

---

## Quick Tips

💡 **Tip 1:** Drag frequently-used tiles to top  
💡 **Tip 2:** Delete unused tiles to declutter UI  
💡 **Tip 3:** Export after customizing for team  
💡 **Tip 4:** Reset anytime if something breaks  
💡 **Tip 5:** All changes auto-save to localStorage

---

## Safety

✅ Confirmation before delete  
✅ Confirmation before reset  
✅ Can restore deleted tiles  
✅ Can reset to defaults  
✅ All actions reversible  
✅ Auto-save prevents data loss

---

**Last Updated:** 2026-05-26
