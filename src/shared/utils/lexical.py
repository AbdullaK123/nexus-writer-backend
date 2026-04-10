import json
from json import JSONDecodeError
from typing import List
from loguru import logger


def get_word_count(lexical_json_string: str) -> int:
    """Get word count from Lexical editor JSON string."""
    if not lexical_json_string or lexical_json_string.strip() == "":
        return 0

    try:
        lexical_json = json.loads(lexical_json_string)
    except JSONDecodeError as e:
        logger.error(f"Failed to parse lexical json string: \n {e}")
        return 0

    def get_text(node: dict) -> str:
        content = node.get("text", "") if node.get("type") == "text" else ""
        for child in node.get("children", []):
            content += " " + get_text(child)
        return content

    all_content = get_text(lexical_json["root"])
    return len(all_content.split())


def get_preview_content(lexical_json_string: str) -> str:
    """Build chapter preview from Lexical editor JSON string."""
    if not lexical_json_string or lexical_json_string.strip() == "":
        return ""

    try:
        lexical_json = json.loads(lexical_json_string)
    except JSONDecodeError as e:
        logger.error(f"Failed to parse lexical json string: \n {e}")
        return ""

    def get_text(node: dict) -> str:
        content = node.get("text", "") if node.get("type") == "text" else ""
        for child in node.get("children", []):
            content += " " + get_text(child)
        return content

    def get_block_content(node: dict) -> List[str]:
        blocks = []
        node_types = {"paragraph", "heading"}
        if node.get("type") in node_types:
            content = get_text(node).strip()
            if content:
                blocks.append(content)
        else:
            for child in node.get("children", []):
                blocks.extend(get_block_content(child))
        return blocks

    blocks = get_block_content(lexical_json["root"])

    # Only add indent to the second block and onwards
    for i in range(1, len(blocks)):
        blocks[i] = "\u00A0\u00A0\u00A0\u00A0" + blocks[i]

    return "\n\n".join(blocks)
