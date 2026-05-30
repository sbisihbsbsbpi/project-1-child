#!/usr/bin/env python3
"""
Documentation Generator
Generates performance documentation from metrics configuration
"""

from pathlib import Path
from performance_metrics import metrics


def generate_actual_performance_summary() -> str:
    """Generate ACTUAL_PERFORMANCE_SUMMARY.md content"""
    m = metrics.to_dict()

    return f"""# 📊 Actual Performance Summary

## ⏱️ Your Actual Performance (56 URLs)

### **Total Time: {m['total_time']:.0f} seconds ({m['total_time_minutes']:.1f} minutes)**

```
Batch 1 ({m['batch_1_urls']} URLs):  {m['batch_timeout']:.0f}s ┐
Batch 2 ({m['batch_2_urls']} URLs):  {m['batch_timeout']:.0f}s ├─ 3 batches total (grouped by domain)
Batch 3 ({m['batch_3_urls']} URLs):  {m['batch_timeout']:.0f}s ┘
──────────────────────────
TOTAL:             {m['total_time']:.0f}s ({m['total_time_minutes']:.1f} minutes)
Average per URL:   {m['avg_time_per_url']:.0f}s
```

---

## 🎯 Quick Summary

### **Per URL:**
- **Wait time:** {m['ui_load_wait_min']:.0f}-{m['ui_load_wait_max']:.0f} seconds (UI load + screenshot)
- **Average time:** {m['avg_time_per_url']:.0f} seconds (due to parallel processing)
- **Speedup:** {m['batch_1_urls']}-{m['batch_2_urls']}x faster than sequential!

### **For {m['total_urls']} URLs:**
- **Total time:** {m['total_time']:.0f} seconds ({m['total_time_minutes']:.1f} minutes)
- **Batches:** 3 (grouped by domain)
- **URLs per batch:** {m['batch_1_urls']}-{m['batch_2_urls']} (all in parallel)
- **Batch timeout:** {m['batch_timeout']:.0f} seconds (Real Browser Mode)
- **Speedup:** {m['speedup']:.1f}x faster than sequential ({m['sequential_time_minutes']:.1f} min → {m['total_time_minutes']:.1f} min)

---

## 📊 Comparison Table

| Metric               | Sequential      | Parallel (Actual) | Speedup           |
| -------------------- | --------------- | ----------------- | ----------------- |
| URLs per batch       | 1               | {m['batch_1_urls']}-{m['batch_2_urls']}             | {m['batch_1_urls']}-{m['batch_2_urls']}x            |
| Total time ({m['total_urls']} URLs) | {m['sequential_time']:.0f}s ({m['sequential_time_minutes']:.1f} min) | {m['total_time']:.0f}s ({m['total_time_minutes']:.1f} min)    | {m['speedup']:.1f}x              |
| Average per URL      | {m['ui_load_wait_max']:.0f}s             | {m['avg_time_per_url']:.0f}s                | {m['speedup']:.1f}x              |
| Wait time per URL    | {m['ui_load_wait_max']:.0f}s             | {m['ui_load_wait_max']:.0f}s               | Same              |
| Batches              | {m['total_urls']}              | 3                 | {m['total_urls'] / 3:.1f}x fewer       |
| Batch timeout        | N/A             | {m['batch_timeout']:.0f}s               | Real Browser Mode |

---

## 🎉 Summary

**Your {m['total_urls']} URLs take {m['total_time_minutes']:.1f} minutes ({m['total_time']:.0f} seconds) to capture:**

- ✅ **Batch 1:** {m['batch_1_urls']} URLs in {m['batch_timeout']:.0f} seconds
- ✅ **Batch 2:** {m['batch_2_urls']} URLs in {m['batch_timeout']:.0f} seconds
- ✅ **Batch 3:** {m['batch_3_urls']} URLs in {m['batch_timeout']:.0f} seconds

**Each URL waits {m['ui_load_wait_min']:.0f}-{m['ui_load_wait_max']:.0f} seconds for UI to load, but all URLs in a batch load at the SAME TIME!**

**Batch time is {m['batch_timeout']:.0f} seconds (Real Browser Mode timeout limit)**

**This is {m['speedup']:.1f}x faster than sequential processing!** 🚀

---

**Generated from:** `backend/performance_metrics.py`
**To update:** Change values in `performance_metrics.py` and run `python generate_docs.py`
"""


def generate_ui_load_wait_time() -> str:
    """Generate UI_LOAD_WAIT_TIME.md content (key sections)"""
    m = metrics.to_dict()

    return f"""# ⏱️ UI Load Wait Time

## 🚀 For {m['total_urls']} URLs (Parallel - ACTUAL):

```
Batch 1 ({m['batch_1_urls']} URLs):  {m['batch_timeout']:.0f}s ┐
Batch 2 ({m['batch_2_urls']} URLs):  {m['batch_timeout']:.0f}s ├─ 3 batches total (grouped by domain)
Batch 3 ({m['batch_3_urls']} URLs):  {m['batch_timeout']:.0f}s ┘
──────────────────────────
TOTAL: ~{m['total_time']:.0f}s ({m['total_time_minutes']:.1f} minutes)
```

**Average per URL:** {m['avg_time_per_url']:.0f} seconds (including all wait times!)

**Why 3 batches?**

- URLs are grouped by domain (same domain = same batch)
- Each batch processes ALL URLs in parallel at the SAME TIME
- Batch time = {m['batch_timeout']:.0f} seconds (Real Browser Mode timeout)

---

**Generated from:** `backend/performance_metrics.py`
**To update:** Change values in `performance_metrics.py` and run `python generate_docs.py`
"""


def main(verbose: bool = True):
    """Generate all documentation files"""
    docs_dir = Path(__file__).parent.parent  # project-1-child/

    # Generate ACTUAL_PERFORMANCE_SUMMARY.md
    summary_path = docs_dir / "ACTUAL_PERFORMANCE_SUMMARY.md"
    summary_content = generate_actual_performance_summary()
    summary_path.write_text(summary_content)
    if verbose:
        print(f"✅ Generated: {summary_path}")

    # Generate UI_LOAD_WAIT_TIME.md (partial - key sections only)
    ui_wait_path = docs_dir / "UI_LOAD_WAIT_TIME_GENERATED.md"
    ui_wait_content = generate_ui_load_wait_time()
    ui_wait_path.write_text(ui_wait_content)
    if verbose:
        print(f"✅ Generated: {ui_wait_path}")

    if verbose:
        print("\n📊 Current Metrics:")
        print(f"  Batch timeout: {metrics.batch_timeout}s")
        print(f"  Total time: {metrics.total_time}s ({metrics.total_time_minutes:.1f} min)")
        print(f"  Avg per URL: {metrics.avg_time_per_url:.1f}s")
        print(f"  Speedup: {metrics.speedup:.1f}x")

        print("\n💡 To change timing:")
        print("  1. Edit backend/performance_metrics.py")
        print("  2. Change 'batch_timeout' value (e.g., 90.0 → 120.0)")
        print("  3. Restart backend (docs auto-generate on startup)")
        print("  4. Or run manually: python backend/generate_docs.py")


if __name__ == "__main__":
    main()
