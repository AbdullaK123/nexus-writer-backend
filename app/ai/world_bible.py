from typing import Dict, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.world_bible import WORLD_BIBLE_SYSTEM_PROMPT, build_world_bible_extraction_prompt
from app.ai.models.world_bible import WorldBibleExtraction
from dotenv import load_dotenv

load_dotenv()

world_bible_extraction_agent = create_agent(
    "google_genai:gemini-2.5-flash-lite",
    tools=[],
    system_prompt=WORLD_BIBLE_SYSTEM_PROMPT,
    response_format=ToolStrategy(WorldBibleExtraction),
)

async def extract_world_bible(
    story_context: str,
    world_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> WorldBibleExtraction:
    """
    Extract comprehensive world bible from story context and chapter world extractions.
    
    Aggregates all worldbuilding elements (locations, technologies, factions, 
    concepts, historical events) and performs consistency checking.
    
    Args:
        story_context: TOON-encoded accumulated story context
        world_extractions: List of world extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        WorldBibleExtraction with complete world bible
    """
    
    result = await world_bible_extraction_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_world_bible_extraction_prompt(
                    story_context,
                    world_extractions,
                    story_title,
                    total_chapters
                )
            }
        ]
    })

    return result["structured_response"]