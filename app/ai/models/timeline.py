from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """A significant event in the story's timeline"""
    event_id: str = Field(description="Unique snake_case identifier for this event. Example: 'artifact_discovery', 'battle_of_ironhold'")
    name: str = Field(description="Short descriptive name for the event. Example: 'Discovery of Alien Artifact'")
    description: str = Field(description="1-2 sentence summary of what happens during this event")
    chapter: int = Field(description="Chapter number where this event occurs or is revealed")
    
    time_marker: str = Field(
        description="When this event happens, using the story's own time references. Examples: 'Day 1, morning', '3 weeks after the war', 'Year 2185', 'that evening'. If unclear, use 'unclear — sometime in Ch. X'"
    )
    event_type: str = Field(
        description="Category: battle, discovery, death, arrival, departure, revelation, decision, confrontation, reunion, betrayal, etc."
    )
    location: str = Field(description="Where this event takes place")
    participants: List[str] = Field(default=[], description="Characters directly involved (use canonical names)")
    
    plot_impact: str = Field(description="1 sentence on how this event affects the story going forward")
    
    is_flashback: bool = Field(default=False, description="True if this event is shown as a flashback (happened before the current narrative time)")
    is_flash_forward: bool = Field(default=False, description="True if this event is shown as a flash-forward (happens after the current narrative time)")


class TimelineGap(BaseModel):
    """A gap in the timeline where time passage is unclear to the reader"""
    description: str = Field(description="What is unclear. Example: 'No time markers between investigation start and the revelation — could be days or weeks'")
    between_chapters: List[int] = Field(description="The chapter numbers between which the gap occurs")
    severity: Literal["minor", "moderate", "major"] = Field(description="minor = doesn't hurt comprehension, moderate = somewhat confusing, major = reader has no idea when things happen")
    recommendation: str = Field(description="Actionable fix with specific chapter reference. Example: 'Add a time marker at the start of Ch. 9: Two weeks into the investigation...'")


class TemporalInconsistency(BaseModel):
    """A contradiction or impossibility in the story's timeline"""
    description: str = Field(description="What's inconsistent, citing specific details from each chapter. Example: 'Ch. 5 says the journey takes 3 days, but Ch. 8 shows arrival the next morning'")
    chapters: List[int] = Field(description="Chapter numbers containing the contradictory information")
    severity: Literal["minor", "moderate", "major"] = Field(description="minor = nitpick, moderate = noticeable to attentive readers, major = clearly broken logic")
    recommendation: str = Field(description="Actionable fix. Example: 'Change Ch. 8 arrival to Day 4 to match the 3-day travel time'")


class StoryTimeline(BaseModel):
    """Complete timeline analysis of a story"""
    
    events: List[TimelineEvent] = Field(description="All significant events in chronological order (story-world time, not narrative order). Include plot turning points, major character decisions, arrivals/departures, battles, revelations, and deaths. Exclude routine activities unless plot-relevant.")
    
    story_duration: str = Field(
        description="Total time span covered by the story. Examples: '3 weeks', '5 years', '48 hours'"
    )
    time_scale: Literal["minutes", "hours", "days", "weeks", "months", "years"] = Field(
        description="The primary unit of time progression in the story"
    )
    
    uses_flashbacks: bool = Field(description="True if the story shows events from before the main narrative timeline")
    uses_flash_forwards: bool = Field(description="True if the story shows events from after the current narrative point")
    linear_narrative: bool = Field(description="True if events are told in chronological order. False if the narrative jumps around in time.")
    
    timeline_gaps: List[TimelineGap] = Field(default=[], description="Places where time passage is unclear or unanchored. Only flag genuinely confusing gaps, not intentional time skips.")
    temporal_inconsistencies: List[TemporalInconsistency] = Field(default=[], description="Contradictions or impossibilities in the timeline. Must cite specific evidence from chapters.")
    
    timeline_clarity: Literal["crystal_clear", "mostly_clear", "somewhat_unclear", "confusing"] = Field(
        description="Overall assessment of how easy it is for a reader to follow when things happen"
    )
    
    timeline_summary: str = Field(
        description="2-3 sentence overview of the story's temporal structure. Example: 'The story unfolds over 3 weeks in mostly linear fashion with two flashbacks to the war. Pacing accelerates in the final week as plot threads converge.'"
    )
    key_recommendations: List[str] = Field(
        default=[],
        description="3-5 specific, actionable suggestions for improving timeline clarity. Each must reference a chapter number and propose a concrete change."
    )