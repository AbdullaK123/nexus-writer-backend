from typing import Any


def extract_text(content: Any) -> str:
    """Normalize AIMessage.content to a plain string.

    Some model providers (e.g. Gemini) return content as a list of
    content-block dicts instead of a single string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)