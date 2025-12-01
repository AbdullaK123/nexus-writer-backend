from typing import List
from pydantic import BaseModel, Field


class CondensedChapterContext(BaseModel):
    """The final condensed, context-friendly version of a chapter"""
    chapter_id: str
    
    # Temporal context
    timeline_context: str = Field(description="When this happens in the story")
    
    # Core content (synthesized from multi-pass extractions)
    entities_summary: str = Field(description="All entities mentioned, with disambiguation")
    events_summary: str = Field(description="Key events in sequence")
    character_developments: str = Field(description="How characters changed")
    plot_progression: str = Field(description="How plot threads moved forward")
    worldbuilding_additions: str = Field(description="New world details established")
    
    # For agents to query
    themes_present: List[str]
    emotional_arc: str = Field(description="Emotional journey of the chapter")
    
    # Metadata
    word_count: int
    estimated_reading_time_minutes: int
    
    # The actual condensed prose
    condensed_text: str = Field(
        description="The 1500-word max condensed version in structured prose format"
    )