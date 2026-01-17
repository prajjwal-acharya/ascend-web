#!/usr/bin/env python3
"""
Validation Runner

Orchestrates validation of normalized canonical data.

Usage:
    python3 run_validation.py --input ../modify_data/output/
    python3 run_validation.py --input ../modify_data/output/ --strict
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

from normalize_schema.validator import SchemaValidator, ValidationResult


# Default paths
DEFAULT_INPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "modify_data", "output")
REJECTED_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "validate_schema", "rejected")


def load_json(filepath: str) -> Any:
    """Load JSON file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, filepath: str):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_validation(
    input_dir: str,
    schema_version: str = "v1.0.0",
    strict: bool = False
) -> ValidationResult:
    """
    Run validation on normalized data.
    
    Args:
        input_dir: Directory containing normalized JSON files
        schema_version: Schema version to use
        strict: If True, treat warnings as errors
        
    Returns:
        ValidationResult
    """
    print("\n" + "=" * 60)
    print("SCHEMA VALIDATION")
    print("=" * 60)
    print(f"Input Dir: {input_dir}")
    print(f"Schema Version: {schema_version}")
    print(f"Strict Mode: {strict}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Load data files
    print("\n[1/4] Loading data files...")
    
    problems = load_json(os.path.join(input_dir, "problems.json")) or []
    contests = load_json(os.path.join(input_dir, "contests.json")) or []
    topics = load_json(os.path.join(input_dir, "topics.json")) or []
    
    print(f"  Problems: {len(problems)}")
    print(f"  Contests: {len(contests)}")
    print(f"  Topics: {len(topics)}")
    
    if not problems and not contests and not topics:
        print("\n  ✗ Error: No data found to validate")
        return ValidationResult(
            is_valid=False,
            warnings=["No data files found"]
        )
    
    # Initialize validator
    print(f"\n[2/4] Initializing validator with schema {schema_version}...")
    validator = SchemaValidator(schema_version)
    
    if not validator.schemas:
        print("  ⚠ Warning: No schemas loaded, using basic validation")
    else:
        print(f"  Loaded schemas: {list(validator.schemas.keys())}")
    
    # Run validation
    print("\n[3/4] Running validation rules...")
    result = validator.validate_all(problems, contests, topics)
    
    # Print results
    print("\n[4/4] Validation Results:")
    print("-" * 40)
    print(f"  Schema Errors: {len(result.schema_errors)}")
    print(f"  Duplicate Errors: {len(result.duplicate_errors)}")
    print(f"  Orphan Errors: {len(result.orphan_errors)}")
    print(f"  Reference Errors: {len(result.reference_errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print("-" * 40)
    print(f"  TOTAL ERRORS: {result.total_errors()}")
    print(f"  VALID: {'✓ YES' if result.is_valid else '✗ NO'}")
    
    # Show error details
    if result.schema_errors:
        print("\n  Schema Errors (first 10):")
        for err in result.schema_errors[:10]:
            print(f"    - [{err.get('entity_id', '?')}] {err.get('path', '?')}: {err.get('message', '')}")
    
    if result.duplicate_errors:
        print("\n  Duplicate Errors:")
        for err in result.duplicate_errors[:10]:
            print(f"    - {err.message}")
    
    if result.orphan_errors:
        print("\n  Orphan Errors:")
        for err in result.orphan_errors[:10]:
            print(f"    - {err.message}")
    
    if result.reference_errors:
        print("\n  Reference Errors (first 10):")
        for err in result.reference_errors[:10]:
            print(f"    - [{err.record_id}] {err.message}")
    
    return result


def save_rejection_report(result: ValidationResult, version: str):
    """
    Save rejection report for failed validation.
    
    Args:
        result: Validation result
        version: Version string for the report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(REJECTED_DIR, f"{version}_{timestamp}")
    
    os.makedirs(report_dir, exist_ok=True)
    
    # Save detailed errors
    save_json(result.to_dict(), os.path.join(report_dir, "errors.json"))
    
    # Save summary log
    summary = [
        f"Validation Failed: {datetime.now().isoformat()}",
        f"Total Errors: {result.total_errors()}",
        f"Schema Errors: {len(result.schema_errors)}",
        f"Duplicate Errors: {len(result.duplicate_errors)}",
        f"Orphan Errors: {len(result.orphan_errors)}",
        f"Reference Errors: {len(result.reference_errors)}",
        "",
        "=== ERRORS ===",
    ]
    
    for err in result.schema_errors:
        summary.append(f"[SCHEMA] {err}")
    for err in result.duplicate_errors:
        summary.append(f"[DUPLICATE] {err.message}")
    for err in result.orphan_errors:
        summary.append(f"[ORPHAN] {err.message}")
    for err in result.reference_errors:
        summary.append(f"[REFERENCE] {err.message}")
    
    with open(os.path.join(report_dir, "errors.log"), 'w') as f:
        f.write('\n'.join(summary))
    
    print(f"\n  Rejection report saved to: {report_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate normalized canonical data against schemas"
    )
    parser.add_argument(
        '--input',
        default=DEFAULT_INPUT_DIR,
        help=f"Directory containing normalized JSON files (default: {DEFAULT_INPUT_DIR})"
    )
    parser.add_argument(
        '--schema-version',
        default="v1.0.0",
        help="Schema version to use (default: v1.0.0)"
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help="Treat warnings as errors"
    )
    parser.add_argument(
        '--save-report',
        action='store_true',
        help="Save rejection report if validation fails"
    )
    args = parser.parse_args()
    
    result = run_validation(
        input_dir=args.input,
        schema_version=args.schema_version,
        strict=args.strict
    )
    
    if not result.is_valid and args.save_report:
        save_rejection_report(result, args.schema_version)
    
    print("\n" + "=" * 60)
    if result.is_valid:
        print("VALIDATION PASSED ✓")
    else:
        print("VALIDATION FAILED ✗")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
