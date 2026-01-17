# Data Documentation

This document details the data sources, schemas, and coverage for the **Codeforces** and **LeetCode** datasets in this repository.

## Overview

| Platform | Type | Count | Content Depth | Location |
|----------|------|-------|---------------|----------|
| **LeetCode** | Problems | 2,913+ | **Full** (Text, Snippets, Hints) | `input_pipeline/fetch_data/leetcode/data/` |
| **Codeforces** | Contests | 1,940 | **Metadata Only** (No Text) | `input_pipeline/fetch_data/codeforces/data/` |

---

## 1. LeetCode Data

### Source
- **Static Baseline**: `merged_problems.json` (2,913 problems)
- **Dynamic Updates**: Fetched via `leetcode_fetch_api.py` (Hybrid API approach)

### Schema (Rich Content)
Each problem object contains complete display and execution data.

| Field | Type | Description | Critical |
|-------|------|-------------|----------|
| `problem_id` | str | Internal unique ID (e.g., "1") | ✅ |
| `title` | str | Display title (e.g., "Two Sum") | ✅ |
| `titleSlug` | str | URL slug (e.g., "two-sum") | ✅ |
| `difficulty` | str | "Easy", "Medium", "Hard" | ✅ |
| `description` | str (HTML/MD) | **Full problem text** including images | ✅ |
| `topicTags` | list | List of tags (e.g., "Array", "Hash Table") | |
| `code_snippets` | list | Starter code for 18+ languages | ✅ |
| `examples` | list | Structured input/output examples | |
| `hints` | list | Hints for solving | |
| `constraints` | list | Problem constraints | |

### Sample JSON
```json
{
  "title": "Two Sum",
  "problem_id": "1",
  "difficulty": "Easy",
  "description": "<p>Given an array of integers...</p>",
  "topicTags": ["Array", "Hash Table"],
  "code_snippets": [ ... ]
}
```

---

## 2. Codeforces Data

### Source
- **API Fetch**: `input_pipeline/fetch_data/codeforces/codeforces_sync.py`
- **Storage**: One JSON file per contest (e.g., `1.json`, `100.json`)

### Schema (Metadata Driven)
Data is organized by **Contest**, containing a list of problems.
> ⚠️ **Note:** Does NOT contain problem descriptions/text. Only metadata.

#### Contest Object
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Contest ID (e.g., 1) |
| `name` | str | Contest Name |
| `type` | str | "ICPC", "CF", etc. |
| `phase` | str | "FINISHED" |
| `startTimeSeconds` | int | Unix timestamp |

#### Problem Object
| Field | Type | Description | Critical |
|-------|------|-------------|----------|
| `contestId` | int | Link to parent contest | ✅ |
| `index` | str | Problem letter (A, B, C...) | ✅ |
| `name` | str | Problem Title | ✅ |
| `rating` | int | Difficulty rating (e.g., 800-3500) | ✅ |
| `tags` | list | Topics (e.g., "dp", "graphs") | |

### Sample JSON (`1.json`)
```json
{
  "contest": {
    "id": 1,
    "name": "Codeforces Beta Round 1",
    "startTimeSeconds": 1266580800
  },
  "problems": [
    {
      "contestId": 1,
      "index": "A",
      "name": "Theatre Square",
      "rating": 1000,
      "tags": ["math"]
    }
  ]
}
```

---

## Critical Differences

| Feature | LeetCode | Codeforces |
|---------|----------|------------|
| **Problem Text** | ✅ **Available** | ❌ **Missing** |
| **Organization** | Flat list of problems | Grouped by Contest |
| **Difficulty** | Categorical (Easy/Med/Hard) | Numerical Rating (800-3500) |
| **Tags** | Structured Objects | Simple Strings |
| **Code Snippets** | ✅ Available | ❌ N/A |

### Common Fields
- **Title/Name**: Available in both.
- **Tags**: Available in both (requires mapping for normalization).
- **ID**: Both have unique identifiers (`frontend_id` vs `contestId`+`index`).
