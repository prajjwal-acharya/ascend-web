"""
Reference Validator

Validates references and formats:
- R2 path formats
- UUID integrity
- URL formats
"""

import re
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ReferenceError:
    """Represents a reference validation error."""
    error_type: str
    field: str
    value: str
    record_id: str
    message: str


# R2 path pattern: r2://bucket/path or null
R2_PATH_PATTERN = re.compile(r'^r2://[a-z0-9-]+/[\w/.-]+$')

# URL pattern
URL_PATTERN = re.compile(r'^https?://[\w.-]+(?:/[\w./?%&=-]*)?$')


def validate_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        value: String to validate
        
    Returns:
        True if valid UUID
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_r2_path(path: Optional[str]) -> bool:
    """
    Validate R2 path format.
    
    Args:
        path: R2 path string or None
        
    Returns:
        True if valid or None
    """
    if path is None:
        return True
    return bool(R2_PATH_PATTERN.match(path))


def validate_url(url: Optional[str]) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string or None
        
    Returns:
        True if valid or None
    """
    if url is None:
        return True
    return bool(URL_PATTERN.match(url))


def validate_uuids(records: List[Dict], id_field: str = "problem_id") -> List[ReferenceError]:
    """
    Validate UUID format for all records.
    
    Args:
        records: List of records to validate
        id_field: Name of the UUID field
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for record in records:
        record_id = record.get(id_field, 'unknown')
        uuid_value = record.get(id_field)
        
        if not uuid_value:
            errors.append(ReferenceError(
                error_type="missing_uuid",
                field=id_field,
                value="",
                record_id=record_id,
                message=f"Missing {id_field}"
            ))
        elif not validate_uuid(uuid_value):
            errors.append(ReferenceError(
                error_type="invalid_uuid",
                field=id_field,
                value=uuid_value,
                record_id=record_id,
                message=f"Invalid UUID format: {uuid_value}"
            ))
    
    return errors


def validate_r2_references(problems: List[Dict]) -> List[ReferenceError]:
    """
    Validate R2 path references in problem content_refs.
    
    Args:
        problems: List of canonical problem documents
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for problem in problems:
        problem_id = problem.get('problem_id', 'unknown')
        content_refs = problem.get('content_refs', {})
        
        for field, path in content_refs.items():
            if path is not None and not validate_r2_path(path):
                errors.append(ReferenceError(
                    error_type="invalid_r2_path",
                    field=f"content_refs.{field}",
                    value=path,
                    record_id=problem_id,
                    message=f"Invalid R2 path format: {path}"
                ))
    
    return errors


def validate_source_urls(problems: List[Dict]) -> List[ReferenceError]:
    """
    Validate source URL references in problem metadata.
    
    Args:
        problems: List of canonical problem documents
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for problem in problems:
        problem_id = problem.get('problem_id', 'unknown')
        metadata = problem.get('metadata', {})
        source_url = metadata.get('source_url')
        
        if source_url and not validate_url(source_url):
            errors.append(ReferenceError(
                error_type="invalid_url",
                field="metadata.source_url",
                value=source_url,
                record_id=problem_id,
                message=f"Invalid URL format: {source_url}"
            ))
    
    return errors


def validate_slug_format(problems: List[Dict]) -> List[ReferenceError]:
    """
    Validate slug format (lowercase, hyphens, alphanumeric only).
    
    Args:
        problems: List of canonical problem documents
        
    Returns:
        List of validation errors
    """
    errors = []
    slug_pattern = re.compile(r'^[a-z0-9-]+$')
    
    for problem in problems:
        problem_id = problem.get('problem_id', 'unknown')
        slug = problem.get('slug', '')
        
        if not slug:
            errors.append(ReferenceError(
                error_type="missing_slug",
                field="slug",
                value="",
                record_id=problem_id,
                message="Missing slug"
            ))
        elif not slug_pattern.match(slug):
            errors.append(ReferenceError(
                error_type="invalid_slug",
                field="slug",
                value=slug,
                record_id=problem_id,
                message=f"Invalid slug format (must be lowercase, alphanumeric, hyphens): {slug}"
            ))
    
    return errors
