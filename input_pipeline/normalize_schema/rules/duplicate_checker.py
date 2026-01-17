"""
Duplicate Checker

Detects duplicate records based on external_id + source combination.
"""

from typing import Dict, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class DuplicateError:
    """Represents a duplicate detection error."""
    entity_type: str
    key: str
    occurrences: List[Dict]
    message: str


def check_duplicates(
    records: List[Dict],
    entity_type: str = "problem",
    key_fields: Tuple[str, ...] = ("source", "external_id")
) -> List[DuplicateError]:
    """
    Check for duplicate records based on composite key.
    
    Args:
        records: List of records to check
        entity_type: Type of entity (problem, contest, topic)
        key_fields: Tuple of field names that form the unique key
        
    Returns:
        List of DuplicateError objects for each set of duplicates found
    """
    errors = []
    seen: Dict[str, List[Dict]] = {}
    
    for record in records:
        # Build composite key
        key_parts = []
        for field in key_fields:
            value = record.get(field, '')
            if isinstance(value, (list, dict)):
                value = str(value)
            key_parts.append(str(value))
        
        key = ":".join(key_parts)
        
        if key not in seen:
            seen[key] = []
        seen[key].append(record)
    
    # Find duplicates (keys with more than one record)
    for key, occurrences in seen.items():
        if len(occurrences) > 1:
            # Get identifiers for the message
            ids = []
            for occ in occurrences:
                if 'problem_id' in occ:
                    ids.append(occ['problem_id'])
                elif 'contest_id' in occ:
                    ids.append(occ['contest_id'])
                elif 'topic_id' in occ:
                    ids.append(occ['topic_id'])
                else:
                    ids.append('unknown')
            
            errors.append(DuplicateError(
                entity_type=entity_type,
                key=key,
                occurrences=occurrences,
                message=f"Duplicate {entity_type} found: key={key}, count={len(occurrences)}, ids={ids}"
            ))
    
    return errors


def check_problem_duplicates(problems: List[Dict]) -> List[DuplicateError]:
    """
    Check for duplicate problems.
    
    Args:
        problems: List of canonical problem documents
        
    Returns:
        List of duplicate errors
    """
    return check_duplicates(
        problems,
        entity_type="problem",
        key_fields=("source", "external_id")
    )


def check_contest_duplicates(contests: List[Dict]) -> List[DuplicateError]:
    """
    Check for duplicate contests.
    
    Args:
        contests: List of canonical contest documents
        
    Returns:
        List of duplicate errors
    """
    return check_duplicates(
        contests,
        entity_type="contest",
        key_fields=("source", "external_id")
    )


def check_topic_duplicates(topics: List[Dict]) -> List[DuplicateError]:
    """
    Check for duplicate topics.
    
    Topics are unique by name alone.
    
    Args:
        topics: List of canonical topic documents
        
    Returns:
        List of duplicate errors
    """
    return check_duplicates(
        topics,
        entity_type="topic",
        key_fields=("name",)
    )


def check_uuid_duplicates(records: List[Dict], id_field: str = "problem_id") -> List[DuplicateError]:
    """
    Check for duplicate UUIDs.
    
    This should never happen with deterministic UUID generation,
    but serves as a sanity check.
    
    Args:
        records: List of records to check
        id_field: Name of the UUID field
        
    Returns:
        List of duplicate errors
    """
    errors = []
    seen: Dict[str, List[Dict]] = {}
    
    for record in records:
        uuid = record.get(id_field, '')
        if uuid:
            if uuid not in seen:
                seen[uuid] = []
            seen[uuid].append(record)
    
    for uuid, occurrences in seen.items():
        if len(occurrences) > 1:
            errors.append(DuplicateError(
                entity_type="uuid",
                key=uuid,
                occurrences=occurrences,
                message=f"Duplicate UUID found: {uuid}, count={len(occurrences)}"
            ))
    
    return errors
