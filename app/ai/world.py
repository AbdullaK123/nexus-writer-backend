from typing import Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.world import SYSTEM_PROMPT, build_world_extraction_prompt
from app.ai.models.world import WorldExtraction
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware
from dotenv import load_dotenv

load_dotenv()

world_structure_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools = [],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(WorldExtraction),
    middleware=[
        AnthropicPromptCachingMiddleware(ttl="5m")
    ]
)

async def extract_world_information(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> WorldExtraction:
    
    result = await world_structure_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_world_extraction_prompt(
                    story_context, 
                    current_chapter_content, 
                    chapter_number, 
                    chapter_title
                )
            }
        ]
    })

    return result["structured_response"]