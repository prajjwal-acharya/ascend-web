#!/usr/bin/env python3
"""
Pipeline Orchestrator

Main entry point for the complete data ingestion pipeline:
1. Normalization (Raw → Canonical)
2. Validation (Schema + Rules)
3. Snapshot Creation (Versioned + Checksums)
4. Upload Gate (Ready for DB injection)

Usage:
    python3 run_pipeline.py                    # Full pipeline
    python3 run_pipeline.py --step normalize   # Only normalization
    python3 run_pipeline.py --step validate    # Only validation
    python3 run_pipeline.py --step snapshot    # Only snapshot creation
    python3 run_pipeline.py --dry-run          # Don't save any files
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any

# Add parent directories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PIPELINE_DIR)

# Import pipeline components
from modify_data.transformers import LeetCodeTransformer, CodeforcesTransformer
from normalize_schema.validator import SchemaValidator
from validate_schema.snapshot_manager import create_snapshot, get_next_version


# Paths
FETCH_DATA_DIR = os.path.join(PIPELINE_DIR, "fetch_data")
LEETCODE_DATA = os.path.join(FETCH_DATA_DIR, "leetcode", "data", "merged_problems.json")
CODEFORCES_DATA = os.path.join(FETCH_DATA_DIR, "codeforces", "data")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "modify_data", "output")
VALIDATED_DIR = os.path.join(PIPELINE_DIR, "validate_schema", "validated")


class PipelineResult:
    """Aggregated result of pipeline execution."""
    
    def __init__(self):
        self.success = True
        self.steps_completed = []
        self.steps_failed = []
        self.normalization = None
        self.validation = None
        self.snapshot = None
        self.errors = []
        self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'steps_completed': self.steps_completed,
            'steps_failed': self.steps_failed,
            'errors': self.errors,
            'warnings': self.warnings,
            'normalization': self.normalization,
            'validation': self.validation.to_dict() if self.validation else None,
            'snapshot': self.snapshot,
        }


def ensure_dirs():
    """Create necessary directories."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(data: Any, filename: str, directory: str = OUTPUT_DIR):
    """Save data to JSON file."""
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath


def step_normalize(dry_run: bool = False) -> Dict[str, Any]:
    """
    Step 1: Normalize raw data to canonical format.
    
    Returns:
        Normalization result with stats
    """
    print("\n" + "=" * 60)
    print("STEP 1: NORMALIZATION")
    print("=" * 60)
    
    result = {
        'success': False,
        'problems': [],
        'contests': [],
        'topics': [],
        'stats': {},
        'errors': [],
    }
    
    # LeetCode normalization
    print("\n[LeetCode]")
    if os.path.exists(LEETCODE_DATA):
        lc_transformer = LeetCodeTransformer()
        lc_result = lc_transformer.transform_from_file(LEETCODE_DATA)
        
        result['problems'].extend(lc_result['problems'])
        result['stats']['leetcode'] = lc_result['stats']
        result['errors'].extend(lc_result['errors'])
        
        print(f"  ✓ Transformed {lc_result['stats']['success']} problems")
        if lc_result['stats']['failed'] > 0:
            print(f"  ⚠ Failed: {lc_result['stats']['failed']}")
    else:
        print(f"  ⚠ Skipped: Data not found at {LEETCODE_DATA}")
    
    # Codeforces normalization
    print("\n[Codeforces]")
    if os.path.exists(CODEFORCES_DATA):
        cf_transformer = CodeforcesTransformer()
        cf_result = cf_transformer.transform_all(CODEFORCES_DATA)
        
        result['problems'].extend(cf_result['problems'])
        result['contests'].extend(cf_result['contests'])
        result['stats']['codeforces'] = cf_result['stats']
        result['errors'].extend(cf_result['errors'])
        
        print(f"  ✓ Transformed {cf_result['stats']['problems']['success']} problems")
        print(f"  ✓ Transformed {cf_result['stats']['contests']['success']} contests")
        if cf_result['stats']['problems']['failed'] > 0:
            print(f"  ⚠ Failed problems: {cf_result['stats']['problems']['failed']}")
    else:
        print(f"  ⚠ Skipped: Data not found at {CODEFORCES_DATA}")
    
    # Merge and deduplicate topics
    print("\n[Topics]")
    all_topics = {}
    for problem in result['problems']:
        for topic in problem.get('topics', []):
            if topic not in all_topics:
                from modify_data.utils.topic_normalizer import build_topic_document
                all_topics[topic] = build_topic_document(topic)
    
    result['topics'] = sorted(all_topics.values(), key=lambda t: t['name'])
    print(f"  ✓ Extracted {len(result['topics'])} unique topics")
    
    # Save output
    if not dry_run:
        ensure_dirs()
        save_json(result['problems'], 'problems.json')
        save_json(result['contests'], 'contests.json')
        save_json(result['topics'], 'topics.json')
        print(f"\n  ✓ Saved to: {OUTPUT_DIR}")
    else:
        print("\n  [DRY RUN] Files not saved")
    
    result['success'] = len(result['problems']) > 0 or len(result['contests']) > 0
    result['stats']['total_problems'] = len(result['problems'])
    result['stats']['total_contests'] = len(result['contests'])
    result['stats']['total_topics'] = len(result['topics'])
    
    return result


