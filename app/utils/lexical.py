import json
from json import JSONDecodeError
from loguru import logger

# helper func to extract word count from lexical json
def get_word_count(lexical_json_string: str) -> int:

    try:
        lexical_json = json.loads(lexical_json_string)
    except JSONDecodeError as e:
        logger.error(f"Failed to parse lexical json string: \n {e}")
        return 0

    def get_text(node: dict) -> str:
        content = node.get('text', '') if node.get('type') == 'text' else ''
        for child in node.get('children', []):
            content += ' ' + get_text(child) 
        return content
    

    all_content = get_text(lexical_json['root'])

    return len(all_content.split())

# helper func to build chapter preview from lexical json
def get_preview_content(lexical_json_string: str) -> int:

    try:
        lexical_json = json.loads(lexical_json_string)
    except JSONDecodeError as e:
        logger.error(f"Failed to parse lexical json string: \n {e}")
        return ""
    
    def get_text(node: dict) -> str:
        content = node.get('text', '') if node.get('type') == 'text' else ''
        for child in node.get('children', []):
            content += ' ' + get_text(child)
        return content
    
    def get_block_content(node: dict) -> str:

        blocks = []

        node_types = {'paragraph', 'heading'}

        # if the node type is in node_types, extract the text from the text nodes within it. Otherwise search the nodes children
        if node.get('type') in node_types:
            content = get_text(node).strip()
            if content:
                blocks.append(content)
        else:
            for child in node.get('children', []):
                blocks.extend(get_block_content(child))

        return blocks
    

    blocks = get_block_content(lexical_json['root'])

    return '\n'.join(blocks)
    

