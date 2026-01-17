"""
Manifest Generator

Generates manifest files with:
- Version information
- Entity counts
- SHA256 checksums
- Creation timestamps
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List


def compute_sha256(filepath: str) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        filepath: Path to file
        
    Returns:
        SHA256 hash string prefixed with 'sha256:'
    """
    sha256_hash = hashlib.sha256()
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    
    return f"sha256:{sha256_hash.hexdigest()}"


def compute_json_checksum(data: Any) -> str:
    """
    Compute SHA256 checksum of JSON data.
    
    Args:
        data: JSON-serializable data
        
    Returns:
        SHA256 hash string prefixed with 'sha256:'
    """
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    sha256_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    return f"sha256:{sha256_hash}"


def generate_manifest(
    version: str,
    schema_version: str,
    problems: List[Dict],
    topics: List[Dict],
    contests: List[Dict] = None,
    data_dir: str = None,
    notes: str = None
) -> Dict[str, Any]:
    """
    Generate a manifest for a data snapshot.
    
    Args:
        version: Snapshot version (e.g., "v1.0.0")
        schema_version: Schema version used for validation
        problems: List of problem documents
        topics: List of topic documents
        contests: List of contest documents (optional)
        data_dir: Directory containing data files (for file checksums)
        notes: Optional notes about the snapshot
        
    Returns:
        Manifest dict
    """
    manifest = {
        'version': version,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'schema_version': schema_version,
        'counts': {
            'problems': len(problems),
            'topics': len(topics),
        },
        'checksums': {},
    }
    
    if contests is not None:
        manifest['counts']['contests'] = len(contests)
    
    # Compute checksums from data
    manifest['checksums']['problems.json'] = compute_json_checksum(problems)
    manifest['checksums']['topics.json'] = compute_json_checksum(topics)
    
    if contests is not None:
        manifest['checksums']['contests.json'] = compute_json_checksum(contests)
    
    # If data_dir is provided, also compute file checksums
    if data_dir and os.path.exists(data_dir):
        for filename in ['problems.json', 'topics.json', 'contests.json']:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                manifest['checksums'][f"{filename}_file"] = compute_sha256(filepath)
    
    if notes:
        manifest['notes'] = notes
    
    return manifest


def verify_manifest(manifest: Dict, data_dir: str) -> Dict[str, Any]:
    """
    Verify manifest checksums against actual files.
    
    Args:
        manifest: Manifest to verify
        data_dir: Directory containing data files
        
    Returns:
        Verification result dict
    """
    result = {
        'valid': True,
        'mismatches': [],
        'missing': [],
    }
    
    for filename, expected_checksum in manifest.get('checksums', {}).items():
        # Skip in-memory checksums (without _file suffix)
        if not filename.endswith('_file'):
            continue
        
        actual_filename = filename.replace('_file', '')
        filepath = os.path.join(data_dir, actual_filename)
        
        if not os.path.exists(filepath):
            result['missing'].append(actual_filename)
            result['valid'] = False
            continue
        
        actual_checksum = compute_sha256(filepath)
        
        if actual_checksum != expected_checksum:
            result['mismatches'].append({
                'file': actual_filename,
                'expected': expected_checksum,
                'actual': actual_checksum,
            })
            result['valid'] = False
    
    return result


def save_manifest(manifest: Dict, filepath: str):
    """
    Save manifest to JSON file.
    
    Args:
        manifest: Manifest dict
        filepath: Path to save to
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def load_manifest(filepath: str) -> Dict:
    """
    Load manifest from JSON file.
    
    Args:
        filepath: Path to manifest file
        
    Returns:
        Manifest dict
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_checksum_file(data_dir: str, output_path: str):
    """
    Generate a checksum.txt file for all JSON files in directory.
    
    Format matches sha256sum output for easy verification.
    
    Args:
        data_dir: Directory containing files
        output_path: Path to write checksum file
    """
    lines = []
    
    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith('.json'):
            filepath = os.path.join(data_dir, filename)
            checksum = compute_sha256(filepath)
            # Format: checksum  filename (sha256sum compatible)
            hash_only = checksum.replace('sha256:', '')
            lines.append(f"{hash_only}  {filename}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
