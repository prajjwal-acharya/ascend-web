"""
HTML Stripper Utility

Converts HTML content to clean markdown/plain text.
Used for stripping HTML from LeetCode problem descriptions.
"""

import re
from html import unescape
from typing import Optional


def strip_html(html_content: str) -> str:
    """
    Remove all HTML tags and return plain text.
    
    Args:
        html_content: HTML string to strip
        
    Returns:
        Plain text with HTML tags removed
    """
    if not html_content:
        return ""
    
    # Decode HTML entities first
    text = unescape(html_content)
    
    # Remove script and style blocks entirely
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Preserve code blocks - convert <pre><code> to markdown
    text = re.sub(r'<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    
    # Convert common block elements to newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 consecutive newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Collapse horizontal whitespace
    text = text.strip()
    
    return text


def html_to_markdown(html_content: str) -> str:
    """
    Convert HTML to markdown format, preserving structure.
    
    Args:
        html_content: HTML string to convert
        
    Returns:
        Markdown-formatted string
    """
    if not html_content:
        return ""
    
    # Decode HTML entities
    text = unescape(html_content)
    
    # Remove script and style blocks
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert headings
    for i in range(6, 0, -1):
        text = re.sub(
            rf'<h{i}[^>]*>(.*?)</h{i}>',
            r'\n' + '#' * i + r' \1\n',
            text,
            flags=re.DOTALL | re.IGNORECASE
        )
    
    # Convert emphasis
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert code blocks
    text = re.sub(r'<pre[^>]*>\s*<code[^>]*>(.*?)</code>\s*</pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    
    # Convert lists
    text = re.sub(r'<ul[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</ul>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<ol[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</ol>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert links
    text = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert images to markdown format
    text = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)', text, flags=re.IGNORECASE)
    
    # Convert line breaks and paragraphs
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '', text, flags=re.IGNORECASE)
    
    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    return text


def extract_examples(html_content: str) -> list:
    """
    Extract structured examples from problem HTML.
    
    Args:
        html_content: HTML content containing examples
        
    Returns:
        List of example dicts with 'input', 'output', 'explanation' keys
    """
    examples = []
    
    if not html_content:
        return examples
    
    # Pattern for LeetCode examples (usually in <pre> or <strong>Example</strong> sections)
    example_pattern = re.compile(
        r'(?:<strong>)?Example\s*\d*:?(?:</strong>)?\s*'
        r'(?:<pre>)?\s*'
        r'(?:<strong>)?Input:?(?:</strong>)?\s*(.*?)\s*'
        r'(?:<strong>)?Output:?(?:</strong>)?\s*(.*?)\s*'
        r'(?:(?:<strong>)?Explanation:?(?:</strong>)?\s*(.*?))?'
        r'(?:</pre>|(?=<strong>Example)|$)',
        re.DOTALL | re.IGNORECASE
    )
    
    matches = example_pattern.findall(html_content)
    
    for match in matches:
        example = {
            'input': strip_html(match[0]).strip(),
            'output': strip_html(match[1]).strip(),
        }
        if len(match) > 2 and match[2]:
            example['explanation'] = strip_html(match[2]).strip()
        examples.append(example)
    
    return examples


def extract_constraints(html_content: str) -> list:
    """
    Extract constraints from problem HTML.
    
    Args:
        html_content: HTML content containing constraints
        
    Returns:
        List of constraint strings
    """
    constraints = []
    
    if not html_content:
        return constraints
    
    # Look for Constraints section
    constraint_section = re.search(
        r'(?:<strong>)?Constraints:?(?:</strong>)?(.+?)(?:<strong>|$)',
        html_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if constraint_section:
        section_text = constraint_section.group(1)
        # Extract list items
        items = re.findall(r'<li[^>]*>(.*?)</li>', section_text, re.DOTALL | re.IGNORECASE)
        for item in items:
            clean = strip_html(item).strip()
            if clean:
                constraints.append(clean)
    
    return constraints
