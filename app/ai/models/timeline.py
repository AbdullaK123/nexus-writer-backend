from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """A significant event in the story"""
    event_id: str
    name: str
    description: str
    chapter: int
    
    time_marker: str = Field(
        description="When this happens (e.g., 'Day 1', '3 weeks later')"
    )
    event_type: str = Field(
        description="Type: battle, discovery, death, arrival, revelation, etc."
    )
    location: str
    participants: List[str] = Field(default=[])
    
    plot_impact: str = Field(description="How this affects the main plot")
    
    is_flashback: bool = False
    is_flash_forward: bool = False


class TimelineGap(BaseModel):
    """A gap in the timeline that needs clarification"""
    description: str
    between_chapters: List[int]
    severity: Literal["minor", "moderate", "major"]
    recommendation: str


class TemporalInconsistency(BaseModel):
    """A contradiction in the timeline"""
    description: str
    chapters: List[int]
    severity: Literal["minor", "moderate", "major"]
    recommendation: str


class StoryTimeline(BaseModel):
    """Complete timeline of story events"""
    
    events: List[TimelineEvent] = Field(description="All major events in order")
    
    story_duration: str = Field(
        description="Total time covered (e.g., '3 weeks', '5 years')"
    )
    time_scale: Literal["minutes", "hours", "days", "weeks", "months", "years"]
    
    uses_flashbacks: bool
    uses_flash_forwards: bool
    linear_narrative: bool = Field(description="Told in chronological order?")
    
    timeline_gaps: List[TimelineGap] = Field(default=[])
    temporal_inconsistencies: List[TemporalInconsistency] = Field(default=[])
    
    timeline_clarity: Literal["crystal_clear", "mostly_clear", "somewhat_unclear", "confusing"]
    
    timeline_summary: str = Field(
        description="Overview of the story's temporal structure"
    )
    key_recommendations: List[str] = Field(
        default=[],
        description="Top recommendations for improving timeline clarity"
    )