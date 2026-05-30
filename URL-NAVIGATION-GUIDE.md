# 🔗 URL Navigation Guide

## App URLs

### **Home Page:**
```
http://localhost:5173/
```

### **Screenshots App:**
```
http://localhost:5173/#screenshots/main        ← CORE COLUMN IS HERE
http://localhost:5173/#screenshots/sessions
http://localhost:5173/#screenshots/urls
```

### **Business Apps:**
```
http://localhost:5173/#business-apps/crm
http://localhost:5173/#business-apps/parts
http://localhost:5173/#business-apps/service
http://localhost:5173/#business-apps/accounting
```

---

## Core Column Location

**✅ To see the Core Column:**
```
http://localhost:5173/#screenshots/main
```

**This is the Screenshots app Main tab where the Core Column appears.**

---

## URL Structure

### **Pattern:**
```
http://localhost:5173/#[app-name]/[tab-name]
```

### **Examples:**
- `/#screenshots/main` - Screenshots app, Main tab (has Core Column)
- `/#screenshots/sessions` - Screenshots app, Sessions tab
- `/#business-apps/parts` - Business Apps, Parts tab

---

## Quick Access

| Feature | URL |
|---------|-----|
| **Core Column** | `http://localhost:5173/#screenshots/main` |
| Parts Tiles (Business Apps) | `http://localhost:5173/#business-apps/parts` |
| Home | `http://localhost:5173/` |

---

## Common Mistakes

❌ `http://localhost:5173/tiles#screenshots/main`  
✅ `http://localhost:5173/#screenshots/main`

The `/tiles` path doesn't exist. Use `/#screenshots/main` instead.

---

**Last Updated:** 2026-05-26
