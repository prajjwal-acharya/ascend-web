"""
Topic Normalizer Utility

Normalizes and standardizes topic names across platforms.
Handles topic mapping, hierarchy, and categorization.
"""

import re
from typing import List, Optional, Dict


# Mapping from platform-specific topic names to canonical names
# Format: 'platform_name': 'canonical_name'
TOPIC_MAPPING: Dict[str, str] = {
    # LeetCode topics (Title Case) -> canonical (kebab-case)
    'Array': 'array',
    'Hash Table': 'hash-table',
    'Linked List': 'linked-list',
    'Math': 'math',
    'Two Pointers': 'two-pointers',
    'String': 'string',
    'Binary Search': 'binary-search',
    'Divide and Conquer': 'divide-and-conquer',
    'Dynamic Programming': 'dynamic-programming',
    'Backtracking': 'backtracking',
    'Stack': 'stack',
    'Heap (Priority Queue)': 'heap',
    'Heap': 'heap',
    'Priority Queue': 'heap',
    'Greedy': 'greedy',
    'Sort': 'sorting',
    'Sorting': 'sorting',
    'Bit Manipulation': 'bit-manipulation',
    'Tree': 'tree',
    'Depth-First Search': 'dfs',
    'DFS': 'dfs',
    'dfs': 'dfs',
    'Breadth-First Search': 'bfs',
    'BFS': 'bfs',
    'bfs': 'bfs',
    'Union Find': 'union-find',
    'Graph': 'graph',
    'Design': 'design',
    'Topological Sort': 'topological-sort',
    'Trie': 'trie',
    'Binary Indexed Tree': 'binary-indexed-tree',
    'Segment Tree': 'segment-tree',
    'Binary Search Tree': 'binary-search-tree',
    'Recursion': 'recursion',
    'Brainteaser': 'brainteaser',
    'Memoization': 'memoization',
    'Queue': 'queue',
    'Minimax': 'minimax',
    'Reservoir Sampling': 'reservoir-sampling',
    'Ordered Set': 'ordered-set',
    'Monotonic Stack': 'monotonic-stack',
    'Monotonic Queue': 'monotonic-queue',
    'Combinatorics': 'combinatorics',
    'Enumeration': 'enumeration',
    'Counting': 'counting',
    'Sliding Window': 'sliding-window',
    'Geometry': 'geometry',
    'Simulation': 'simulation',
    'Prefix Sum': 'prefix-sum',
    'Hash Function': 'hash-function',
    'Rolling Hash': 'rolling-hash',
    'String Matching': 'string-matching',
    'Matrix': 'matrix',
    'Number Theory': 'number-theory',
    'Shortest Path': 'shortest-path',
    'Biconnected Component': 'biconnected-component',
    'Strongly Connected Component': 'strongly-connected-component',
    'Eulerian Circuit': 'eulerian-circuit',
    'Game Theory': 'game-theory',
    'Interactive': 'interactive',
    'Database': 'database',
    'Shell': 'shell',
    'Concurrency': 'concurrency',
    'Probability and Statistics': 'probability-statistics',
    'Suffix Array': 'suffix-array',
    'Line Sweep': 'line-sweep',
    'Data Stream': 'data-stream',
    'Doubly-Linked List': 'doubly-linked-list',
    'Radix Sort': 'radix-sort',
    'Merge Sort': 'merge-sort',
    'Quickselect': 'quickselect',
    'Bucket Sort': 'bucket-sort',
    'Counting Sort': 'counting-sort',
    
    # Codeforces topics (lowercase) -> canonical
    'dp': 'dynamic-programming',
    'graphs': 'graph',
    'trees': 'tree',
    'strings': 'string',
    'implementation': 'implementation',
    'constructive algorithms': 'constructive-algorithms',
    'number theory': 'number-theory',
    'data structures': 'data-structures',
    'sortings': 'sorting',
    'binary search': 'binary-search',
    'greedy': 'greedy',
    'brute force': 'brute-force',
    'math': 'math',
    'two pointers': 'two-pointers',
    'combinatorics': 'combinatorics',
    'geometry': 'geometry',
    'bitmasks': 'bitmask',
    'divide and conquer': 'divide-and-conquer',
    'games': 'game-theory',
    'probabilities': 'probability-statistics',
    'interactive': 'interactive',
    'hashing': 'hash-function',
    'string suffix structures': 'suffix-array',
    'dsu': 'union-find',
    'shortest paths': 'shortest-path',
    'fft': 'fft',
    'flows': 'network-flow',
    'meet-in-the-middle': 'meet-in-the-middle',
    'ternary search': 'ternary-search',
    'expression parsing': 'expression-parsing',
    'matrices': 'matrix',
    '2-sat': 'two-sat',
    'chinese remainder theorem': 'chinese-remainder-theorem',
    'schedules': 'scheduling',
}

