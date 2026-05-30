# 📊 STORE 7619 (MB Cutler Bay) - USER STRUCTURE ANALYSIS

**Date:** 2026-05-26  
**Target User:** Maria.Caso@mbcutlerbay.com  
**User ID:** e85513ec-d69a-46a4-9c2d-fb24dabb3909

---

## ✅ KEY FINDINGS

### **1. User Has EXISTING OEM Mappings**
- ✅ `oemMappings` array exists
- ✅ Contains **complexListId** at multiple levels
- ✅ This is **SCENARIO 1** - Update oemId and PRESERVE complexListId

### **2. User Works at BOTH Stores!**
Maria Caso has OEM mappings for **TWO dealers**:
- **Dealer 7619** (MB Cutler Bay) - Primary
- **Dealer 7616** (MB Coral Gables) - Secondary

This explains why she's in the Cutler Bay data!

---

## 📋 OEM MAPPINGS STRUCTURE

### **Mapping 0: Store 7619 (MB Cutler Bay)**
```json
{
  "complexListId": "ada6a4fd-3fc0-4f10-809d-aaabc1729606",
  "dealerId": "7619",
  "oemDetails": [
    {
      "complexListId": "de2a415d-e165-4ef1-830d-7bd56d89d473",
      "oem": "benz",
      "oemId": null,  // ← Currently EMPTY - needs to be set to UMB1191975
      "oemName": null,
      "makeOverrideDisabled": true,
      "makeOverrides": [
        {
          "complexListId": "39b4fc25-ce28-42de-b955-7e55bec32fbd",
          "make": "mercedesbenz",
          "oemId": null
        }
      ]
    }
  ]
}
```

### **Mapping 1: Store 7616 (MB Coral Gables)**
```json
{
  "complexListId": "cfb531ac-d069-4c8a-b7bd-71b484701716",
  "dealerId": "7616",
  "oemDetails": [
    {
      "complexListId": "de98247b-8b49-47e5-b918-278f371b82df",
      "oem": "benz",
      "oemId": null,  // ← Also null
      "makeOverrideDisabled": true,
      "makeOverrides": [...]
    }
  ]
}
```

---

## 🎯 CRITICAL INSIGHT: Multi-Store Users

**This user has mappings for BOTH stores!**
- When updating for store 7619, we need to update **Mapping 0** (dealerId 7619)
- We must **preserve Mapping 1** (dealerId 7616) as-is

---

## 🔧 UPDATE STRATEGY FOR STORE 7619

### **Challenge:**
Users may have **multiple dealer mappings** in a single array.

### **Current Script Logic:**
```python
# ❌ WRONG - Assumes only one mapping
user['oemMappings'][0]['oemDetails'][0]['oemId'] = new_oem_id
```

This would always update the **first** mapping, which might be the wrong dealer!

### **Correct Logic:**
```python
# ✅ RIGHT - Find the mapping for the current dealer
target_dealer_id = HEADERS['dealerid']  # "7619"

# Find the mapping for this dealer
mapping_found = False
for mapping in user['oemMappings']:
    if mapping.get('dealerId') == target_dealer_id:
        # Update THIS dealer's oemId
        mapping['oemDetails'][0]['oemId'] = new_oem_id
        mapping_found = True
        break

if not mapping_found:
    # This dealer's mapping doesn't exist - create it
    # (Scenario 3 logic)
    pass
```

---

## 📊 EXTRACTED TEMPLATE VALUES FOR STORE 7619

From Maria.Caso's existing structure:
- ✅ `dealerId`: `"7619"`
- ✅ `oem`: `"benz"`
- ✅ `make`: `"mercedesbenz"`
- ✅ `makeOverrideDisabled`: `true`

**These values match store 7616!** Both are Mercedes-Benz dealerships.

---

## ⚠️ CRITICAL ISSUE DISCOVERED

### **Problem: Index-based update won't work for multi-store users**

**Current approach:**
- Update `user['oemMappings'][0]` (first mapping)

**Why it fails:**
- User may have mappings for multiple dealers
- Index 0 might be for dealer 7616, not 7619
- We need to **search by dealerId**, not index

---

## ✅ RECOMMENDED FIX

### **1. Search for Correct Dealer Mapping**
```python
def find_dealer_mapping(user, dealer_id):
    """Find the oemMapping for a specific dealer"""
    for mapping in user.get('oemMappings', []):
        if mapping.get('dealerId') == dealer_id:
            return mapping
    return None
```

### **2. Update the Correct Mapping**
```python
dealer_mapping = find_dealer_mapping(user, '7619')

if dealer_mapping:
    # SCENARIO 1 or 2: Update existing
    dealer_mapping['oemDetails'][0]['oemId'] = new_oem_id
else:
    # SCENARIO 3: Create new mapping for this dealer
    user['oemMappings'].append({
        "dealerId": "7619",
        "oemDetails": [{
            "oem": "benz",
            "oemId": new_oem_id,
            ...
        }]
    })
```

---

## 📁 FILES CREATED

1. ✅ `analyze_user_structure.py` - Analysis script
2. ✅ `user_structure_e85513ec-d69a-46a4-9c2d-fb24dabb3909.json` - Full user JSON
3. ✅ `STORE_7619_ANALYSIS.md` - This document

---

## 🎯 NEXT STEPS

1. **Update batch script** to handle multi-dealer mappings
2. **Search by dealerId** instead of using index [0]
3. **Test with Maria.Caso** to verify it updates the right mapping
4. **Run full batch** for store 7619

---

## 📝 SUMMARY

- ✅ User structure retrieved successfully
- ✅ Template values extracted: `dealerId=7619, oem=benz, make=mercedesbenz`
- ⚠️ **Critical issue found:** Multi-dealer mappings require dealer-specific search
- ✅ Solution identified: Search by `dealerId` instead of array index

**Ready to update the batch script!** 🚀