def step_validate(schema_version: str = "v1.0.0") -> Any:
    """
    Step 2: Validate normalized data against schemas.
    
    Returns:
        ValidationResult
    """
    print("\n" + "=" * 60)
    print("STEP 2: VALIDATION")
    print("=" * 60)
    
    # Load normalized data
    try:
        with open(os.path.join(OUTPUT_DIR, 'problems.json'), 'r') as f:
            problems = json.load(f)
        with open(os.path.join(OUTPUT_DIR, 'contests.json'), 'r') as f:
            contests = json.load(f)
        with open(os.path.join(OUTPUT_DIR, 'topics.json'), 'r') as f:
            topics = json.load(f)
    except FileNotFoundError as e:
        print(f"  ✗ Error: Normalized data not found. Run normalization first.")
        print(f"    {e}")
        return None
    
    print(f"\n  Loaded: {len(problems)} problems, {len(contests)} contests, {len(topics)} topics")
    
    # Run validation
    validator = SchemaValidator(schema_version)
    result = validator.validate_all(problems, contests, topics)
    
    # Print summary
    print(f"\n  Schema Errors: {len(result.schema_errors)}")
    print(f"  Duplicate Errors: {len(result.duplicate_errors)}")
    print(f"  Orphan Errors: {len(result.orphan_errors)}")
    print(f"  Reference Errors: {len(result.reference_errors)}")
    print(f"\n  VALID: {'✓ YES' if result.is_valid else '✗ NO'}")
    
    return result


def step_snapshot(
    version: str = None,
    schema_version: str = "v1.0.0",
    notes: str = None
) -> Dict[str, Any]:
    """
    Step 3: Create immutable versioned snapshot.
    
    Returns:
        Snapshot creation result
    """
    print("\n" + "=" * 60)
    print("STEP 3: SNAPSHOT CREATION")
    print("=" * 60)
    
    if version is None:
        version = get_next_version("patch")
    
    print(f"\n  Version: {version}")
    print(f"  Schema Version: {schema_version}")
    
    result = create_snapshot(
        version=version,
        source_dir=OUTPUT_DIR,
        schema_version=schema_version,
        notes=notes
    )
    
    if result['success']:
        print(f"\n  ✓ Snapshot created: {result['path']}")
        print(f"    Problems: {result['manifest']['counts']['problems']}")
        print(f"    Topics: {result['manifest']['counts']['topics']}")
        print(f"    Contests: {result['manifest']['counts'].get('contests', 0)}")
    else:
        print(f"\n  ✗ Failed: {result['error']}")
    
    return result