# Topic hierarchy: child -> parent
TOPIC_HIERARCHY: Dict[str, str] = {
    'binary-search-tree': 'tree',
    'segment-tree': 'tree',
    'binary-indexed-tree': 'tree',
    'trie': 'tree',
    'dfs': 'graph',
    'bfs': 'graph',
    'shortest-path': 'graph',
    'topological-sort': 'graph',
    'network-flow': 'graph',
    'union-find': 'graph',
    'strongly-connected-component': 'graph',
    'biconnected-component': 'graph',
    'eulerian-circuit': 'graph',
    'doubly-linked-list': 'linked-list',
    'monotonic-stack': 'stack',
    'monotonic-queue': 'queue',
    'heap': 'tree',
    'merge-sort': 'sorting',
    'quickselect': 'sorting',
    'radix-sort': 'sorting',
    'bucket-sort': 'sorting',
    'counting-sort': 'sorting',
    'rolling-hash': 'hash-function',
    'memoization': 'dynamic-programming',
}

# Topic categories
TOPIC_CATEGORIES: Dict[str, str] = {
    # DSA fundamentals
    'array': 'dsa',
    'linked-list': 'dsa',
    'stack': 'dsa',
    'queue': 'dsa',
    'hash-table': 'dsa',
    'tree': 'dsa',
    'graph': 'dsa',
    'heap': 'dsa',
    'trie': 'dsa',
    
    # Algorithms
    'sorting': 'dsa',
    'binary-search': 'dsa',
    'two-pointers': 'dsa',
    'sliding-window': 'dsa',
    'dynamic-programming': 'dsa',
    'greedy': 'dsa',
    'backtracking': 'dsa',
    'recursion': 'dsa',
    'divide-and-conquer': 'dsa',
    'dfs': 'dsa',
    'bfs': 'dsa',
    
    # CP-specific
    'game-theory': 'cp',
    'number-theory': 'cp',
    'combinatorics': 'cp',
    'geometry': 'cp',
    'fft': 'cp',
    'network-flow': 'cp',
    'meet-in-the-middle': 'cp',
    'two-sat': 'cp',
    'chinese-remainder-theorem': 'cp',
    
    # System design
    'design': 'system-design',
    'database': 'system-design',
    'concurrency': 'system-design',
    'data-stream': 'system-design',
}


def normalize_topic(topic: str) -> str:
    """
    Normalize a topic name to canonical format.
    
    - Looks up in mapping first
    - Falls back to kebab-case conversion
    
    Args:
        topic: Raw topic name from any platform
        
    Returns:
        Normalized topic name (lowercase, kebab-case)
    """
    if not topic:
        return ''
    
    topic = topic.strip()
    
    # Check mapping first
    if topic in TOPIC_MAPPING:
        return TOPIC_MAPPING[topic]
    
    # Check lowercase version
    lower = topic.lower()
    if lower in TOPIC_MAPPING:
        return TOPIC_MAPPING[lower]
    
    # Convert to kebab-case
    # Replace spaces, underscores, camelCase with hyphens
    normalized = re.sub(r'([a-z])([A-Z])', r'\1-\2', topic)  # camelCase
    normalized = normalized.lower()
    normalized = re.sub(r'[\s_]+', '-', normalized)  # spaces and underscores
    normalized = re.sub(r'[^\w-]', '', normalized)  # remove special chars
    normalized = re.sub(r'-+', '-', normalized)  # collapse multiple hyphens
    normalized = normalized.strip('-')
    
    return normalized


def normalize_topics(topics: List[str]) -> List[str]:
    """
    Normalize a list of topics, removing duplicates.
    
    Args:
        topics: List of raw topic names
        
    Returns:
        List of normalized, deduplicated topic names
    """
    if not topics:
        return []
    
    normalized = []
    seen = set()
    
    for topic in topics:
        norm = normalize_topic(topic)
        if norm and norm not in seen:
            normalized.append(norm)
            seen.add(norm)
    
    return normalized


def get_topic_parent(topic: str) -> Optional[str]:
    """
    Get the parent topic for a given topic.
    
    Args:
        topic: Normalized topic name
        
    Returns:
        Parent topic name or None if no parent
    """
    return TOPIC_HIERARCHY.get(topic)


def get_topic_category(topic: str) -> str:
    """
    Get the category for a given topic.
    
    Args:
        topic: Normalized topic name
        
    Returns:
        Category name (dsa, cp, system-design, or 'other')
    """
    return TOPIC_CATEGORIES.get(topic, 'other')


def build_topic_document(name: str) -> Dict:
    """
    Build a canonical topic document.
    
    Args:
        name: Normalized topic name
        
    Returns:
        Topic document dict ready for canonical format
    """
    from .uuid_generator import generate_topic_uuid
    
    return {
        'topic_id': generate_topic_uuid(name),
        'name': name,
        'parent': get_topic_parent(name),
        'category': get_topic_category(name),
    }
