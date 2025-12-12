from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """A significant event in the story"""
    event_id: str = Field(description="Unique identifier (lowercase with underscores)")
    name: str = Field(description="Short name for this event")
    description: str = Field(description="What happened (2-3 sentences)")
    chapter: int = Field(description="Chapter where this event occurs")
    
    # Temporal information
    time_marker: str = Field(
        description="When this happens in story time (e.g., 'Day 1', '3 weeks later', 'Year 2184', 'The night of the attack')"
    )
    relative_timing: Optional[str] = Field(
        default=None,
        description="How this relates to other events (e.g., '2 days after discovery', 'simultaneous with battle')"
    )
    duration: Optional[str] = Field(
        default=None,
        description="How long this event lasted (e.g., '30 minutes', '3 days', 'instantaneous')"
    )
    
    # Event details
    event_type: str = Field(
        description="Type: battle, discovery, death, arrival, departure, revelation, betrayal, romance, decision, etc."
    )
    location: str = Field(description="Where this event takes place")
    participants: List[str] = Field(description="Characters directly involved")
    witnesses: List[str] = Field(
        default_factory=list,
        description="Characters who observed but didn't participate"
    )
    
    # Significance
    plot_impact: str = Field(
        description="How this event affects the main plot (1-2 sentences)"
    )
    character_impact: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Impact on characters: [{'character': 'Vex', 'impact': 'Loses trust in command'}]"
    )
    
    # Relationships
    caused_by: Optional[str] = Field(
        default=None,
        description="Event ID that directly caused this event"
    )
    leads_to: List[str] = Field(
        default_factory=list,
        description="Event IDs that this event directly causes"
    )
    related_plot_threads: List[str] = Field(
        default_factory=list,
        description="Plot thread IDs this event is part of"
    )
    
    # Temporal flags
    is_flashback: bool = Field(
        default=False,
        description="Is this a flashback to earlier events?"
    )
    is_flash_forward: bool = Field(
        default=False,
        description="Is this a flash-forward to future events?"
    )
    is_backstory: bool = Field(
        default=False,
        description="Is this historical backstory mentioned but not shown?"
    )


class TimelineGap(BaseModel):
    """A gap in the timeline that may need clarification"""
    gap_id: str = Field(description="Unique identifier")
    between_events: List[str] = Field(
        description="Event IDs where gap occurs (in order)"
    )
    between_chapters: List[int] = Field(
        description="Chapters where gap occurs"
    )
    estimated_duration: Optional[str] = Field(
        default=None,
        description="How much time is unaccounted for (e.g., '2 weeks', 'unknown')"
    )
    description: str = Field(
        description="What's unclear about the timing"
    )
    severity: Literal["minor", "moderate", "major"] = Field(
        description="How problematic this gap is"
    )
    recommendation: str = Field(
        description="How to clarify (e.g., 'Add time marker in Ch. 8', 'Specify passage of time')"
    )


class TemporalInconsistency(BaseModel):
    """A contradiction in the timeline"""
    inconsistency_id: str = Field(description="Unique identifier")
    inconsistency_type: Literal["duration", "sequence", "simultaneity", "date", "impossibility"] = Field(
        description="What kind of inconsistency"
    )
    description: str = Field(
        description="What contradicts what (be specific with details)"
    )
    events_involved: List[str] = Field(
        description="Event IDs that contradict each other"
    )
    chapters: List[int] = Field(
        description="Chapters where inconsistency appears"
    )
    severity: Literal["minor", "moderate", "major"]
    evidence: str = Field(
        description="Specific quotes or details showing the contradiction"
    )
    recommendation: str = Field(
        description="How to fix (be specific)"
    )


class TimelinePeriod(BaseModel):
    """A distinct period in the story's timeline"""
    period_name: str = Field(description="Name for this period (e.g., 'The Investigation', 'Week of Crisis')")
    start_event: str = Field(description="Event ID that starts this period")
    end_event: str = Field(description="Event ID that ends this period")
    chapters: List[int] = Field(description="Chapters that occur during this period")
    duration: str = Field(description="How long this period lasts")
    summary: str = Field(description="What happens during this period (2-3 sentences)")


