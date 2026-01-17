"""
Snapshot Manager

Manages immutable versioned snapshots of validated data:
- Creates new version directories
- Copies validated data
- Generates manifests and checksums
- Prevents modification of existing snapshots
"""

import os
import sys
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from .manifest_generator import (
        generate_manifest,
        save_manifest,
        generate_checksum_file,
        verify_manifest,
        load_manifest
    )
except ImportError:
    # When run as standalone script
    from manifest_generator import (
        generate_manifest,
        save_manifest,
        generate_checksum_file,
        verify_manifest,
        load_manifest
    )


# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATED_DIR = os.path.join(SCRIPT_DIR, "validated")
CANONICAL_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "modify_data", "output")


class SnapshotError(Exception):
    """Exception raised for snapshot operations."""
    pass


def get_existing_versions() -> list:
    """
    Get list of existing snapshot versions.
    
    Returns:
        Sorted list of version strings
    """
    if not os.path.exists(VALIDATED_DIR):
        return []
    
    versions = []
    for name in os.listdir(VALIDATED_DIR):
        if name.startswith('v') and os.path.isdir(os.path.join(VALIDATED_DIR, name)):
            versions.append(name)
    
    return sorted(versions)


def version_exists(version: str) -> bool:
    """
    Check if a version already exists.
    
    Args:
        version: Version string (e.g., "v1.0.0")
        
    Returns:
        True if version directory exists
    """
    return os.path.exists(os.path.join(VALIDATED_DIR, version))


def get_next_version(bump: str = "patch") -> str:
    """
    Get the next version number based on existing versions.
    
    Args:
        bump: Type of version bump (major, minor, patch)
        
    Returns:
        Next version string
    """
    versions = get_existing_versions()
    
    if not versions:
        return "v1.0.0"
    
    # Parse latest version
    latest = versions[-1]
    parts = latest.lstrip('v').split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump == "major":
        return f"v{major + 1}.0.0"
    elif bump == "minor":
        return f"v{major}.{minor + 1}.0"
    else:  # patch
        return f"v{major}.{minor}.{patch + 1}"


