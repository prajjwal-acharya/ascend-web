#!/usr/bin/env python3
"""
Normalization Runner

Orchestrates the transformation of raw data from all platforms
into canonical format.

Usage:
    python3 run_normalization.py --source leetcode
    python3 run_normalization.py --source codeforces
    python3 run_normalization.py --source all
    python3 run_normalization.py --source all --dry-run
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

from modify_data.transformers import LeetCodeTransformer, CodeforcesTransformer


# Paths
FETCH_DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "fetch_data")
LEETCODE_DATA = os.path.join(FETCH_DATA_DIR, "leetcode", "data", "merged_problems.json")
CODEFORCES_DATA = os.path.join(FETCH_DATA_DIR, "codeforces", "data")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def save_json(data: Any, filename: str):
    """Save data to JSON file in output directory."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved: {filename} ({len(json.dumps(data))} bytes)")


def run_leetcode_normalization(dry_run: bool = False) -> Dict[str, Any]:
    """
    Run LeetCode normalization.
    
    Args:
        dry_run: If True, don't save output files
        
    Returns:
        Transformation result
    """
    print("\n" + "=" * 60)
    print("LEETCODE NORMALIZATION")
    print("=" * 60)
    
    if not os.path.exists(LEETCODE_DATA):
        print(f"  ✗ Error: LeetCode data not found at {LEETCODE_DATA}")
        return {'problems': [], 'topics': [], 'stats': {}, 'errors': ['Data file not found']}
    
    transformer = LeetCodeTransformer()
    print(f"  Loading: {LEETCODE_DATA}")
    
    result = transformer.transform_from_file(LEETCODE_DATA)
    
    print(f"\n  Stats:")
    print(f"    Total: {result['stats']['total']}")
    print(f"    Success: {result['stats']['success']}")
    print(f"    Failed: {result['stats']['failed']}")
    print(f"    Warnings: {result['stats']['warnings']}")
    print(f"    Topics extracted: {len(result['topics'])}")
    
    if result['errors']:
        print(f"\n  Errors ({len(result['errors'])}):")
        for err in result['errors'][:10]:
            print(f"    - {err}")
        if len(result['errors']) > 10:
            print(f"    ... and {len(result['errors']) - 10} more")
    
    if not dry_run:
        ensure_output_dir()
        save_json(result['problems'], 'leetcode_problems.json')
        save_json(result['topics'], 'leetcode_topics.json')
    else:
        print("\n  [DRY RUN] Output files not saved")
    
    return result


def run_codeforces_normalization(dry_run: bool = False) -> Dict[str, Any]:
    """
    Run Codeforces normalization.
    
    Args:
        dry_run: If True, don't save output files
        
    Returns:
        Transformation result
    """
    print("\n" + "=" * 60)
    print("CODEFORCES NORMALIZATION")
    print("=" * 60)
    
    if not os.path.exists(CODEFORCES_DATA):
        print(f"  ✗ Error: Codeforces data not found at {CODEFORCES_DATA}")
        return {'problems': [], 'contests': [], 'topics': [], 'stats': {}, 'errors': ['Data dir not found']}
    
    transformer = CodeforcesTransformer()
    print(f"  Loading from: {CODEFORCES_DATA}")
    
    result = transformer.transform_all(CODEFORCES_DATA)
    
    print(f"\n  Problem Stats:")
    print(f"    Total: {result['stats']['problems']['total']}")
    print(f"    Success: {result['stats']['problems']['success']}")
    print(f"    Failed: {result['stats']['problems']['failed']}")
    
    print(f"\n  Contest Stats:")
    print(f"    Total: {result['stats']['contests']['total']}")
    print(f"    Success: {result['stats']['contests']['success']}")
    print(f"    Failed: {result['stats']['contests']['failed']}")
    
    print(f"\n  Topics extracted: {len(result['topics'])}")
    
    if result['errors']:
        print(f"\n  Errors ({len(result['errors'])}):")
        for err in result['errors'][:10]:
            print(f"    - {err}")
        if len(result['errors']) > 10:
            print(f"    ... and {len(result['errors']) - 10} more")
    
    if not dry_run:
        ensure_output_dir()
        save_json(result['problems'], 'codeforces_problems.json')
        save_json(result['contests'], 'codeforces_contests.json')
        save_json(result['topics'], 'codeforces_topics.json')
    else:
        print("\n  [DRY RUN] Output files not saved")
    
    return result


def merge_topics(leetcode_topics: list, codeforces_topics: list) -> list:
    """
    Merge topics from both platforms, deduplicating by name.
    
    Args:
        leetcode_topics: Topic documents from LeetCode
        codeforces_topics: Topic documents from Codeforces
        
    Returns:
        Merged, deduplicated topic list
    """
    seen = {}
    
    for topic in leetcode_topics + codeforces_topics:
        name = topic['name']
        if name not in seen:
            seen[name] = topic
    
    return sorted(seen.values(), key=lambda t: t['name'])


def run_all_normalization(dry_run: bool = False) -> Dict[str, Any]:
    """
    Run normalization for all platforms and merge results.
    
    Args:
        dry_run: If True, don't save output files
        
    Returns:
        Merged transformation result
    """
    lc_result = run_leetcode_normalization(dry_run=True)  # Always dry-run individual
    cf_result = run_codeforces_normalization(dry_run=True)
    
    # Merge all problems
    all_problems = lc_result['problems'] + cf_result['problems']
    
    # Merge and deduplicate topics
    all_topics = merge_topics(lc_result['topics'], cf_result['topics'])
    
    # Aggregate stats
    combined_stats = {
        'leetcode': lc_result['stats'],
        'codeforces': cf_result['stats'],
        'total_problems': len(all_problems),
        'total_topics': len(all_topics),
        'total_contests': len(cf_result.get('contests', [])),
    }
    
    print("\n" + "=" * 60)
    print("COMBINED RESULTS")
    print("=" * 60)
    print(f"  Total Problems: {len(all_problems)}")
    print(f"  Total Topics: {len(all_topics)}")
    print(f"  Total Contests: {len(cf_result.get('contests', []))}")
    
    if not dry_run:
        ensure_output_dir()
        save_json(all_problems, 'problems.json')
        save_json(all_topics, 'topics.json')
        save_json(cf_result.get('contests', []), 'contests.json')
        
        # Save normalization report
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': combined_stats,
            'errors': {
                'leetcode': lc_result['errors'],
                'codeforces': cf_result['errors'],
            },
            'warnings': {
                'leetcode': lc_result.get('warnings', []),
                'codeforces': cf_result.get('warnings', []),
            }
        }
        save_json(report, 'normalization_report.json')
    
    return {
        'problems': all_problems,
        'topics': all_topics,
        'contests': cf_result.get('contests', []),
        'stats': combined_stats,
        'errors': lc_result['errors'] + cf_result['errors'],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Normalize raw platform data into canonical format"
    )
    parser.add_argument(
        '--source',
        choices=['leetcode', 'codeforces', 'all'],
        default='all',
        help="Which platform to normalize (default: all)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't save output files, just show what would be done"
    )
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("DATA NORMALIZATION PIPELINE")
    print("=" * 60)
    print(f"Source: {args.source}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    if args.source == 'leetcode':
        run_leetcode_normalization(args.dry_run)
    elif args.source == 'codeforces':
        run_codeforces_normalization(args.dry_run)
    else:
        run_all_normalization(args.dry_run)
    
    print("\n" + "=" * 60)
    print("NORMALIZATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