class StoryTimeline(BaseModel):
    """Complete timeline of story events"""
    
    # All events
    events: Dict[str, TimelineEvent] = Field(
        description="All events indexed by event_id"
    )
    
    # Timeline orderings
    chronological_order: List[str] = Field(
        description="Event IDs in actual chronological story order (timeline order, not chapter order)"
    )
    narrative_order: List[str] = Field(
        description="Event IDs in order they appear in chapters (chapter order)"
    )
    
    # Temporal scope
    story_duration: str = Field(
        description="Total time the main story covers (e.g., '3 weeks', '5 years', '24 hours')"
    )
    time_scale: Literal["minutes", "hours", "days", "weeks", "months", "years", "decades", "centuries"] = Field(
        description="Primary time scale of the story"
    )
    pacing_description: str = Field(
        description="How time passes in the story (e.g., 'Real-time for 3 days', 'Compressed middle with time skips')"
    )
    
    # Time reference system
    uses_absolute_dates: bool = Field(
        description="Does the story use absolute dates (e.g., '2184-03-15') vs relative time ('Day 3')?"
    )
    calendar_system: Optional[str] = Field(
        default=None,
        description="If absolute dates used, what calendar (e.g., 'Gregorian', 'Galactic Standard', 'Year of the Empire')"
    )
    time_reference_consistency: Literal["consistent", "mixed", "unclear"] = Field(
        description="How consistently time is referenced"
    )
    
    # Narrative structure
    uses_flashbacks: bool = Field(
        description="Does the story include flashbacks?"
    )
    flashback_chapters: List[int] = Field(
        default_factory=list,
        description="Chapters containing flashbacks"
    )
    uses_flash_forwards: bool = Field(
        description="Does the story include flash-forwards?"
    )
    flash_forward_chapters: List[int] = Field(
        default_factory=list,
        description="Chapters containing flash-forwards"
    )
    parallel_timelines: bool = Field(
        description="Are there parallel/simultaneous storylines?"
    )
    linear_narrative: bool = Field(
        description="Is the narrative told in linear chronological order?"
    )
    
    # Timeline periods
    periods: List[TimelinePeriod] = Field(
        default_factory=list,
        description="Distinct periods/phases of the story"
    )
    
    # Chapter-level timestamps
    chapter_timestamps: Dict[str, str] = Field(
        description="When each chapter occurs: {'1': 'Day 1, Morning', '2': 'Day 1, Evening'}"
    )
    chapter_durations: Dict[str, str] = Field(
        description="How much time each chapter covers: {'1': '4 hours', '2': '2 hours'}"
    )
    
    # Issue detection
    timeline_gaps: List[TimelineGap] = Field(
        default_factory=list,
        description="Unclear time passages that may confuse readers"
    )
    temporal_inconsistencies: List[TemporalInconsistency] = Field(
        default_factory=list,
        description="Timeline contradictions that break continuity"
    )
    
    # Statistics
    total_events: int
    major_events: List[str] = Field(
        description="Event IDs of the most significant turning points"
    )
    events_per_chapter: Dict[str, int] = Field(
        description="Number of major events per chapter: {'1': 2, '2': 3}"
    )
    
    # Causal chains
    causal_chains: List[List[str]] = Field(
        default_factory=list,
        description="Sequences of causally-linked events: [['event_a', 'event_b', 'event_c']]"
    )
    longest_causal_chain: List[str] = Field(
        default_factory=list,
        description="The longest cause-effect chain in the story"
    )
    
    # Assessment
    timeline_clarity: Literal["crystal_clear", "mostly_clear", "somewhat_unclear", "confusing"] = Field(
        description="How easy it is to follow the timeline"
    )
    temporal_complexity: Literal["simple", "moderate", "complex", "very_complex"] = Field(
        description="How complicated the timeline structure is"
    )
    
    # Summary
    timeline_summary: str = Field(
        description="2-3 sentence overview of the story's temporal structure and flow"
    )
    key_temporal_recommendations: List[str] = Field(
        description="Top 3-5 recommendations for improving timeline clarity"
    )