"""
Codeforces Transformer

Transforms raw Codeforces data from per-contest JSON files
into canonical problem and contest formats.
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..utils.uuid_generator import generate_problem_uuid, generate_contest_uuid
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


class CodeforcesTransformer:
    """
    Transforms Codeforces raw data into canonical format.
    
    Input: Per-contest JSON files ({contestId}.json)
    Output: Canonical problem + contest documents
    """
    
    SOURCE = "codeforces"
    
    # Rating to difficulty mapping
    RATING_RANGES = {
        'easy': (0, 1200),      # 800-1200
        'medium': (1200, 1800), # 1200-1800
        'hard': (1800, 4000),   # 1800+
    }
    
    def __init__(self, content_base_path: str = "r2://problems/codeforces"):
        """
        Initialize transformer.
        
        Args:
            content_base_path: Base path for R2 content references
        """
        self.content_base_path = content_base_path
        self.all_topics = set()
        self.stats = {
            'problems': {'total': 0, 'success': 0, 'failed': 0, 'warnings': 0},
            'contests': {'total': 0, 'success': 0, 'failed': 0, 'warnings': 0},
        }
    
    def rating_to_difficulty(self, rating: Optional[int]) -> str:
        """
        Convert Codeforces rating to difficulty category.
        
        Args:
            rating: Numeric rating (800-3500)
            
        Returns:
            Difficulty string (easy, medium, hard)
        """
        if rating is None:
            return 'medium'  # Default for unrated
        
        if rating < self.RATING_RANGES['easy'][1]:
            return 'easy'
        elif rating < self.RATING_RANGES['medium'][1]:
            return 'medium'
        else:
            return 'hard'
    
    def transform_problem(self, raw: Dict, contest_id: str) -> TransformResult:
        """
        Transform a single Codeforces problem to canonical format.
        
        Args:
            raw: Raw problem data from Codeforces
            contest_id: Parent contest ID
            
        Returns:
            TransformResult with canonical problem or errors
        """
        errors = []
        warnings = []
        
        # Build external_id from contestId and index
        problem_contest_id = str(raw.get('contestId', contest_id))
        index = raw.get('index', '')
        
        if not index:
            return TransformResult(
                success=False,
                errors=[f"Missing index for problem in contest {problem_contest_id}"]
            )
        
        external_id = f"{problem_contest_id}-{index}"
        
        # Extract title/name
        title = raw.get('name', '')
        if not title:
            warnings.append(f"Missing name for problem {external_id}")
            title = f"Problem {index}"
        
        # Create slug from title (ASCII only)
        import re
        # Remove non-ASCII characters first, then normalize
        ascii_title = title.encode('ascii', 'ignore').decode('ascii')
        slug = ascii_title.lower()
        slug = ''.join(c if c.isalnum() or c == ' ' else '' for c in slug)
        slug = slug.strip().replace(' ', '-')
        slug = re.sub(r'-+', '-', slug)  # Collapse multiple hyphens
        slug = slug[:30] if slug else 'problem'  # Fallback if all non-ASCII
        slug = f"{problem_contest_id.lower()}-{index.lower()}-{slug}"
        
        # Rating and difficulty
        rating = raw.get('rating')
        if rating is not None:
            try:
                rating = int(rating)
            except (ValueError, TypeError):
                warnings.append(f"Invalid rating '{rating}' for {external_id}")
                rating = None
        
        difficulty = self.rating_to_difficulty(rating)
        
        # Extract and normalize topics
        raw_topics = raw.get('tags', [])
        topics = normalize_topics(raw_topics)
        self.all_topics.update(topics)
        
        # Build metadata
        metadata = {
            'frontend_id': None,  # CF doesn't have frontend IDs
            'contest_index': index,
            'source_url': f"https://codeforces.com/problemset/problem/{problem_contest_id}/{index}",
        }
        
        # Add points if available
        if raw.get('points'):
            metadata['points'] = raw.get('points')
        
        # Content refs - Codeforces doesn't provide problem text via API
        # These paths are placeholders for future scraping
        content_refs = {
            'description_path': None,  # Not available via API
            'examples_path': None,
            'constraints_path': None,
        }
        
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
            'rating': rating,
            'metadata': metadata,
            'topics': topics,
            'content_refs': content_refs,
        }
        
        return TransformResult(
            success=True,
            data=canonical,
            warnings=warnings
        )
    
    def transform_contest(self, raw: Dict, problems: List[Dict]) -> TransformResult:
        """
        Transform a Codeforces contest to canonical format.
        
        Args:
            raw: Raw contest data
            problems: List of canonical problem documents for this contest
            
        Returns:
            TransformResult with canonical contest or errors
        """
        errors = []
        warnings = []
        
        external_id = str(raw.get('id', ''))
        if not external_id:
            return TransformResult(
                success=False,
                errors=["Missing contest id"]
            )
        
        name = raw.get('name', '')
        if not name:
            warnings.append(f"Missing name for contest {external_id}")
            name = f"Contest {external_id}"
        
        # Contest type
        contest_type = raw.get('type', 'CF')
        if contest_type not in ['ICPC', 'CF', 'IOI']:
            warnings.append(f"Unknown contest type '{contest_type}' for {external_id}")
        
        # Validate phase
        phase = raw.get('phase', 'FINISHED')
        if phase != 'FINISHED':
            warnings.append(f"Contest {external_id} has phase '{phase}', expected FINISHED")
        
        # Duration
        duration = raw.get('durationSeconds', 0)
        
        # Start time
        start_time = raw.get('startTimeSeconds')
        
        # Build problem references
        problem_refs = []
        for p in problems:
            problem_refs.append({
                'problem_external_id': p['external_id'],
                'index': p['metadata']['contest_index'],
            })
        
        # Generate deterministic UUID
        contest_id = generate_contest_uuid(self.SOURCE, external_id)
        
        # Build canonical document
        canonical = {
            'contest_id': contest_id,
            'source': self.SOURCE,
            'external_id': external_id,
            'name': name,
            'type': contest_type,
            'duration_seconds': duration,
            'start_time': start_time,
            'phase': phase,
            'problems': problem_refs,
        }
        
        return TransformResult(
            success=True,
            data=canonical,
            warnings=warnings
        )
    
    def transform_contest_file(self, filepath: str) -> Dict[str, Any]:
        """
        Transform a single contest JSON file.
        
        Args:
            filepath: Path to {contestId}.json
            
        Returns:
            Dict with 'contest', 'problems', 'errors', 'warnings'
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        raw_contest = data.get('contest', {})
        raw_problems = data.get('problems', [])
        
        contest_id = str(raw_contest.get('id', ''))
        
        # Transform problems
        canonical_problems = []
        all_errors = []
        all_warnings = []
        
        for raw_problem in raw_problems:
            result = self.transform_problem(raw_problem, contest_id)
            if result.success:
                canonical_problems.append(result.data)
                self.stats['problems']['success'] += 1
                if result.warnings:
                    self.stats['problems']['warnings'] += len(result.warnings)
                    all_warnings.extend(result.warnings)
            else:
                self.stats['problems']['failed'] += 1
                for err in result.errors:
                    all_errors.append(f"[contest:{contest_id}] {err}")
        
        self.stats['problems']['total'] += len(raw_problems)
        
        # Transform contest
        contest_result = self.transform_contest(raw_contest, canonical_problems)
        self.stats['contests']['total'] += 1
        
        if contest_result.success:
            self.stats['contests']['success'] += 1
            if contest_result.warnings:
                self.stats['contests']['warnings'] += len(contest_result.warnings)
                all_warnings.extend(contest_result.warnings)
        else:
            self.stats['contests']['failed'] += 1
            all_errors.extend(contest_result.errors)
        
        return {
            'contest': contest_result.data if contest_result.success else None,
            'problems': canonical_problems,
            'errors': all_errors,
            'warnings': all_warnings,
        }
    
    def transform_all(self, data_dir: str) -> Dict[str, Any]:
        """
        Transform all contest files in a directory.
        
        Args:
            data_dir: Directory containing {contestId}.json files
            
        Returns:
            Dict with 'problems', 'contests', 'topics', 'stats', 'errors', 'warnings'
        """
        self.all_topics = set()
        self.stats = {
            'problems': {'total': 0, 'success': 0, 'failed': 0, 'warnings': 0},
            'contests': {'total': 0, 'success': 0, 'failed': 0, 'warnings': 0},
        }
        
        all_problems = []
        all_contests = []
        all_errors = []
        all_warnings = []
        
        # Find all JSON files
        json_files = sorted([
            f for f in os.listdir(data_dir) 
            if f.endswith('.json') and f[:-5].isdigit()  # Only contest ID files
        ])
        
        for filename in json_files:
            filepath = os.path.join(data_dir, filename)
            try:
                result = self.transform_contest_file(filepath)
                
                if result['contest']:
                    all_contests.append(result['contest'])
                all_problems.extend(result['problems'])
                all_errors.extend(result['errors'])
                all_warnings.extend(result['warnings'])
                
            except Exception as e:
                all_errors.append(f"[{filename}] Failed to process: {str(e)}")
                self.stats['contests']['failed'] += 1
        
        # Build topic documents
        from ..utils.topic_normalizer import build_topic_document
        topic_docs = [build_topic_document(name) for name in sorted(self.all_topics)]
        
        return {
            'problems': all_problems,
            'contests': all_contests,
            'topics': topic_docs,
            'stats': self.stats,
            'errors': all_errors,
            'warnings': all_warnings,
        }
