"""
Orphan Detector

Detects orphan references:
- Topics used in problems but not defined in topics list
- Problems referenced in contests but not defined in problems list
"""

from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class OrphanError:
    """Represents an orphan detection error."""
    orphan_type: str
    value: str
    referenced_by: List[str]
    message: str


def detect_orphan_topics(
    problems: List[Dict],
    topics: List[Dict]
) -> List[OrphanError]:
    """
    Detect topics used in problems but not defined in topics list.
    
    Args:
        problems: List of canonical problem documents
        topics: List of canonical topic documents
        
    Returns:
        List of orphan errors for undefined topics
    """
    errors = []
    
    # Build set of defined topic names
    defined_topics = {t.get('name', '') for t in topics}
    
    # Track which problems use each undefined topic
    undefined_usage: Dict[str, List[str]] = {}
    
    for problem in problems:
        problem_id = problem.get('problem_id', 'unknown')
        problem_topics = problem.get('topics', [])
        
        for topic in problem_topics:
            if topic not in defined_topics:
                if topic not in undefined_usage:
                    undefined_usage[topic] = []
                undefined_usage[topic].append(problem_id)
    
    # Create errors for each undefined topic
    for topic, problem_ids in undefined_usage.items():
        errors.append(OrphanError(
            orphan_type="topic",
            value=topic,
            referenced_by=problem_ids,
            message=f"Orphan topic '{topic}' used in {len(problem_ids)} problems but not defined"
        ))
    
    return errors


def detect_orphan_problems(
    contests: List[Dict],
    problems: List[Dict]
) -> List[OrphanError]:
    """
    Detect problems referenced in contests but not defined in problems list.
    
    Args:
        contests: List of canonical contest documents
        problems: List of canonical problem documents
        
    Returns:
        List of orphan errors for undefined problem references
    """
    errors = []
    
    # Build set of defined problem external_ids (with source prefix)
    defined_problems = {
        f"{p.get('source', '')}:{p.get('external_id', '')}"
        for p in problems
    }
    
    # Track which contests reference each undefined problem
    undefined_usage: Dict[str, List[str]] = {}
    
    for contest in contests:
        contest_id = contest.get('contest_id', 'unknown')
        source = contest.get('source', '')
        problem_refs = contest.get('problems', [])
        
        for ref in problem_refs:
            external_id = ref.get('problem_external_id', '')
            key = f"{source}:{external_id}"
            
            if key not in defined_problems:
                if key not in undefined_usage:
                    undefined_usage[key] = []
                undefined_usage[key].append(contest_id)
    
    # Create errors for each undefined problem
    for problem_key, contest_ids in undefined_usage.items():
        errors.append(OrphanError(
            orphan_type="problem",
            value=problem_key,
            referenced_by=contest_ids,
            message=f"Orphan problem '{problem_key}' referenced in {len(contest_ids)} contests but not defined"
        ))
    
    return errors


def detect_orphan_parents(topics: List[Dict]) -> List[OrphanError]:
    """
    Detect parent topics that don't exist.
    
    Args:
        topics: List of canonical topic documents
        
    Returns:
        List of orphan errors for undefined parent topics
    """
    errors = []
    
    # Build set of defined topic names
    defined_topics = {t.get('name', '') for t in topics}
    
    # Track which topics reference undefined parents
    undefined_usage: Dict[str, List[str]] = {}
    
    for topic in topics:
        parent = topic.get('parent')
        if parent and parent not in defined_topics:
            if parent not in undefined_usage:
                undefined_usage[parent] = []
            undefined_usage[parent].append(topic.get('name', 'unknown'))
    
    # Create errors for each undefined parent
    for parent, child_names in undefined_usage.items():
        errors.append(OrphanError(
            orphan_type="parent_topic",
            value=parent,
            referenced_by=child_names,
            message=f"Orphan parent topic '{parent}' referenced by {len(child_names)} topics but not defined"
        ))
    
    return errors
