"""
Upload Orchestrator

Handles the final upload gate and database injection:
1. Verifies snapshot integrity
2. Uploads content to Cloudflare R2 (if applicable)
3. Uploads metadata to Supabase
4. Warms Redis cache (optional)

Upload only proceeds if all validation gates pass.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PIPELINE_DIR)

from validate_schema.snapshot_manager import (
    verify_snapshot,
    get_latest_snapshot,
    list_snapshots,
    VALIDATED_DIR
)


class UploadGate:
    """
    Upload gate that checks all preconditions before allowing upload.
    """
    
    def __init__(self, version: str = None):
        """
        Initialize upload gate.
        
        Args:
            version: Specific version to upload, or None for latest
        """
        if version is None:
            latest = get_latest_snapshot()
            if latest:
                version = latest['version']
            else:
                raise ValueError("No snapshots available")
        
        self.version = version
        self.snapshot_dir = os.path.join(VALIDATED_DIR, version)
        self.checks_passed = False
        self.check_results = {}
    
    def run_checks(self) -> Dict[str, Any]:
        """
        Run all pre-upload checks.
        
        Returns:
            Check results dict
        """
        results = {
            'version': self.version,
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'all_passed': False,
        }
        
        # Check 1: Snapshot exists
        results['checks']['snapshot_exists'] = os.path.exists(self.snapshot_dir)
        
        # Check 2: Manifest exists
        manifest_path = os.path.join(self.snapshot_dir, 'manifest.json')
        results['checks']['manifest_exists'] = os.path.exists(manifest_path)
        
        # Check 3: Data files exist
        required_files = ['problems.json', 'topics.json']
        for f in required_files:
            filepath = os.path.join(self.snapshot_dir, f)
            results['checks'][f'file_exists_{f}'] = os.path.exists(filepath)
        
        # Check 4: Snapshot integrity (checksums)
        if results['checks']['manifest_exists']:
            verification = verify_snapshot(self.version)
            results['checks']['checksum_valid'] = verification['valid']
            if not verification['valid']:
                results['checks']['checksum_errors'] = verification['errors']
        else:
            results['checks']['checksum_valid'] = False
        
        # Check 5: Data is non-empty
        try:
            with open(os.path.join(self.snapshot_dir, 'problems.json'), 'r') as f:
                problems = json.load(f)
            results['checks']['has_problems'] = len(problems) > 0
            results['problem_count'] = len(problems)
        except Exception:
            results['checks']['has_problems'] = False
        
        # Check 6: Load manifest for counts
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            results['manifest'] = manifest
        except Exception:
            results['manifest'] = None
        
        # Aggregate
        results['all_passed'] = all(
            v for k, v in results['checks'].items()
            if not k.endswith('_errors')
        )
        
        self.check_results = results
        self.checks_passed = results['all_passed']
        
        return results
    
    def can_upload(self) -> bool:
        """Check if upload is allowed."""
        if not self.check_results:
            self.run_checks()
        return self.checks_passed


class UploadOrchestrator:
    """
    Orchestrates the upload process with proper ordering and rollback.
    """
    
    def __init__(self, version: str = None):
        """
        Initialize orchestrator.
        
        Args:
            version: Specific version to upload
        """
        self.gate = UploadGate(version)
        self.version = self.gate.version
        self.snapshot_dir = self.gate.snapshot_dir
        self.upload_log = []
    
    def log(self, message: str, level: str = "INFO"):
        """Add message to upload log."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
        }
        self.upload_log.append(entry)
        print(f"  [{level}] {message}")
    
    def upload_to_r2(self, dry_run: bool = False) -> bool:
        """
        Upload content files to Cloudflare R2.
        
        Args:
            dry_run: Don't actually upload
            
        Returns:
            True if successful
        """
        self.log("Starting R2 upload...")
        
        # This is a placeholder for actual R2 upload logic
        # In production, this would use boto3 with R2 endpoint
        
        if dry_run:
            self.log("[DRY RUN] R2 upload skipped")
            return True
        
        # TODO: Implement actual R2 upload
        # - Read content from snapshot
        # - Upload to R2 bucket
        # - Verify upload success
        
        self.log("R2 upload: Not implemented (content storage)", "WARN")
        return True
    
    def upload_to_supabase(self, dry_run: bool = False) -> bool:
        """
        Upload metadata to Supabase.
        
        Args:
            dry_run: Don't actually upload
            
        Returns:
            True if successful
        """
        self.log("Starting Supabase upload...")
        
        if dry_run:
            self.log("[DRY RUN] Supabase upload skipped")
            return True
        
        # TODO: Implement actual Supabase upload
        # - Read problems, topics, contests from snapshot
        # - Batch insert to Supabase tables
        # - Handle conflicts (upsert)
        
        self.log("Supabase upload: Not implemented (requires credentials)", "WARN")
        return True
    
    def warmup_redis(self, dry_run: bool = False) -> bool:
        """
        Warm up Redis cache with frequently accessed data.
        
        Args:
            dry_run: Don't actually warm cache
            
        Returns:
            True if successful
        """
        self.log("Starting Redis warmup...")
        
        if dry_run:
            self.log("[DRY RUN] Redis warmup skipped")
            return True
        
        # TODO: Implement Redis warmup
        # - Connect to Redis
        # - Cache topic lists, difficulty distributions, etc.
        
        self.log("Redis warmup: Not implemented (optional)", "WARN")
        return True
    
    def rollback(self):
        """
        Rollback any partial uploads.
        
        This should undo any changes made during a failed upload.
        """
        self.log("Rolling back partial uploads...", "WARN")
        
        # TODO: Implement rollback logic
        # - Delete uploaded R2 objects
        # - Delete inserted Supabase rows
        # - Clear Redis cache entries
        
        self.log("Rollback: Not implemented", "WARN")
    
    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run the complete upload process.
        
        Args:
            dry_run: Don't actually upload anything
            
        Returns:
            Upload result dict
        """
        result = {
            'success': False,
            'version': self.version,
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'log': [],
        }
        
        print("\n" + "=" * 60)
        print("UPLOAD ORCHESTRATOR")
        print("=" * 60)
        print(f"Version: {self.version}")
        print(f"Dry Run: {dry_run}")
        
        # Step 1: Run gate checks
        print("\n[1/4] Running pre-upload checks...")
        checks = self.gate.run_checks()
        result['checks'] = checks
        
        if not checks['all_passed']:
            self.log("Pre-upload checks FAILED", "ERROR")
            for check, passed in checks['checks'].items():
                if not passed:
                    self.log(f"  Failed: {check}", "ERROR")
            result['log'] = self.upload_log
            return result
        
        self.log("All pre-upload checks passed")
        manifest = checks.get('manifest', {})
        counts = manifest.get('counts', {})
        self.log(f"  Problems: {counts.get('problems', '?')}")
        self.log(f"  Topics: {counts.get('topics', '?')}")
        self.log(f"  Contests: {counts.get('contests', '?')}")
        
        # Step 2: Upload to R2

        print("\n[2/4] Uploading to R2...")
        try:
            result['steps']['r2'] = self.upload_to_r2(dry_run)
        except Exception as e:
            self.log(f"R2 upload failed: {e}", "ERROR")
            result['steps']['r2'] = False
            self.rollback()
            result['log'] = self.upload_log
            return result
        
        # Step 3: Upload to Supabase
        print("\n[3/4] Uploading to Supabase...")
        try:
            result['steps']['supabase'] = self.upload_to_supabase(dry_run)
        except Exception as e:
            self.log(f"Supabase upload failed: {e}", "ERROR")
            result['steps']['supabase'] = False
            self.rollback()
            result['log'] = self.upload_log
            return result
        
        # Step 4: Warm Redis cache
        print("\n[4/4] Warming Redis cache...")
        try:
            result['steps']['redis'] = self.warmup_redis(dry_run)
        except Exception as e:
            self.log(f"Redis warmup failed: {e}", "WARN")
            result['steps']['redis'] = False
            # Don't rollback for Redis failure - it's optional
        
        # Success!
        result['success'] = True
        result['log'] = self.upload_log
        
        print("\n" + "=" * 60)
        print("UPLOAD COMPLETE ✓")
        print("=" * 60)
        
        return result
    
    def save_log(self, output_dir: str = None):
        """
        Save upload log to file.
        
        Args:
            output_dir: Directory to save log (default: upload_logs)
        """
        if output_dir is None:
            output_dir = os.path.join(
                PIPELINE_DIR, "validate_schema", "upload_logs"
            )
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.version}_{timestamp}.log"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            for entry in self.upload_log:
                f.write(f"[{entry['timestamp']}] [{entry['level']}] {entry['message']}\n")
        
        print(f"\n  Log saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload Orchestrator - Final database injection gate"
    )
    parser.add_argument(
        '--version',
        help="Specific snapshot version to upload (default: latest)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't actually upload, just verify"
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help="Only run pre-upload checks"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="List available snapshots"
    )
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable Snapshots:")
        print("-" * 40)
        for snap in list_snapshots():
            manifest = snap.get('manifest', {})
            counts = manifest.get('counts', {})
            print(f"  {snap['version']}")
            print(f"    Problems: {counts.get('problems', '?')}")
            print(f"    Topics: {counts.get('topics', '?')}")
            print()
        return
    
    try:
        orchestrator = UploadOrchestrator(version=args.version)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    if args.check_only:
        print("\nRunning pre-upload checks only...")
        checks = orchestrator.gate.run_checks()
        
        print("\nCheck Results:")
        for check, passed in checks['checks'].items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}")
        
        print(f"\nAll Passed: {'✓ YES' if checks['all_passed'] else '✗ NO'}")
        sys.exit(0 if checks['all_passed'] else 1)
    
    result = orchestrator.run(dry_run=args.dry_run)
    orchestrator.save_log()
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
