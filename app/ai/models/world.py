from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class LocationMention(BaseModel):
    """A location referenced in the chapter"""
    name: str
    type: str = Field(description="planet, city, building, region, etc.")
    description: Optional[str] = Field(None, description="Physical description if provided")
    is_new: bool = Field(description="First mention in story")
    notable_features: List[str] = Field(default_factory=list)


class WorldRule(BaseModel):
    """How something works in this world"""
    rule_type: str = Field(description="magic, technology, physics, social, political, etc.")
    description: str
    limitations: List[str] = Field(default_factory=list, description="Known constraints")
    examples_in_chapter: List[str] = Field(description="How this rule was demonstrated")


class FactualClaim(BaseModel):
    """Concrete fact that could contradict later"""
    claim_type: str = Field(description="physical_description, capability, measurement, date, relationship, etc.")
    subject: str = Field(description="What/who this is about")
    claim: str = Field(description="The specific claim made")
    context: str = Field(description="Surrounding context for disambiguation")


class TimelineMarker(BaseModel):
    """Temporal reference"""
    marker_type: Literal["absolute_date", "relative_time", "duration", "sequence"]
    description: str
    reference_point: Optional[str] = Field(None, description="What this is relative to")


class CulturalElement(BaseModel):
    """Social/cultural detail"""
    element_type: str = Field(description="custom, language, taboo, tradition, etc.")
    description: str
    group: str = Field(description="Which culture/faction this belongs to")


class WorldExtraction(BaseModel):
    """All worldbuilding and continuity information"""
    locations: List[LocationMention]
    world_rules: List[WorldRule]
    factual_claims: List[FactualClaim]
    timeline_markers: List[TimelineMarker]
    cultural_elements: List[CulturalElement]
    sensory_details: Dict[str, List[str]] = Field(
        description="Sense -> list of details (sight, sound, smell, touch, taste)"
    )