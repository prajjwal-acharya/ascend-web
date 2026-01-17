"""
LeetCode Transformer

Transforms raw LeetCode data from merged_problems.json
into canonical problem format.
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..utils.html_stripper import html_to_markdown, extract_examples, extract_constraints
from ..utils.uuid_generator import generate_problem_uuid
from ..utils.topic_normalizer import normalize_topics


@dataclass
class TransformResult:
    """Result of a transformation operation."""
    success: bool
    data: Optional[Dict] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        self.errors = self.errors or []
        self.warnings = self.warnings or []


class LeetCodeTransformer:
    """
    Transforms LeetCode raw data into canonical format.
    
    Input: merged_problems.json or individual problem JSONs
    Output: Canonical problem documents + topics list
    """
    
    SOURCE = "leetcode"
    
    def __init__(self, content_base_path: str = "r2://problems/leetcode"):
        """
        Initialize transformer.
        
        Args:
            content_base_path: Base path for R2 content references
        """
        self.content_base_path = content_base_path
        self.all_topics = set()
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'warnings': 0,
        }
    
    def transform_problem(self, raw: Dict) -> TransformResult:
        """
        Transform a single raw LeetCode problem to canonical format.
        
        Args:
            raw: Raw problem data from LeetCode
            
        Returns:
            TransformResult with canonical problem or errors
        """
        errors = []
        warnings = []
        
        # Extract external ID
        external_id = str(raw.get('problem_id') or raw.get('questionId') or '')
        if not external_id:
            frontend_id = raw.get('frontend_id') or raw.get('questionFrontendId')
            if frontend_id:
                external_id = str(frontend_id)
        
        if not external_id:
            return TransformResult(
                success=False,
                errors=["Missing external_id (problem_id, questionId, or frontend_id)"]
            )
        
        # Extract slug
        slug = raw.get('problem_slug') or raw.get('titleSlug') or ''
        if not slug:
            return TransformResult(
                success=False,
                errors=[f"Missing slug for problem {external_id}"]
            )
        
        # Extract title
        title = raw.get('title') or raw.get('questionTitle') or ''
        if not title:
            warnings.append(f"Missing title for {slug}, using slug as title")
            title = slug.replace('-', ' ').title()
        
        # Normalize difficulty
        raw_difficulty = raw.get('difficulty', '').lower()
        difficulty_map = {
            'easy': 'easy',
            'medium': 'medium',
            'hard': 'hard',
            '1': 'easy',
            '2': 'medium',
            '3': 'hard',
        }
        difficulty = difficulty_map.get(raw_difficulty, 'medium')
        if raw_difficulty and raw_difficulty not in difficulty_map:
            warnings.append(f"Unknown difficulty '{raw_difficulty}', defaulting to 'medium'")
        
        # Extract and normalize topics
        raw_topics = raw.get('topicTags') or raw.get('topics') or []
        if isinstance(raw_topics, list):
            if raw_topics and isinstance(raw_topics[0], dict):
                # LeetCode format: [{"name": "Array", "slug": "array"}, ...]
                topic_names = [t.get('name') or t.get('slug', '') for t in raw_topics]
            else:
                topic_names = raw_topics
        else:
            topic_names = []
        
        topics = normalize_topics(topic_names)
        self.all_topics.update(topics)
        
        # Build content refs
        content_refs = {
            'description_path': f"{self.content_base_path}/{slug}/description.md",
            'examples_path': f"{self.content_base_path}/{slug}/examples.json",
            'constraints_path': f"{self.content_base_path}/{slug}/constraints.json",
        }
        
        # Check if we have description content
        description = raw.get('description') or raw.get('question') or raw.get('content')
        if not description:
            content_refs['description_path'] = None
            warnings.append(f"No description content for {slug}")
        
        # Build metadata
        metadata = {
            'frontend_id': raw.get('frontend_id') or raw.get('questionFrontendId') or external_id,
            'contest_index': None,  # LeetCode problems aren't contest-indexed
            'source_url': f"https://leetcode.com/problems/{slug}/",
        }
        
        # Add optional fields to metadata if present
        if raw.get('isPaidOnly') or raw.get('paidOnly'):
            metadata['is_premium'] = True
        if raw.get('acRate'):
            metadata['accept_rate'] = raw.get('acRate')
        if raw.get('likes'):
            metadata['likes'] = raw.get('likes')
        if raw.get('dislikes'):
            metadata['dislikes'] = raw.get('dislikes')
        
        # Generate deterministic UUID
        problem_id = generate_problem_uuid(self.SOURCE, external_id)
        
        # Build canonical document
        canonical = {
            'problem_id': problem_id,
            'source': self.SOURCE,
            'external_id': external_id,
            'slug': slug,
            'title': title,
            'difficulty': difficulty,
            'rating': None,  # LeetCode doesn't have numeric ratings
            'metadata': metadata,
            'topics': topics,
            'content_refs': content_refs,
        }
        
        return TransformResult(
            success=True,
            data=canonical,
            warnings=warnings
        )
    
    def transform_all(self, raw_problems: List[Dict]) -> Dict[str, Any]:
        """
        Transform all raw problems to canonical format.
        
        Args:
            raw_problems: List of raw LeetCode problems
            
        Returns:
            Dict with 'problems', 'topics', 'stats', 'errors', 'warnings'
        """
        self.all_topics = set()
        self.stats = {'total': len(raw_problems), 'success': 0, 'failed': 0, 'warnings': 0}
        
        canonical_problems = []
        all_errors = []
        all_warnings = []
        
        for raw in raw_problems:
            result = self.transform_problem(raw)
            
            if result.success:
                canonical_problems.append(result.data)
                self.stats['success'] += 1
                if result.warnings:
                    self.stats['warnings'] += len(result.warnings)
                    all_warnings.extend(result.warnings)
            else:
                self.stats['failed'] += 1
                # Include identifier in error context
                slug = raw.get('titleSlug') or raw.get('problem_slug') or 'unknown'
                for err in result.errors:
                    all_errors.append(f"[{slug}] {err}")
        
        # Build topic documents
        from ..utils.topic_normalizer import build_topic_document
        topic_docs = [build_topic_document(name) for name in sorted(self.all_topics)]
        
        return {
            'problems': canonical_problems,
            'topics': topic_docs,
            'stats': self.stats,
            'errors': all_errors,
            'warnings': all_warnings,
        }
    
    def transform_from_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load and transform problems from a JSON file.
        
        Args:
            filepath: Path to merged_problems.json or similar
            
        Returns:
            Transformation result dict
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different file formats
        if isinstance(data, list):
            problems = data
        elif isinstance(data, dict):
            problems = data.get('questions') or data.get('problems') or []
        else:
            return {
                'problems': [],
                'topics': [],
                'stats': {'total': 0, 'success': 0, 'failed': 1, 'warnings': 0},
                'errors': ['Invalid JSON format - expected list or dict'],
                'warnings': [],
            }
        
        return self.transform_all(problems)
    
    def extract_content(self, raw: Dict) -> Dict[str, Any]:
        """
        Extract content (description, examples, constraints) from raw problem.
        
        This is separate from transform_problem because content extraction
        may be stored separately in R2.
        
        Args:
            raw: Raw problem data
            
        Returns:
            Dict with 'description', 'examples', 'constraints'
        """
        description_html = raw.get('description') or raw.get('question') or raw.get('content') or ''
        
        return {
            'description': html_to_markdown(description_html),
            'examples': extract_examples(description_html) or raw.get('examples', []),
            'constraints': extract_constraints(description_html) or raw.get('constraints', []),
            'hints': raw.get('hints', []),
            'code_snippets': raw.get('code_snippets') or raw.get('codeSnippets', []),
        }
