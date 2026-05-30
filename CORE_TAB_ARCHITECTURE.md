# ⚡ Core Tab - Architecture & Design

**Date:** 2026-05-27  
**Status:** ✅ Tile-Based Layout Implemented

---

## 🎨 **Design Pattern: Tile-Based Feature Selector**

The Core Tab uses a **tile-based layout** similar to the Parts Tab, making it easy to add new features in the future.

---

## 📐 **Layout Structure**

```
┌─────────────────────────────────────────────────────────┐
│                    ⚡ Core Operations                    │
│              Select a feature to get started             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │      🔑      │  │      🔧      │  │      ⚙️      │  │
│  │              │  │              │  │              │  │
│  │ OEM ID Update│  │ Feature Name │  │ Feature Name │  │
│  │              │  │              │  │              │  │
│  │ Bulk update  │  │              │  │              │  │
│  │ OEM IDs...   │  │ Coming soon  │  │ Coming soon  │  │
│  │              │  │              │  │              │  │
│  │ Ready to Use │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### **When a Tile is Clicked:**

```
┌─────────────────────────────────────────────────────────┐
│  ← Back to Core Features                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                  🔑 OEM ID Update                        │
│             OEM ID Update for User Setup                │
│                                                          │
│  [Feature-specific UI renders here]                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🧩 **Component Structure**

### **Main Component:**
```typescript
CoreTab.tsx
├── State: activeFeature ('none' | 'oem-id-update' | ...)
├── Tile View (default)
│   ├── Header (icon, title, description)
│   └── Feature Grid
│       ├── Active Tiles (clickable)
│       └── Placeholder Tiles (coming soon)
└── Feature View (when tile clicked)
    ├── Back Button
    └── Feature Component (e.g., OemIdUpdate)
```

### **Current Features:**
```typescript
type CoreFeature = 
  | 'none'                // Default: Show tiles
  | 'oem-id-update'       // OEM ID Update feature
  // Add more features here in the future
```

---

## ➕ **How to Add New Features**

### **Step 1: Add Feature Type**
```typescript
// In CoreTab.tsx
type CoreFeature = 
  | 'none'
  | 'oem-id-update'
  | 'new-feature-id';  // ← Add your feature ID
```

### **Step 2: Create Feature Component**
```typescript
// Create: frontend/src/components/BusinessApps/CoreTab/NewFeature.tsx

export const NewFeature: React.FC<{
  addLog: (message: string) => void;
  clearLogs: () => void;
}> = ({ addLog, clearLogs }) => {
  return <div>Your feature UI here</div>;
};
```

### **Step 3: Add Tile to Grid**
```typescript
// In CoreTab.tsx, add to the feature tiles grid:

<div
  onClick={() => setActiveFeature('new-feature-id')}
  style={{
    padding: '32px',
    backgroundColor: 'white',
    border: '2px solid #FF9800',
    borderRadius: '12px',
    cursor: 'pointer',
    // ... hover effects
  }}
>
  <div style={{ fontSize: '48px' }}>🎯</div>
  <h3>New Feature Name</h3>
  <p>Feature description here...</p>
  <div style={{ backgroundColor: '#FFF3E0' }}>
    <strong>Ready to Use</strong>
  </div>
</div>
```

### **Step 4: Add Render Logic**
```typescript
// In CoreTab.tsx, add to the conditional rendering:

if (activeFeature === 'new-feature-id') {
  return (
    <div>
      <BackButton onClick={handleBackToTiles} />
      <NewFeature addLog={addLog} clearLogs={clearLogs} />
    </div>
  );
}
```

**That's it!** 🎉 Your new feature is integrated!

---

## 🎨 **Tile Design Guidelines**

### **Active Tile (Clickable):**
- **Border:** `2px solid #FF9800` (orange)
- **Background:** White
- **Hover Effect:** 
  - Transform: `translateY(-4px)`
  - Shadow: `0 4px 16px rgba(255, 152, 0, 0.3)`
- **Status Badge:** Green background (`#FFF3E0`) with "Ready to Use"

### **Placeholder Tile (Coming Soon):**
- **Border:** `2px dashed #ddd` (gray dashed)
- **Background:** `#f9f9f9` (light gray)
- **Opacity:** `0.6`
- **Cursor:** `not-allowed`
- **Text Color:** `#999` (gray)

### **Grid Layout:**
```css
display: grid;
grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
gap: 24px;
```
- Responsive: Automatically adjusts to screen width
- Min tile width: 300px
- Equal column widths

---

## 📋 **Current Features**

### **1. OEM ID Update** 🔑
- **Status:** ✅ Ready to Use
- **Location:** `CoreTab/OemIdUpdate.tsx`
- **Description:** Bulk update OEM IDs for user setup
- **Features:**
  - cURL/header parser
  - CSV upload with drag-and-drop
  - Auto-column detection
  - Real-time batch processing
  - Dealer ID verification

---

## 🔮 **Future Features (Examples)**

Add more tiles as needed:

```typescript
// Example future features:

type CoreFeature = 
  | 'none'
  | 'oem-id-update'
  | 'user-bulk-import'      // Import users from CSV
  | 'role-management'       // Bulk assign roles
  | 'data-export'           // Export user data
  | 'audit-logs'            // View system audit logs
  | 'settings-sync'         // Sync settings across stores
```

---

## 📁 **File Structure**

```
frontend/src/components/BusinessApps/
├── CoreTab.tsx                    # Main tab with tile grid
├── CoreTab/
│   ├── OemIdUpdate.tsx           # Feature 1: OEM ID Update
│   ├── CurlParser.ts             # Utility for OemIdUpdate
│   ├── CsvParser.ts              # Utility for OemIdUpdate
│   ├── types.ts                  # Shared types
│   └── [NewFeature.tsx]          # Future features go here
└── index.tsx                      # Business Apps router
```

---

## 🎯 **Benefits of This Design**

✅ **Scalable:** Easy to add new features  
✅ **Discoverable:** Users see all available features at a glance  
✅ **Organized:** Each feature is self-contained  
✅ **Consistent:** All features follow the same navigation pattern  
✅ **Future-Proof:** Simple to extend without refactoring

---

## 🚀 **User Experience Flow**

1. User clicks **"Core"** tab
2. Sees **tile grid** with all features
3. Clicks **"OEM ID Update"** tile
4. Feature UI loads with **back button**
5. User completes task
6. Clicks **"← Back to Core Features"**
7. Returns to tile grid

**Clean, simple, intuitive!** ✨

---

## ✅ **Implementation Complete**

The Core Tab is now set up with a scalable tile-based architecture, ready for future growth! 🎉
