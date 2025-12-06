# app/utils/html.py

from bs4 import BeautifulSoup
from typing import List


def get_word_count(html: str) -> int:
    """Get word count from TipTap Editor"""
    if not html or html.strip() == "":
        return 0
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style tags
    for script in soup(["script", "style"]):
        script.decompose()
    
    plain_text = soup.get_text()
    
    # Clean whitespace and count
    words = plain_text.split()
    return len(words)


def get_preview_content(html: str) -> str:
    """
    Get novel-like preview with indent after first line.
    
    USE FOR: Display previews in UI
    DON'T USE FOR: AI processing (use html_to_plain_text instead)
    """
    if not html or html.strip() == "":
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script and style tags
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Add newlines after block elements before getting text
    block_elements = [
        'p', 'div', 'br',  # Basic blocks
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # Headings
        'blockquote', 'pre',  # Quotes and code
        'ul', 'ol', 'li',  # Lists
        'table', 'tr', 'td', 'th',  # Tables
        'article', 'section', 'header', 'footer', 'nav', 'aside',  # Semantic HTML5
        'hr',  # Horizontal rule
        'address', 'figure', 'figcaption',  # Other blocks
    ]
    
    for element in soup.find_all(block_elements):
        element.append('\n')
    
    plain_text = soup.get_text()
    
    # Clean lines and indent after first
    lines = [line.strip() for line in plain_text.splitlines() if line.strip()]
    
    if not lines:
        return ""
    
    # First line stays normal, rest get indented
    result = [lines[0]]
    for line in lines[1:]:
        result.append('\u00A0\u00A0\u00A0\u00A0' + line)  # Indentation for display
    
    return "\n\n".join(result)


def html_to_plain_text(html: str) -> str:
    """
    Convert TipTap HTML to clean plain text for AI processing.
    
    Preserves paragraph structure without formatting.
    
    USE FOR: Extraction jobs, line edits, AI analysis
    DON'T USE FOR: Display (use get_preview_content instead)
    
    Args:
        html: TipTap HTML content
    
    Returns:
        Clean plain text with paragraphs separated by double newlines
    
    Example:
        Input: '<p>First para</p><p>Second para</p>'
        Output: 'First para\\n\\nSecond para'
    """
    if not html or html.strip() == "":
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style tags
    for script in soup(["script", "style"]):
        script.decompose()
    
    paragraphs = []
    
    # TipTap uses <p> tags for paragraphs
    for p_tag in soup.find_all('p'):
        # Get text, preserve spaces between inline elements
        text = p_tag.get_text(separator=' ', strip=True)
        
        # Only add non-empty paragraphs
        if text:
            paragraphs.append(text)
    
    # Join with double newlines to preserve paragraph structure
    return '\n\n'.join(paragraphs)


def html_to_paragraphs(html: str) -> List[str]:
    """
    Convert TipTap HTML to list of paragraphs.
    
    USE FOR: Line edits (need paragraph indices)
    
    Args:
        html: TipTap HTML content
    
    Returns:
        List of plain text paragraphs
    
    Example:
        Input: '<p>First para</p><p>Second para</p>'
        Output: ['First para', 'Second para']
    """
    if not html or html.strip() == "":
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style tags
    for script in soup(["script", "style"]):
        script.decompose()
    
    paragraphs = []
    
    # TipTap uses <p> tags for paragraphs
    for p_tag in soup.find_all('p'):
        # Get text, preserve spaces between inline elements
        text = p_tag.get_text(separator=' ', strip=True)
        
        # Only add non-empty paragraphs
        if text:
            paragraphs.append(text)
    
    return paragraphs