from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from uuid import uuid4


# ============================================================================
# OPTIMIZED FOR: World Consistency & Rule Violations
# ============================================================================

class WorldRule(BaseModel):
    """How something works in this world - with violation tracking"""
    rule_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique rule ID")
    rule_type: str = Field(
        description="magic, technology, physics, social, political, biological, etc."
    )
    rule_statement: str = Field(description="Clear statement of the rule")
    limitations: List[str] = Field(
        default_factory=list,
        description="Known constraints and boundaries"
    )
    examples_in_chapter: List[str] = Field(
        description="How this rule was demonstrated"
    )
    consistency_level: Literal["strict", "flexible", "soft"] = Field(
        default="strict",
        description="How rigidly this rule must be followed"
    )
    established_in_chapter: int = Field(description="When this rule was first shown")
    
    # For violation detection:
    # Query: "Find chapters where rule_id X is contradicted"


class RuleViolation(BaseModel):
    """Detected violation of established world rule"""
    rule_id: str = Field(description="Which rule was violated")
    rule_statement: str = Field(description="What the rule says")
    violation_description: str = Field(description="What happened that breaks the rule")
    severity: Literal["major", "moderate", "minor", "possible_exception"]
    explanation_exists: bool = Field(
        description="Is there an in-world explanation for this?"
    )
    explanation: Optional[str] = Field(None, description="The explanation if it exists")
    
    # For consistency checking:
    # Query: "All violations with severity='major' and explanation_exists=False"


# ============================================================================
# OPTIMIZED FOR: Timeline Validation & Temporal Logic
# ============================================================================

class ChapterTimespan(BaseModel):
    """How much time passes in this chapter"""
    duration_value: Optional[float] = Field(None, description="Numeric value (e.g., 3 for '3 days')")
    duration_unit: Optional[str] = Field(
        None,
        description="minutes, hours, days, weeks, months, years"
    )
    duration_description: str = Field(description="Natural language description")
    time_certainty: Literal["exact", "approximate", "unclear"] = Field(
        description="How precise is this timespan?"
    )
    spans_multiple_days: bool = Field(description="Does this chapter cover > 1 day?")
    
    # For timeline validation:
    # Accumulate durations to track total story time


class TimelineMarker(BaseModel):
    """Temporal reference - enhanced"""
    marker_id: str = Field(default_factory=lambda: str(uuid4()))
    marker_type: Literal["absolute_date", "relative_time", "duration", "sequence", "seasonal"]
    description: str
    reference_point: Optional[str] = Field(
        None,
        description="What this is relative to (e.g., 'two days after the battle')"
    )
    
    # Precise tracking
    days_since_story_start: Optional[float] = Field(
        None,
        description="Cumulative days (for timeline visualization)"
    )
    season: Optional[str] = Field(None, description="spring, summer, fall, winter")
    time_of_day: Optional[str] = Field(None, description="morning, afternoon, evening, night")
    
    # For inconsistency detection:
    # Compare markers: "3 days passed" vs "still morning of same day"


# ============================================================================
# OPTIMIZED FOR: Injury Healing Validation
# ============================================================================

class Injury(BaseModel):
    """Physical injury to character - tracks healing realism"""
    injury_id: str = Field(default_factory=lambda: str(uuid4()))
    character_name: str
    injury_type: str = Field(
        description="broken bone, stab wound, concussion, burns, bruising, etc."
    )
    severity: int = Field(
        ge=1, le=10,
        description="1=minor scratch, 10=life-threatening"
    )
    location_on_body: str = Field(description="where on the body")
    
    # Healing tracking
    occurred_in_chapter: int
    realistic_healing_time: Optional[str] = Field(
        None,
        description="Expected healing time based on injury type (e.g., '6-8 weeks for broken leg')"
    )
    current_healing_stage: Literal["fresh", "healing", "mostly_healed", "recovered"] = Field(
        default="fresh"
    )
    affects_capabilities: List[str] = Field(
        default_factory=list,
        description="What can't they do? ['run', 'use right hand', 'see clearly']"
    )
    
    # For realism checking:
    # Query: "Injuries with severity > 7 that are 'recovered' after 1 chapter"