def create_snapshot(
    version: str,
    source_dir: str = None,
    schema_version: str = "v1.0.0",
    notes: str = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Create an immutable snapshot of validated data.
    
    Args:
        version: Version string (e.g., "v1.0.0")
        source_dir: Directory containing validated data (default: canonical output)
        schema_version: Schema version used for validation
        notes: Optional notes about this snapshot
        force: If True, overwrite existing version (dangerous!)
        
    Returns:
        Snapshot creation result dict
        
    Raises:
        SnapshotError: If version exists and force is False
    """
    if source_dir is None:
        source_dir = CANONICAL_DIR
    
    result = {
        'success': False,
        'version': version,
        'path': None,
        'manifest': None,
        'error': None,
    }
    
    # Validate version format
    if not version.startswith('v') or len(version.split('.')) != 3:
        result['error'] = f"Invalid version format: {version} (expected vX.Y.Z)"
        return result
    
    # Check if version exists
    snapshot_dir = os.path.join(VALIDATED_DIR, version)
    
    if version_exists(version):
        if not force:
            result['error'] = f"Version {version} already exists. Use force=True to overwrite."
            return result
        print(f"  ⚠ Warning: Overwriting existing version {version}")
        shutil.rmtree(snapshot_dir)
    
    # Load source data
    try:
        with open(os.path.join(source_dir, "problems.json"), 'r') as f:
            problems = json.load(f)
        
        with open(os.path.join(source_dir, "topics.json"), 'r') as f:
            topics = json.load(f)
        
        contests_path = os.path.join(source_dir, "contests.json")
        if os.path.exists(contests_path):
            with open(contests_path, 'r') as f:
                contests = json.load(f)
        else:
            contests = []
            
    except FileNotFoundError as e:
        result['error'] = f"Source data not found: {e}"
        return result
    except json.JSONDecodeError as e:
        result['error'] = f"Invalid JSON in source data: {e}"
        return result
    
    # Create snapshot directory
    os.makedirs(snapshot_dir, exist_ok=True)
    
    # Copy data files
    for filename in ['problems.json', 'topics.json', 'contests.json']:
        src = os.path.join(source_dir, filename)
        dst = os.path.join(snapshot_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
    
    # Generate manifest
    manifest = generate_manifest(
        version=version,
        schema_version=schema_version,
        problems=problems,
        topics=topics,
        contests=contests if contests else None,
        data_dir=snapshot_dir,
        notes=notes
    )
    
    # Save manifest
    save_manifest(manifest, os.path.join(snapshot_dir, "manifest.json"))
    
    # Generate checksum file
    generate_checksum_file(snapshot_dir, os.path.join(snapshot_dir, "checksum.txt"))
    
    result['success'] = True
    result['path'] = snapshot_dir
    result['manifest'] = manifest
    
    return result


def verify_snapshot(version: str) -> Dict[str, Any]:
    """
    Verify integrity of an existing snapshot.
    
    Args:
        version: Version to verify
        
    Returns:
        Verification result dict
    """
    snapshot_dir = os.path.join(VALIDATED_DIR, version)
    
    result = {
        'valid': False,
        'version': version,
        'path': snapshot_dir,
        'manifest': None,
        'errors': [],
    }
    
    if not os.path.exists(snapshot_dir):
        result['errors'].append(f"Version {version} does not exist")
        return result
    
    manifest_path = os.path.join(snapshot_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        result['errors'].append("Manifest file not found")
        return result
    
    try:
        manifest = load_manifest(manifest_path)
        result['manifest'] = manifest
    except Exception as e:
        result['errors'].append(f"Failed to load manifest: {e}")
        return result
    
    # Verify checksums
    verification = verify_manifest(manifest, snapshot_dir)
    
    if verification['missing']:
        result['errors'].append(f"Missing files: {verification['missing']}")
    
    if verification['mismatches']:
        for mismatch in verification['mismatches']:
            result['errors'].append(
                f"Checksum mismatch for {mismatch['file']}: "
                f"expected {mismatch['expected']}, got {mismatch['actual']}"
            )
    
    result['valid'] = len(result['errors']) == 0
    
    return result


def list_snapshots() -> list:
    """
    List all snapshots with their manifest info.
    
    Returns:
        List of snapshot info dicts
    """
    snapshots = []
    
    for version in get_existing_versions():
        snapshot_dir = os.path.join(VALIDATED_DIR, version)
        manifest_path = os.path.join(snapshot_dir, "manifest.json")
        
        info = {
            'version': version,
            'path': snapshot_dir,
            'manifest': None,
        }
        
        if os.path.exists(manifest_path):
            try:
                info['manifest'] = load_manifest(manifest_path)
            except Exception:
                pass
        
        snapshots.append(info)
    
    return snapshots


def get_latest_snapshot() -> Optional[Dict]:
    """
    Get the latest snapshot info.
    
    Returns:
        Snapshot info dict or None
    """
    snapshots = list_snapshots()
    return snapshots[-1] if snapshots else None


if __name__ == "__main__":
    # CLI for snapshot management
    import argparse
    
    parser = argparse.ArgumentParser(description="Snapshot Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new snapshot")
    create_parser.add_argument("--version", help="Version string (e.g., v1.0.0)")
    create_parser.add_argument("--bump", choices=["major", "minor", "patch"], default="patch")
    create_parser.add_argument("--source", help="Source data directory")
    create_parser.add_argument("--notes", help="Notes for this snapshot")
    create_parser.add_argument("--force", action="store_true", help="Overwrite existing")
    
    # List command
    subparsers.add_parser("list", help="List all snapshots")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a snapshot")
    verify_parser.add_argument("version", help="Version to verify")
    
    args = parser.parse_args()
    
    if args.command == "create":
        version = args.version or get_next_version(args.bump)
        print(f"\nCreating snapshot {version}...")
        
        result = create_snapshot(
            version=version,
            source_dir=args.source,
            notes=args.notes,
            force=args.force
        )
        
        if result['success']:
            print(f"✓ Snapshot created: {result['path']}")
            print(f"  Problems: {result['manifest']['counts']['problems']}")
            print(f"  Topics: {result['manifest']['counts']['topics']}")
            print(f"  Contests: {result['manifest']['counts'].get('contests', 0)}")
        else:
            print(f"✗ Failed: {result['error']}")
            sys.exit(1)
    
    elif args.command == "list":
        print("\nExisting Snapshots:")
        print("-" * 60)
        
        for snap in list_snapshots():
            manifest = snap.get('manifest', {})
            counts = manifest.get('counts', {})
            created = manifest.get('created_at', 'unknown')
            
            print(f"  {snap['version']}")
            print(f"    Created: {created}")
            print(f"    Problems: {counts.get('problems', '?')}")
            print(f"    Topics: {counts.get('topics', '?')}")
            print(f"    Contests: {counts.get('contests', '?')}")
            print()
    
    elif args.command == "verify":
        print(f"\nVerifying snapshot {args.version}...")
        
        result = verify_snapshot(args.version)
        
        if result['valid']:
            print(f"✓ Snapshot {args.version} is valid")
        else:
            print(f"✗ Snapshot {args.version} is INVALID")
            for err in result['errors']:
                print(f"  - {err}")
            sys.exit(1)
    
    else:
        parser.print_help()