def run_pipeline(
    steps: list = None,
    dry_run: bool = False,
    schema_version: str = "v1.0.0",
    snapshot_version: str = None,
    notes: str = None
) -> PipelineResult:
    """
    Run the complete data ingestion pipeline.
    
    Args:
        steps: List of steps to run (normalize, validate, snapshot)
        dry_run: Don't save any files
        schema_version: Schema version to use
        snapshot_version: Specific version for snapshot
        notes: Notes for snapshot
        
    Returns:
        PipelineResult with aggregated results
    """
    if steps is None:
        steps = ['normalize', 'validate', 'snapshot']
    
    result = PipelineResult()
    
    print("\n" + "=" * 60)
    print("DATA INGESTION PIPELINE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Steps: {steps}")
    print(f"Dry Run: {dry_run}")
    print(f"Schema Version: {schema_version}")
    
    # Step 1: Normalization
    if 'normalize' in steps:
        try:
            norm_result = step_normalize(dry_run=dry_run)
            result.normalization = norm_result['stats']
            result.errors.extend(norm_result.get('errors', []))
            
            if norm_result['success']:
                result.steps_completed.append('normalize')
            else:
                result.steps_failed.append('normalize')
                result.success = False
        except Exception as e:
            result.steps_failed.append('normalize')
            result.errors.append(f"Normalization failed: {str(e)}")
            result.success = False
    
    # Step 2: Validation
    if 'validate' in steps and result.success:
        try:
            val_result = step_validate(schema_version)
            result.validation = val_result
            
            if val_result and val_result.is_valid:
                result.steps_completed.append('validate')
            else:
                result.steps_failed.append('validate')
                # Don't fail the whole pipeline for validation warnings
                # but don't proceed to snapshot
                if val_result and val_result.total_errors() > 0:
                    result.success = False
        except Exception as e:
            result.steps_failed.append('validate')
            result.errors.append(f"Validation failed: {str(e)}")
            result.success = False
    
    # Step 3: Snapshot
    if 'snapshot' in steps and result.success and not dry_run:
        # Only create snapshot if validation passed
        if result.validation and result.validation.is_valid:
            try:
                snap_result = step_snapshot(
                    version=snapshot_version,
                    schema_version=schema_version,
                    notes=notes
                )
                result.snapshot = snap_result
                
                if snap_result['success']:
                    result.steps_completed.append('snapshot')
                else:
                    result.steps_failed.append('snapshot')
            except Exception as e:
                result.steps_failed.append('snapshot')
                result.errors.append(f"Snapshot creation failed: {str(e)}")
        else:
            print("\n  ⚠ Skipping snapshot: Validation did not pass")
            result.warnings.append("Snapshot skipped due to validation errors")
    
    # Final summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Success: {'✓ YES' if result.success else '✗ NO'}")
    print(f"  Steps Completed: {result.steps_completed}")
    print(f"  Steps Failed: {result.steps_failed}")
    
    if result.errors:
        print(f"  Errors: {len(result.errors)}")
    if result.warnings:
        print(f"  Warnings: {len(result.warnings)}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Data Ingestion Pipeline Orchestrator"
    )
    parser.add_argument(
        '--step',
        choices=['normalize', 'validate', 'snapshot', 'all'],
        default='all',
        help="Which step to run (default: all)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't save any files"
    )
    parser.add_argument(
        '--schema-version',
        default="v1.0.0",
        help="Schema version to use (default: v1.0.0)"
    )
    parser.add_argument(
        '--snapshot-version',
        help="Specific version for snapshot (auto-increments if not specified)"
    )
    parser.add_argument(
        '--notes',
        help="Notes for the snapshot"
    )
    args = parser.parse_args()
    
    if args.step == 'all':
        steps = ['normalize', 'validate', 'snapshot']
    else:
        steps = [args.step]
    
    result = run_pipeline(
        steps=steps,
        dry_run=args.dry_run,
        schema_version=args.schema_version,
        snapshot_version=args.snapshot_version,
        notes=args.notes
    )
    
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