class TravelEvent(BaseModel):
    """Character traveling between locations - validates travel time"""
    travel_id: str = Field(default_factory=lambda: str(uuid4()))
    character_name: str
    from_location: str
    to_location: str
    
    # Travel validation
    distance_description: Optional[str] = Field(
        None,
        description="'100 miles', 'across the kingdom', 'next town over'"
    )
    time_taken: str = Field(description="'3 days', 'two weeks', 'overnight'")
    method: str = Field(description="walking, horse, ship, car, teleportation, flying, etc.")
    
    # Realism check
    plausible: bool = Field(
        description="Is this travel time realistic given distance and method?"
    )
    why_implausible: Optional[str] = Field(
        None,
        description="Explanation if plausible=False"
    )
    
    # For impossibility detection:
    # Query: "Travel events with plausible=False"


# ============================================================================
# OPTIMIZED FOR: Continuity Tracking
# ============================================================================

class LocationMention(BaseModel):
    """A location referenced in the chapter - enhanced"""
    location_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str = Field(description="planet, city, building, region, room, etc.")
    description: Optional[str] = Field(None, description="Physical description if provided")
    is_new: bool = Field(description="First mention in story")
    notable_features: List[str] = Field(default_factory=list)
    
    # Continuity tracking
    previous_description: Optional[str] = Field(
        None,
        description="Description from earlier chapters (if different)"
    )
    description_consistent: bool = Field(
        default=True,
        description="Does this match prior descriptions?"
    )


class FactualClaim(BaseModel):
    """Concrete fact that could contradict later - enhanced"""
    fact_id: str = Field(default_factory=lambda: str(uuid4()))
    claim_type: str = Field(
        description="physical_measurement, capability, historical_date, relationship, distance, etc."
    )
    subject: str = Field(description="What/who this is about")
    claim: str = Field(description="The specific claim made")
    context: str = Field(description="Surrounding context for disambiguation")
    
    # Contradiction tracking
    certainty: Literal["stated_as_fact", "character_belief", "rumor", "uncertain"]
    contradicts_fact_id: Optional[str] = Field(
        None,
        description="If this contradicts an earlier fact, link to it"
    )
    contradiction_severity: Optional[Literal["major", "minor", "retcon"]] = None
    
    # For contradiction detection:
    # Query: "Facts with contradicts_fact_id != None and severity='major'"


# ============================================================================
# OPTIMIZED FOR: Cultural/Social Consistency
# ============================================================================

class CulturalElement(BaseModel):
    """Social/cultural detail - enhanced"""
    element_id: str = Field(default_factory=lambda: str(uuid4()))
    element_type: str = Field(
        description="custom, language, taboo, tradition, social_hierarchy, law, etc."
    )
    description: str
    group: str = Field(description="Which culture/faction this belongs to")
    importance: Literal["common_knowledge", "important", "sacred", "minor_detail"]
    
    # Consistency tracking
    established_in_chapter: int
    violated_this_chapter: bool = Field(default=False)
    violation_explained: Optional[str] = Field(None, description="Why it was violated")
    
    # For cultural consistency:
    # Query: "Cultural elements violated without explanation"


# ============================================================================
# Updated Core Model
# ============================================================================

class WorldExtraction(BaseModel):
    """All worldbuilding and continuity information"""
    locations: List[LocationMention]
    world_rules: List[WorldRule]
    rule_violations: List[RuleViolation] = Field(
        default_factory=list,
        description="Detected violations of established rules"
    )
    factual_claims: List[FactualClaim]
    timeline_markers: List[TimelineMarker]
    chapter_timespan: Optional[ChapterTimespan] = Field(
        None,
        description="How much time passes in this chapter"
    )
    injuries: List[Injury] = Field(
        default_factory=list,
        description="Physical injuries occurring this chapter"
    )
    travel_events: List[TravelEvent] = Field(
        default_factory=list,
        description="Characters traveling between locations"
    )
    cultural_elements: List[CulturalElement]
    sensory_details: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Sense -> list of details (sight, sound, smell, touch, taste)"
    )


class ChapterWorldExtraction(BaseModel):
    """MongoDB document structure"""
    chapter_id: str
    story_id: str
    chapter_number: int
    locations: List[LocationMention]
    world_rules: List[WorldRule]
    rule_violations: List[RuleViolation] = Field(default_factory=list)
    factual_claims: List[FactualClaim]
    timeline_markers: List[TimelineMarker]
    chapter_timespan: Optional[ChapterTimespan] = None
    injuries: List[Injury] = Field(default_factory=list)
    travel_events: List[TravelEvent] = Field(default_factory=list)
    cultural_elements: List[CulturalElement]
    sensory_details: Dict[str, List[str]] = Field(default_factory=dict)