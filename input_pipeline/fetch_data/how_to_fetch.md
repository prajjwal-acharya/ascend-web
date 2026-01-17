# How to Fetch Data

This guide explains how to update the problem datasets for Codeforces and LeetCode.

## Prerequisites

Ensure you are in the project root and have the virtual environment activated (for pandas/requests if needed, though most scripts use standard library now):

```bash
# Optional: Activate venv if you have specific dependencies
source input_pipeline/fetch_data/leetcode/venv/bin/activate
```

---

## 1. Codeforces Data

**Script:** `input_pipeline/fetch_data/codeforces/codeforces_sync.py`  
**Goal:** Fetch all "FINISHED" contests and their problems.

### How to Run
```bash
python3 input_pipeline/fetch_data/codeforces/codeforces_sync.py
```

### Output
- **Location:** `input_pipeline/fetch_data/codeforces/data/`
- **Format:** One JSON file per contest (e.g., `123.json`).
- **Content:** Contest metadata + List of problems (metadata only).

---

## 2. LeetCode Data

**Script:** `input_pipeline/fetch_data/leetcode/leetcode_fetch_api.py`  
**Goal:** Sync new problems top-up to the static baseline.

### A. Check Status
See how many problems you have vs. what's live on LeetCode.
```bash
python3 input_pipeline/fetch_data/leetcode/leetcode_fetch_api.py --mode list
```

### B. Find New Problems
Identify problems that exist on LeetCode but are missing locally.
```bash
python3 input_pipeline/fetch_data/leetcode/leetcode_fetch_api.py --mode sync --show-new
```
*   **Output:** Generates `data/new_problems.json`.

### C. Fetch Missing Details
Fetch full content (text, snippets) for the missing problems found in step B.
```bash
# Fetch 20 at a time (recommended to avoid rate limits)
python3 input_pipeline/fetch_data/leetcode/leetcode_fetch_api.py --mode details --limit 20
```
*   **Location:** `input_pipeline/fetch_data/leetcode/data/api_fetched/`
*   **Format:** Individual files (e.g., `two-sum.json`).

### D. Daily Problem
Fetch today's daily challenge.
```bash
python3 input_pipeline/fetch_data/leetcode/leetcode_fetch_api.py --mode daily --save
```
*   **Location:** `input_pipeline/fetch_data/leetcode/data/api_fetched/`

---

## Summary of Data Locations

| Platform | Data Type | Directory |
|:---|:---|:---|
| **Codeforces** | Contest JSONs | `input_pipeline/fetch_data/codeforces/data/` |
| **LeetCode** | Static Baseline | `input_pipeline/fetch_data/leetcode/data/merged_problems.json` |
| **LeetCode** | New Fetched Items | `input_pipeline/fetch_data/leetcode/data/api_fetched/` |
