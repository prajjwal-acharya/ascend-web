"""
Schema Validator

Main validation engine that:
1. Loads versioned JSON schemas
2. Validates entities against schemas
3. Runs all validation rules
4. Aggregates errors and produces validation report
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

try:
    import jsonschema
    from jsonschema import Draft7Validator, FormatChecker
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not installed. Install with: pip install jsonschema")

from .rules.duplicate_checker import (
    check_problem_duplicates,
    check_contest_duplicates,
    check_topic_duplicates,
    check_uuid_duplicates,
    DuplicateError
)
from .rules.orphan_detector import (
    detect_orphan_topics,
    detect_orphan_problems,
    detect_orphan_parents,
    OrphanError
)
from .rules.reference_validator import (
    validate_uuids,
    validate_r2_references,
    validate_source_urls,
    validate_slug_format,
    ReferenceError
)


# Schema directory relative to this file
SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")


@dataclass
class ValidationResult:
    """Result of validation operations."""
    is_valid: bool
    schema_errors: List[Dict] = field(default_factory=list)
    duplicate_errors: List[DuplicateError] = field(default_factory=list)
    orphan_errors: List[OrphanError] = field(default_factory=list)
    reference_errors: List[ReferenceError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)
    
    def total_errors(self) -> int:
        """Get total error count."""
        return (
            len(self.schema_errors) +
            len(self.duplicate_errors) +
            len(self.orphan_errors) +
            len(self.reference_errors)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'is_valid': self.is_valid,
            'total_errors': self.total_errors(),
            'schema_errors': self.schema_errors,
            'duplicate_errors': [
                {'type': e.entity_type, 'key': e.key, 'message': e.message}
                for e in self.duplicate_errors
            ],
            'orphan_errors': [
                {'type': e.orphan_type, 'value': e.value, 'message': e.message}
                for e in self.orphan_errors
            ],
            'reference_errors': [
                {'type': e.error_type, 'field': e.field, 'value': e.value, 'message': e.message}
                for e in self.reference_errors
            ],
            'warnings': self.warnings,
            'stats': self.stats,
        }


class SchemaValidator:
    """
    Main validation engine for canonical data.
    """
    
    def __init__(self, schema_version: str = "v1.0.0"):
        """
        Initialize validator with specified schema version.
        
        Args:
            schema_version: Version of schemas to use (e.g., "v1.0.0")
        """
        self.schema_version = schema_version
        self.schemas: Dict[str, Dict] = {}
        self.validators: Dict[str, Any] = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all schemas for the specified version."""
        schema_dir = os.path.join(SCHEMAS_DIR, self.schema_version)
        
        if not os.path.exists(schema_dir):
            print(f"Warning: Schema directory not found: {schema_dir}")
            return
        
        schema_files = {
            'problem': 'problem.schema.json',
            'contest': 'contest.schema.json',
            'topic': 'topic.schema.json',
            'manifest': 'manifest.schema.json',
        }
        
        for name, filename in schema_files.items():
            filepath = os.path.join(schema_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.schemas[name] = json.load(f)
                
                if HAS_JSONSCHEMA:
                    self.validators[name] = Draft7Validator(
                        self.schemas[name],
                        format_checker=FormatChecker()
                    )
    
    def validate_entity(
        self,
        entity: Dict,
        entity_type: str
    ) -> List[Dict]:
        """
        Validate a single entity against its schema.
        
        Args:
            entity: Entity document to validate
            entity_type: Type of entity (problem, contest, topic)
            
        Returns:
            List of validation error dicts
        """
        errors = []
        
        if not HAS_JSONSCHEMA:
            # Fallback: basic required field checks
            return self._basic_validation(entity, entity_type)
        
        validator = self.validators.get(entity_type)
        if not validator:
            return [{'message': f'No validator for type: {entity_type}'}]
        
        for error in validator.iter_errors(entity):
            # Get a meaningful identifier for the entity
            entity_id = (
                entity.get('problem_id') or
                entity.get('contest_id') or
                entity.get('topic_id') or
                entity.get('name') or
                'unknown'
            )
            
            errors.append({
                'entity_id': entity_id,
                'path': '.'.join(str(p) for p in error.absolute_path),
                'message': error.message,
                'schema_path': '.'.join(str(p) for p in error.schema_path),
            })
        
        return errors
    
    def _basic_validation(self, entity: Dict, entity_type: str) -> List[Dict]:
        """
        Basic validation without jsonschema library.
        
        Args:
            entity: Entity to validate
            entity_type: Type of entity
            
        Returns:
            List of validation errors
        """
        errors = []
        
        required_fields = {
            'problem': ['problem_id', 'source', 'external_id', 'slug', 'title', 'difficulty'],
            'contest': ['contest_id', 'source', 'external_id', 'name', 'type', 'problems'],
            'topic': ['topic_id', 'name', 'category'],
        }
        
        fields = required_fields.get(entity_type, [])
        for field in fields:
            if field not in entity or entity[field] is None:
                errors.append({
                    'path': field,
                    'message': f'Missing required field: {field}'
                })
        
        return errors
    
    def validate_problems(self, problems: List[Dict]) -> ValidationResult:
        """
        Validate a list of problems.
        
        Args:
            problems: List of canonical problem documents
            
        Returns:
            ValidationResult with all errors and stats
        """
        result = ValidationResult(is_valid=True)
        result.stats['total_problems'] = len(problems)
        
        # Schema validation
        for problem in problems:
            schema_errors = self.validate_entity(problem, 'problem')
            result.schema_errors.extend(schema_errors)
        
        # Duplicate checks
        result.duplicate_errors.extend(check_problem_duplicates(problems))
        result.duplicate_errors.extend(check_uuid_duplicates(problems, 'problem_id'))
        
        # Reference validation
        result.reference_errors.extend(validate_uuids(problems, 'problem_id'))
        result.reference_errors.extend(validate_r2_references(problems))
        result.reference_errors.extend(validate_source_urls(problems))
        result.reference_errors.extend(validate_slug_format(problems))
        
        result.is_valid = result.total_errors() == 0
        return result
    
    def validate_contests(self, contests: List[Dict]) -> ValidationResult:
        """
        Validate a list of contests.
        
        Args:
            contests: List of canonical contest documents
            
        Returns:
            ValidationResult with all errors and stats
        """
        result = ValidationResult(is_valid=True)
        result.stats['total_contests'] = len(contests)
        
        # Schema validation
        for contest in contests:
            schema_errors = self.validate_entity(contest, 'contest')
            result.schema_errors.extend(schema_errors)
        
        # Duplicate checks
        result.duplicate_errors.extend(check_contest_duplicates(contests))
        result.duplicate_errors.extend(check_uuid_duplicates(contests, 'contest_id'))
        
        # UUID validation
        result.reference_errors.extend(validate_uuids(contests, 'contest_id'))
        
        result.is_valid = result.total_errors() == 0
        return result
    
    def validate_topics(self, topics: List[Dict]) -> ValidationResult:
        """
        Validate a list of topics.
        
        Args:
            topics: List of canonical topic documents
            
        Returns:
            ValidationResult with all errors and stats
        """
        result = ValidationResult(is_valid=True)
        result.stats['total_topics'] = len(topics)
        
        # Schema validation
        for topic in topics:
            schema_errors = self.validate_entity(topic, 'topic')
            result.schema_errors.extend(schema_errors)
        
        # Duplicate checks
        result.duplicate_errors.extend(check_topic_duplicates(topics))
        result.duplicate_errors.extend(check_uuid_duplicates(topics, 'topic_id'))
        
        # Orphan parent checks
        result.orphan_errors.extend(detect_orphan_parents(topics))
        
        result.is_valid = result.total_errors() == 0
        return result
    
    def validate_all(
        self,
        problems: List[Dict],
        contests: List[Dict],
        topics: List[Dict]
    ) -> ValidationResult:
        """
        Validate all entity types with cross-entity checks.
        
        Args:
            problems: List of canonical problem documents
            contests: List of canonical contest documents
            topics: List of canonical topic documents
            
        Returns:
            Combined ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        # Individual validations
        prob_result = self.validate_problems(problems)
        contest_result = self.validate_contests(contests)
        topic_result = self.validate_topics(topics)
        
        # Aggregate errors
        result.schema_errors.extend(prob_result.schema_errors)
        result.schema_errors.extend(contest_result.schema_errors)
        result.schema_errors.extend(topic_result.schema_errors)
        
        result.duplicate_errors.extend(prob_result.duplicate_errors)
        result.duplicate_errors.extend(contest_result.duplicate_errors)
        result.duplicate_errors.extend(topic_result.duplicate_errors)
        
        result.orphan_errors.extend(topic_result.orphan_errors)
        
        result.reference_errors.extend(prob_result.reference_errors)
        result.reference_errors.extend(contest_result.reference_errors)
        
        # Cross-entity validation
        result.orphan_errors.extend(detect_orphan_topics(problems, topics))
        result.orphan_errors.extend(detect_orphan_problems(contests, problems))
        
        # Aggregate stats
        result.stats = {
            'total_problems': len(problems),
            'total_contests': len(contests),
            'total_topics': len(topics),
            'schema_errors': len(result.schema_errors),
            'duplicate_errors': len(result.duplicate_errors),
            'orphan_errors': len(result.orphan_errors),
            'reference_errors': len(result.reference_errors),
        }
        
        result.is_valid = result.total_errors() == 0
        
        return result
