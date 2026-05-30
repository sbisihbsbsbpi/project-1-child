# 🔗 Core Tab - URL Routing Guide

**Date:** 2026-05-27  
**Feature:** Hash-based URL routing for Core Tab features

---

## 📍 **URL Structure**

### **Base URLs:**

| URL | Description | View |
|-----|-------------|------|
| `http://localhost:5173/main#business-apps/core` | Core Tab - Tile Grid | Shows all available features |
| `http://localhost:5173/main#business-apps/core/oem-id-update` | OEM ID Update Feature | Opens OEM ID Update directly |

---

## 🎯 **How It Works**

### **1. Direct Navigation**

You can now **share or bookmark** direct links to specific features:

```
✅ Share this link to OEM ID Update:
http://localhost:5173/main#business-apps/core/oem-id-update

✅ User clicks → Opens directly to OEM ID Update feature
```

### **2. Browser Back/Forward**

The browser back/forward buttons now work:

```
User Journey:
1. Opens Core Tab → URL: #business-apps/core
2. Clicks "OEM ID Update" → URL: #business-apps/core/oem-id-update
3. Clicks browser back ← → Returns to tile grid
4. Clicks browser forward → → Returns to OEM ID Update
```

### **3. URL Updates on Click**

When users click a feature tile, the URL automatically updates:

```javascript
// Before: http://localhost:5173/main#business-apps/core
[User clicks "OEM ID Update" tile]
// After:  http://localhost:5173/main#business-apps/core/oem-id-update
```

---

## 🔧 **Technical Implementation**

### **URL Pattern:**
```
#business-apps/core/{feature-id}
                     └─────────── Feature identifier
```

### **Feature IDs:**

| Feature | URL Segment | Full Hash |
|---------|-------------|-----------|
| Tile Grid (default) | `core` | `#business-apps/core` |
| OEM ID Update | `oem-id-update` | `#business-apps/core/oem-id-update` |
| Future Feature 1 | `feature-name` | `#business-apps/core/feature-name` |
| Future Feature 2 | `another-feature` | `#business-apps/core/another-feature` |

---

## 🎨 **User Experience**

### **Scenario 1: Fresh Load**

```
1. User visits: http://localhost:5173/main#business-apps/core/oem-id-update
2. CoreTab component:
   - Reads hash from URL
   - Parses feature ID: "oem-id-update"
   - Sets activeFeature state
   - Renders OEM ID Update directly (no tile grid shown)
```

### **Scenario 2: Navigation Within App**

```
1. User is on Core tile grid
2. Clicks "OEM ID Update" tile
3. Component:
   - Updates state: setActiveFeature('oem-id-update')
   - Updates URL: window.location.hash = '#business-apps/core/oem-id-update'
   - Renders OEM ID Update feature
```

### **Scenario 3: Back Button**

```
1. User is viewing OEM ID Update
2. Clicks browser back button
3. Component:
   - Detects hashchange event
   - Reads new hash: #business-apps/core
   - Updates state: setActiveFeature('none')
   - Shows tile grid
```

---

## 📋 **Code Details**

### **State Management:**
```typescript
const [activeFeature, setActiveFeature] = useState<CoreFeature>('none');
```

### **URL Initialization (on mount):**
```typescript
useEffect(() => {
  const hash = window.location.hash;
  const match = hash.match(/#business-apps\/core\/([^\/]+)/);
  
  if (match) {
    const featureName = match[1];
    if (featureName === 'oem-id-update') {
      setActiveFeature('oem-id-update');
    }
  }
}, []);
```

### **Hash Change Listener:**
```typescript
window.addEventListener('hashchange', handleHashChange);
```

### **URL Update on Click:**
```typescript
const handleSelectFeature = (feature: CoreFeature) => {
  setActiveFeature(feature);
  
  if (feature === 'none') {
    window.location.hash = '#business-apps/core';
  } else {
    window.location.hash = `#business-apps/core/${feature}`;
  }
};
```

---

## 🔮 **Future Features**

When you add new features, they automatically get URL routing:

```typescript
// Add to CoreTab.tsx:

type CoreFeature = 
  | 'none'
  | 'oem-id-update'
  | 'user-import'        // New feature
  | 'role-management';   // New feature

// URLs automatically work:
// #business-apps/core/user-import
// #business-apps/core/role-management
```

---

## ✅ **Benefits**

1. ✅ **Shareable Links** - Send direct links to specific features
2. ✅ **Bookmarking** - Save favorite features as bookmarks
3. ✅ **Browser Navigation** - Back/forward buttons work correctly
4. ✅ **Deep Linking** - Open specific features from external links
5. ✅ **Better UX** - URL reflects current view
6. ✅ **Debugging** - Easier to debug specific feature states

---

## 🧪 **Testing**

### **Test 1: Direct Link**
1. Open: `http://localhost:5173/main#business-apps/core/oem-id-update`
2. ✅ Expected: OEM ID Update opens directly

### **Test 2: Navigation**
1. Open: `http://localhost:5173/main#business-apps/core`
2. Click: "OEM ID Update" tile
3. ✅ Expected: URL changes to `#business-apps/core/oem-id-update`

### **Test 3: Back Button**
1. From OEM ID Update view
2. Click browser back button
3. ✅ Expected: Returns to tile grid

### **Test 4: Forward Button**
1. After clicking back
2. Click browser forward button
3. ✅ Expected: Returns to OEM ID Update

### **Test 5: Back to Tiles Button**
1. From OEM ID Update view
2. Click "← Back to Core Features" button
3. ✅ Expected: URL changes to `#business-apps/core`

---

## 📝 **Example URLs**

Copy and test these URLs:

```bash
# Tile Grid (all features)
http://localhost:5173/main#business-apps/core

# OEM ID Update Feature
http://localhost:5173/main#business-apps/core/oem-id-update

# Future: User Import (when implemented)
http://localhost:5173/main#business-apps/core/user-import
```

---

## 🎉 **Implementation Complete!**

URL routing is now active for the Core Tab. Users can:
- Share direct links to features
- Use browser navigation
- Bookmark specific features
- Deep link from external sources

**All features automatically get URL routing when added!** 🚀
