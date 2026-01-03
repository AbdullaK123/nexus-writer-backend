from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class WorldLocation(BaseModel):
    """A place in the story world"""
    name: str
    location_type: str = Field(description="Type: planet, city, building, ship, station, etc.")
    first_mention: int
    description: str = Field(description="Description of this location")
    significance: str = Field(description="Why this location matters")


class WorldTechnology(BaseModel):
    """A technology, device, or scientific concept"""
    name: str
    category: str = Field(description="weapon, transportation, communication, medical, AI, etc.")
    first_mention: int
    description: str = Field(description="How it works and what it does")
    capabilities: List[str] = Field(default=[])
    limitations: List[str] = Field(default=[])


class WorldFaction(BaseModel):
    """An organization, faction, or group"""
    name: str
    faction_type: str = Field(description="government, military, corporation, rebel, etc.")
    first_mention: int
    description: str = Field(description="What this faction is and what they do")
    goals: str
    key_members: List[str] = Field(default=[])


class WorldConcept(BaseModel):
    """Abstract worldbuilding concept"""
    name: str
    category: str = Field(description="magic_system, law, cultural_practice, religion, etc.")
    first_mention: int
    description: str
    rules: List[str] = Field(default=[], description="How this concept works")


class ConsistencyWarning(BaseModel):
    """Potential worldbuilding inconsistency"""
    category: Literal["location", "technology", "faction", "timeline", "rules"]
    severity: Literal["minor", "moderate", "major"]
    description: str
    chapters: List[int]
    recommendation: str


class WorldBibleExtraction(BaseModel):
    """Complete world bible for the story"""
    
    locations: List[WorldLocation] = Field(default=[])
    technologies: List[WorldTechnology] = Field(default=[])
    factions: List[WorldFaction] = Field(default=[])
    concepts: List[WorldConcept] = Field(default=[])
    
    primary_setting: str = Field(description="Main setting of the story")
    setting_scope: Literal["single_location", "city", "planet", "solar_system", "galaxy", "multiverse"]
    
    genre_elements: List[str] = Field(
        default=[],
        description="Key genre markers: FTL travel, magic, cybernetics, etc."
    )
    
    consistency_warnings: List[ConsistencyWarning] = Field(default=[])
    
    world_summary: str = Field(description="Overview of the story world")
    worldbuilding_depth_score: int = Field(ge=1, le=10)