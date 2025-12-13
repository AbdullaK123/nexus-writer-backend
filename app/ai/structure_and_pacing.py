from typing import Dict, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.structure_and_pacing import (
    PACING_AND_STRUCTURE_SYSTEM_PROMPT,
    build_pacing_and_structure_extraction_prompt
)
from app.ai.models.structure_and_pacing import PacingAndStructureAnalysis
from dotenv import load_dotenv
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware

load_dotenv()

pacing_structure_extraction_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=PACING_AND_STRUCTURE_SYSTEM_PROMPT,
    response_format=ToolStrategy(PacingAndStructureAnalysis),
    middleware=[
        AnthropicPromptCachingMiddleware(ttl="5m", min_messages_to_cache=0)
    ]
)

async def extract_pacing_and_structure(
    story_context: str,
    structure_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> PacingAndStructureAnalysis:
    """
    Extract comprehensive pacing and structural analysis from story context 
    and chapter structure extractions.
    
    Analyzes tension curves, pacing patterns, scene composition, POV distribution,
    emotional arcs, thematic consistency, show vs tell balance, and structural 
    framework to provide actionable insights for improving story pacing and structure.
    
    Args:
        story_context: TOON-encoded accumulated story context
        structure_extractions: List of structure extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        PacingAndStructureAnalysis with complete pacing and structural assessment
    """
    
    result = await pacing_structure_extraction_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_pacing_and_structure_extraction_prompt(
                    story_context,
                    structure_extractions,
                    story_title,
                    total_chapters
                )
            }
        ]
    })

    return result["structured_response"]