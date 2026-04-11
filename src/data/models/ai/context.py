from typing import List
from pydantic import BaseModel, Field


class CondensedChapterContext(BaseModel):
    """The final condensed, context-friendly version of a chapter"""
    chapter_id: str
    
    # Temporal context
    timeline_context: str = Field(description="When this chapter takes place relative to the overall story timeline, including elapsed time and any time jumps (e.g., 'Day 5 of the expedition, two days after the ambush in Ch. 3')")
    
    # Core content (synthesized from multi-pass extractions)
    entities_summary: str = Field(description="All named entities (characters, locations, objects, organizations) mentioned in this chapter, with disambiguation for similar names and noting any new introductions")
    events_summary: str = Field(description="Key plot events in chronological sequence as they occur in this chapter, focusing on actions that change the story state")
    character_developments: str = Field(description="How each significant character's emotional state, knowledge, relationships, or goals shifted during this chapter")
    plot_progression: str = Field(description="Which active plot threads advanced, stalled, or resolved in this chapter, and what new threads were introduced")
    worldbuilding_additions: str = Field(description="New world details established in this chapter: locations, rules, technologies, cultural details, or facts not previously known")
    
    # For agents to query
    themes_present: List[str] = Field(max_length=7, description="Thematic concepts actively explored in this chapter (e.g., ['sacrifice', 'identity', 'trust'])")
    emotional_arc: str = Field(description="The emotional trajectory of the chapter from opening to close, describing the shifts in tone and mood (e.g., 'Opens with tense anticipation, peaks with the betrayal reveal, ends on quiet despair')")
    
    # Metadata
    word_count: int = Field(description="Total word count of the original chapter text")
    estimated_reading_time_minutes: int = Field(description="Estimated reading time in minutes, based on ~250 words per minute")
    
    # The actual condensed prose
    condensed_text: str = Field(
        description="A structured prose summary (max 1500 words) that preserves the chapter's key events, character actions, dialogue highlights, and emotional beats in narrative order. Written densely enough to serve as context for analyzing later chapters."
    )


class ChapterContext(BaseModel):
    chapter_id: str
    story_id: str
    chapter_number: int
    
    # Temporal context
    timeline_context: str = Field(description="When this chapter takes place relative to the overall story timeline, including elapsed time and any time jumps (e.g., 'Day 5 of the expedition, two days after the ambush in Ch. 3')")
    
    # Core content (synthesized from multi-pass extractions)
    entities_summary: str = Field(description="All named entities (characters, locations, objects, organizations) mentioned in this chapter, with disambiguation for similar names and noting any new introductions")
    events_summary: str = Field(description="Key plot events in chronological sequence as they occur in this chapter, focusing on actions that change the story state")
    character_developments: str = Field(description="How each significant character's emotional state, knowledge, relationships, or goals shifted during this chapter")
    plot_progression: str = Field(description="Which active plot threads advanced, stalled, or resolved in this chapter, and what new threads were introduced")
    worldbuilding_additions: str = Field(description="New world details established in this chapter: locations, rules, technologies, cultural details, or facts not previously known")
    
    # For agents to query
    themes_present: List[str] = Field(max_length=7, description="Thematic concepts actively explored in this chapter (e.g., ['sacrifice', 'identity', 'trust'])")
    emotional_arc: str = Field(description="The emotional trajectory of the chapter from opening to close, describing the shifts in tone and mood (e.g., 'Opens with tense anticipation, peaks with the betrayal reveal, ends on quiet despair')")
    
    # Metadata
    word_count: int = Field(description="Total word count of the original chapter text")
    estimated_reading_time_minutes: int = Field(description="Estimated reading time in minutes, based on ~250 words per minute")
    
    # The actual condensed prose
    condensed_text: str = Field(
        description="A structured prose summary (max 1500 words) that preserves the chapter's key events, character actions, dialogue highlights, and emotional beats in narrative order. Written densely enough to serve as context for analyzing later chapters."
    )