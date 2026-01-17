"""
Validation rules for schema enforcement.
"""

from .duplicate_checker import check_duplicates, DuplicateError
from .orphan_detector import detect_orphan_topics, detect_orphan_problems
from .reference_validator import validate_r2_references, validate_uuids
