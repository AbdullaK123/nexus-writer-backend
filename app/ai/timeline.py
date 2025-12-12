from typing import Dict, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.timeline import (
    STORY_TIMELINE_SYSTEM_PROMPT,
    build_story_timeline_extraction_prompt
)
from app.ai.models.timeline import StoryTimeline
from dotenv import load_dotenv

load_dotenv()

story_timeline_extraction_agent = create_agent(
    "google_genai:gemini-2.5-flash-lite",
    tools=[],
    system_prompt=STORY_TIMELINE_SYSTEM_PROMPT,
    response_format=ToolStrategy(StoryTimeline)
)

async def extract_story_timeline(
    story_context: str,
    plot_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> StoryTimeline:
    """
    Extract comprehensive timeline from story context and chapter plot extractions.
    
    Constructs chronological event ordering, identifies temporal gaps and inconsistencies,
    tracks causal relationships, and provides recommendations for improving timeline clarity.
    
    Args:
        story_context: TOON-encoded accumulated story context
        plot_extractions: List of plot extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        StoryTimeline with complete temporal analysis
    """
    
    result = await story_timeline_extraction_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_story_timeline_extraction_prompt(
                    story_context,
                    plot_extractions,
                    story_title,
                    total_chapters
                )
            }
        ]
    })

    return result["structured_response"]