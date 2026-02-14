from typing import Dict, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.prompts.structure_and_pacing import (
    PACING_AND_STRUCTURE_SYSTEM_PROMPT,
    build_pacing_and_structure_extraction_prompt
)
from app.ai.models.structure_and_pacing import PacingAndStructureAnalysis
from app.config.settings import app_config

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=None,
    max_retries=3,
)

pacing_structure_extraction_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=PACING_AND_STRUCTURE_SYSTEM_PROMPT,
    response_format=ToolStrategy(PacingAndStructureAnalysis),
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