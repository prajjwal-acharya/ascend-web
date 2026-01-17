# Data Ingestion Pipeline

> **Raw Data → Normalized Canonical Format → Schema Validation → Versioned Snapshot → Upload or Reject**

This pipeline provides a robust, reproducible, and auditable data flow for the Ascend platform.

## Quick Start

```bash
# Install dependencies
cd input_pipeline
pip install -r requirements.txt

# Run full pipeline
python3 validate_schema/run_pipeline.py

# Or run individual steps
python3 modify_data/run_normalization.py --source all
python3 normalize_schema/run_validation.py
python3 validate_schema/snapshot_manager.py create --version v1.0.0
```

## Directory Structure

```
input_pipeline/
├── fetch_data/              # Raw data sources
│   ├── leetcode/            # LeetCode problems
│   └── codeforces/          # Codeforces contests
│
├── modify_data/             # Normalization layer
│   ├── utils/               # Utility modules
│   ├── transformers/        # Platform transformers
│   ├── output/              # Canonical output
│   └── run_normalization.py
│
├── normalize_schema/        # Validation layer
│   ├── schemas/v1.0.0/      # Versioned JSON schemas
│   ├── rules/               # Validation rules
│   ├── validator.py         # Main validator
│   └── run_validation.py
│
├── validate_schema/         # Snapshot & manifest layer
│   ├── validated/           # Immutable snapshots
│   ├── rejected/            # Failed validation logs
│   ├── upload_logs/         # Upload logs
│   ├── manifest_generator.py
│   ├── snapshot_manager.py
│   └── run_pipeline.py
│
└── inject_schema/           # Upload gate
    └── upload_orchestrator.py
```

## Pipeline Steps

### 1. Normalization (`modify_data/`)

Transforms raw platform data into canonical format:
- Strips HTML from descriptions
- Generates deterministic UUIDs
- Normalizes topics to kebab-case
- Validates required fields

```bash
python3 modify_data/run_normalization.py --source all --dry-run
```

### 2. Validation (`normalize_schema/`)

Validates canonical data against versioned schemas:
- JSON Schema validation
- Duplicate detection
- Orphan topic/problem detection
- Reference validation (UUIDs, URLs)

```bash
python3 normalize_schema/run_validation.py --input ../modify_data/output/
```

### 3. Snapshot Creation (`validate_schema/`)

Creates immutable versioned snapshots:
- Copies validated data to versioned directory
- Generates manifest with checksums
- Prevents modification of existing versions

```bash
python3 validate_schema/snapshot_manager.py create --version v1.0.0
python3 validate_schema/snapshot_manager.py verify v1.0.0
python3 validate_schema/snapshot_manager.py list
```

### 4. Upload Gate (`inject_schema/`)

Final gate before database injection:
- Verifies snapshot integrity
- Ordered upload: R2 → Supabase → Redis
- Rollback on failure

```bash
python3 inject_schema/upload_orchestrator.py --check-only
python3 inject_schema/upload_orchestrator.py --dry-run
```

## Canonical Formats

### Problem
```json
{
  "problem_id": "uuid",
  "source": "leetcode",
  "external_id": "1",
  "slug": "two-sum",
  "title": "Two Sum",
  "difficulty": "easy",
  "rating": null,
  "metadata": { "source_url": "..." },
  "topics": ["array", "hash-table"],
  "content_refs": { "description_path": "r2://..." }
}
```

### Contest
```json
{
  "contest_id": "uuid",
  "source": "codeforces",
  "external_id": "1",
  "name": "Codeforces Beta Round 1",
  "type": "ICPC",
  "problems": [{ "problem_external_id": "1-A", "index": "A" }]
}
```

### Topic
```json
{
  "topic_id": "uuid",
  "name": "hash-table",
  "parent": "array",
  "category": "dsa"
}
```

## Schema Versioning

Schemas are versioned and immutable:
- `schemas/v1.0.0/` - Current production schema
- Never edit existing schemas
- Only add new versions

## Validation Rules

1. **Schema validation** - JSON Schema draft-07
2. **Duplicate detection** - external_id + source uniqueness
3. **Orphan detection** - Topics used but not defined
4. **Reference validation** - UUID format, R2 paths, URLs
5. **Slug validation** - lowercase, alphanumeric, hyphens only

## Rejection Strategy

Failed validations are logged to `rejected/`:
```
rejected/
└── v1.0.0_20260117_120000/
    ├── errors.json
    └── errors.log
```

No partial uploads are ever allowed.
