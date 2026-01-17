"""
UUID Generator Utility

Generates deterministic and random UUIDs for canonical entities.
Uses UUID5 with custom namespace for reproducibility.
"""

import uuid
from typing import Optional


# Custom namespace for Ascend project
# This ensures same inputs always produce same UUIDs across runs
ASCEND_NAMESPACE = uuid.UUID('a5ce0d00-0000-4000-8000-000000000000')


def generate_uuid() -> str:
    """
    Generate a random UUID4.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def generate_deterministic_uuid(source: str, external_id: str) -> str:
    """
    Generate a deterministic UUID5 based on source and external ID.
    
    Same source + external_id will always produce the same UUID.
    This ensures reproducibility and idempotent transformations.
    
    Args:
        source: Platform source (e.g., 'leetcode', 'codeforces')
        external_id: Platform-specific ID
        
    Returns:
        UUID string
    """
    # Create a unique name by combining source and external_id
    name = f"{source}:{external_id}"
    return str(uuid.uuid5(ASCEND_NAMESPACE, name))


def generate_problem_uuid(source: str, external_id: str) -> str:
    """
    Generate a deterministic UUID for a problem.
    
    Args:
        source: Platform source
        external_id: Platform problem ID
        
    Returns:
        UUID string
    """
    return generate_deterministic_uuid(f"problem:{source}", external_id)


def generate_contest_uuid(source: str, external_id: str) -> str:
    """
    Generate a deterministic UUID for a contest.
    
    Args:
        source: Platform source
        external_id: Platform contest ID
        
    Returns:
        UUID string
    """
    return generate_deterministic_uuid(f"contest:{source}", external_id)


def generate_topic_uuid(name: str) -> str:
    """
    Generate a deterministic UUID for a topic.
    
    Topics are platform-agnostic, so we only use the normalized name.
    
    Args:
        name: Normalized topic name (lowercase, kebab-case)
        
    Returns:
        UUID string
    """
    return generate_deterministic_uuid("topic", name)


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        value: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
