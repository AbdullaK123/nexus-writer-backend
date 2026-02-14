from typing import Dict, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.prompts.timeline import (
    STORY_TIMELINE_SYSTEM_PROMPT,
    build_story_timeline_extraction_prompt
)
from app.ai.models.timeline import StoryTimeline
from app.config.settings import app_config

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=None,
    max_retries=3,
)

story_timeline_extraction_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=STORY_TIMELINE_SYSTEM_PROMPT,
    response_format=ToolStrategy(StoryTimeline),
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