from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class WorldLocation(BaseModel):
    """A place in the story world"""
    name: str = Field(description="Name of the location")
    aliases: List[str] = Field(default_factory=list, description="Other names for this location")
    location_type: str = Field(
        description="Type: planet, city, building, region, ship, station, etc."
    )
    first_mention: int = Field(description="Chapter where first mentioned")
    last_mention: int = Field(description="Chapter where last mentioned")
    chapters_mentioned: List[int] = Field(description="All chapters where this location appears")
    description: str = Field(description="2-3 sentence description of this location")
    parent_location: Optional[str] = Field(
        default=None,
        description="Larger location this is part of (e.g., 'Mars' for 'Olympus City')"
    )
    sub_locations: List[str] = Field(
        default_factory=list,
        description="Smaller locations within this one"
    )
    significance: str = Field(
        description="Why this location matters to the story"
    )
    key_events: List[Dict[str, int | str]] = Field(
        default_factory=list,
        description="Important events at this location: [{'chapter': 5, 'event': 'Final battle'}]"
    )


class WorldTechnology(BaseModel):
    """A technology, device, or scientific concept"""
    name: str = Field(description="Name of the technology")
    category: str = Field(
        description="Category: weapon, transportation, communication, medical, AI, energy, etc."
    )
    first_mention: int = Field(description="Chapter where first introduced")
    description: str = Field(description="How it works and what it does (2-3 sentences)")
    capabilities: List[str] = Field(description="What this technology can do")
    limitations: List[str] = Field(description="What it cannot do or its constraints")
    users: List[str] = Field(
        default_factory=list,
        description="Characters who use this technology"
    )
    significance: str = Field(description="Role in the story")


class WorldFaction(BaseModel):
    """An organization, faction, or group"""
    name: str = Field(description="Name of the faction")
    aliases: List[str] = Field(default_factory=list, description="Other names")
    faction_type: str = Field(
        description="Type: government, military, corporation, rebel, cult, species, etc."
    )
    first_mention: int = Field(description="Chapter where first mentioned")
    description: str = Field(description="What this faction is and what they do (2-3 sentences)")
    goals: str = Field(description="What this faction wants to achieve")
    structure: Optional[str] = Field(
        default=None,
        description="How the faction is organized (if known)"
    )
    key_members: List[str] = Field(
        default_factory=list,
        description="Important characters in this faction"
    )
    relationships: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Relations with other factions: [{'faction': 'Alliance', 'relationship': 'enemy'}]"
    )
    territories: List[str] = Field(
        default_factory=list,
        description="Locations controlled by this faction"
    )


class WorldConcept(BaseModel):
    """Abstract worldbuilding concept (magic system, law, cultural practice, etc.)"""
    name: str = Field(description="Name of the concept")
    category: str = Field(
        description="Category: magic_system, law, cultural_practice, religion, economic_system, etc."
    )
    first_mention: int = Field(description="Chapter where first explained")
    description: str = Field(description="Explanation of this concept (2-3 sentences)")
    rules: List[str] = Field(
        default_factory=list,
        description="How this concept works or its governing rules"
    )
    exceptions: List[str] = Field(
        default_factory=list,
        description="Known exceptions or edge cases"
    )
    affected_characters: List[str] = Field(
        default_factory=list,
        description="Characters directly affected by this concept"
    )


class WorldHistoricalEvent(BaseModel):
    """Past event that shapes the story world"""
    name: str = Field(description="Name of the event")
    time_period: str = Field(
        description="When it happened relative to story (e.g., '100 years ago', 'The Great War')"
    )
    first_mentioned: int = Field(description="Chapter where first referenced")
    description: str = Field(description="What happened (2-3 sentences)")
    participants: List[str] = Field(
        default_factory=list,
        description="Factions, characters, or groups involved"
    )
    consequences: List[str] = Field(
        description="How this event affects the present story"
    )
    locations: List[str] = Field(
        default_factory=list,
        description="Where this event took place"
    )


class ConsistencyWarning(BaseModel):
    """Potential worldbuilding inconsistency"""
    category: str = Field(
        description="What type of inconsistency: location, technology, faction, timeline, rules"
    )
    severity: str = Field(
        description="How serious: minor, moderate, major"
    )
    description: str = Field(description="What the inconsistency is")
    chapters: List[int] = Field(description="Chapters where the inconsistency appears")
    recommendation: str = Field(description="How to fix it")


class WorldBibleExtraction(BaseModel):
    """Complete world bible for the story"""
    
    # Core worldbuilding elements
    locations: Dict[str, WorldLocation] = Field(
        description="All locations indexed by name"
    )
    technologies: Dict[str, WorldTechnology] = Field(
        default_factory=dict,
        description="All technologies indexed by name"
    )
    factions: Dict[str, WorldFaction] = Field(
        default_factory=dict,
        description="All factions indexed by name"
    )
    concepts: Dict[str, WorldConcept] = Field(
        default_factory=dict,
        description="All abstract concepts indexed by name"
    )
    historical_events: Dict[str, WorldHistoricalEvent] = Field(
        default_factory=dict,
        description="All historical events indexed by name"
    )
    
    # Statistics
    total_locations: int
    total_technologies: int
    total_factions: int
    total_concepts: int
    total_historical_events: int
    
    # Geography
    primary_setting: str = Field(
        description="The main setting of the story (e.g., 'Outer rim of the galaxy')"
    )
    setting_scope: str = Field(
        description="Scale: single_location, city, planet, solar_system, galaxy, multiverse, etc."
    )
    
    # Genre-specific
    genre_elements: List[str] = Field(
        description="Key genre markers: FTL travel, magic, cybernetics, time travel, etc."
    )
    
    # Consistency tracking
    consistency_warnings: List[ConsistencyWarning] = Field(
        default_factory=list,
        description="Potential worldbuilding inconsistencies detected"
    )
    
    # Summary
    world_summary: str = Field(
        description="2-3 sentence overview of the story world and its key features"
    )
    worldbuilding_depth_score: int = Field(
        ge=1, le=10,
        description="1-10 rating of worldbuilding detail (1=minimal, 10=encyclopedic)"
    )