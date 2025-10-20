from bs4 import BeautifulSoup


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
    """Get novel-like preview with indent after first line"""
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
        result.append('\u00A0\u00A0\u00A0\u00A0' + line)
    
    return "\n\n".join(result)