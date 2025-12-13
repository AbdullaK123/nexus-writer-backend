from typing import Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.character import SYSTEM_PROMPT, build_character_extraction_prompt
from app.ai.models.character import CharacterExtraction
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware
from dotenv import load_dotenv

load_dotenv()

character_extraction_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools = [],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(CharacterExtraction),
    middleware=[
        AnthropicPromptCachingMiddleware(ttl="5m", min_messages_to_cache=0)
    ]
)

async def extract_characters(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> CharacterExtraction:
    
    result = await character_extraction_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_character_extraction_prompt(
                    story_context, 
                    current_chapter_content, 
                    chapter_number, 
                    chapter_title
                )
            }
        ]
    })

    return result["structured_response"]