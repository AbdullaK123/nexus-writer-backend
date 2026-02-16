from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class WorldLocation(BaseModel):
    """A place in the story world"""
    name: str = Field(description="The canonical name of this location as used in the narrative")
    location_type: str = Field(description="Category of location: 'planet', 'city', 'building', 'ship', 'station', 'continent', 'region', 'room', 'landmark', etc.")
    first_mention: int = Field(description="Chapter number where this location is first mentioned or visited")
    description: str = Field(description="Physical and atmospheric description of this location as established in the text — what it looks like, feels like, and any notable features")
    significance: str = Field(description="Why this location matters to the narrative — its role in the plot, what events happen here, or what it represents thematically")


class WorldTechnology(BaseModel):
    """A technology, device, or scientific concept"""
    name: str = Field(description="The canonical name of this technology or device as used in the narrative")
    category: str = Field(description="Functional category: 'weapon', 'transportation', 'communication', 'medical', 'AI', 'energy', 'surveillance', 'construction', 'computing', etc.")
    first_mention: int = Field(description="Chapter number where this technology is first mentioned or demonstrated")
    description: str = Field(description="How this technology works and what it does, based on details provided in the text — include operating principles if explained")
    capabilities: List[str] = Field(default=[], max_length=5, description="Specific things this technology can do, as established in the narrative (e.g., ['FTL travel up to 10 light-years', 'Translates 200+ alien languages in real-time'])")
    limitations: List[str] = Field(default=[], max_length=5, description="Established constraints, drawbacks, or failure modes (e.g., ['Requires 24-hour cooldown between jumps', 'Cannot penetrate Vorak shielding'])")


class WorldFaction(BaseModel):
    """An organization, faction, or group"""
    name: str = Field(description="The canonical name of this faction or organization as used in the narrative")
    faction_type: str = Field(description="Organizational category: 'government', 'military', 'corporation', 'rebel', 'criminal', 'religious', 'scientific', 'mercenary', 'alien', etc.")
    first_mention: int = Field(description="Chapter number where this faction is first mentioned or encountered")
    description: str = Field(description="What this faction is, its structure, and its role in the story world — how it operates and what it controls")
    goals: str = Field(description="The faction's primary objectives and motivations as revealed in the narrative (e.g., 'Seeking to monopolize FTL technology to control interstellar trade routes')")
    key_members: List[str] = Field(default=[], max_length=8, description="Canonical names of notable characters who belong to this faction, ordered by their prominence")


class WorldConcept(BaseModel):
    """Abstract worldbuilding concept"""
    name: str = Field(description="The canonical name of this concept as used in the narrative (e.g., 'The Binding', 'Void Law', 'The Communion')")
    category: str = Field(description="Type of concept: 'magic_system', 'law', 'cultural_practice', 'religion', 'philosophy', 'biological_trait', 'social_hierarchy', 'economic_system', etc.")
    first_mention: int = Field(description="Chapter number where this concept is first introduced or referenced")
    description: str = Field(description="What this concept is and how it functions within the story world, based on information provided in the text")
    rules: List[str] = Field(default=[], max_length=5, description="Specific rules, constraints, or mechanics governing this concept as established in the narrative (e.g., ['Only works within line of sight', 'Costs the user a memory', 'Cannot affect the dead'])")


class ConsistencyWarning(BaseModel):
    """Potential worldbuilding inconsistency"""
    category: Literal["location", "technology", "faction", "timeline", "rules"] = Field(
        description="Which worldbuilding domain the inconsistency falls under"
    )
    severity: Literal["minor", "moderate", "major"] = Field(
        description="Impact level: 'minor' (cosmetic or nitpick), 'moderate' (attentive readers will notice), 'major' (clearly contradicts established facts)"
    )
    description: str = Field(description="Specific explanation of the inconsistency, citing the conflicting details and the chapters where each appears")
    chapters: List[int] = Field(max_length=5, description="Chapter numbers containing the contradictory or inconsistent information")
    recommendation: str = Field(description="Actionable fix with specific chapter references (e.g., 'Update Ch. 15 to match the 3-day travel time established in Ch. 5')")


class WorldBibleExtraction(BaseModel):
    """Complete world bible for the story"""
    
    locations: List[WorldLocation] = Field(default=[], max_length=30, description="All named locations in the story world, ordered by narrative importance")
    technologies: List[WorldTechnology] = Field(default=[], max_length=20, description="All technologies, devices, and scientific concepts established in the story")
    factions: List[WorldFaction] = Field(default=[], max_length=15, description="All organizations, factions, and groups operating in the story world")
    concepts: List[WorldConcept] = Field(default=[], max_length=15, description="All abstract worldbuilding concepts: magic systems, laws, cultural practices, religions, etc.")
    
    primary_setting: str = Field(description="The main setting where the majority of the story takes place, described in 1-2 sentences")
    setting_scope: Literal["single_location", "city", "planet", "solar_system", "galaxy", "multiverse"] = Field(
        description="The geographic/spatial scale of the story world: how broadly the narrative ranges across physical space"
    )
    
    genre_elements: List[str] = Field(
        default=[],
        max_length=8,
        description="Key genre-defining worldbuilding markers present in the story (e.g., ['FTL travel', 'cybernetic augmentation', 'hard magic system', 'post-apocalyptic Earth', 'alien first contact'])"
    )
    
    consistency_warnings: List[ConsistencyWarning] = Field(default=[], max_length=15, description="Detected worldbuilding inconsistencies or contradictions across chapters, ordered by severity")
    
    world_summary: str = Field(description="A 3-5 sentence overview of the story world covering its setting, key features, governing systems, and atmosphere")
    worldbuilding_depth_score: int = Field(ge=1, le=10, description="How thoroughly the world is developed: 1-3 = minimal worldbuilding (setting is backdrop), 4-6 = moderate detail (key systems explained), 7-8 = rich and immersive, 9-10 = deeply layered with extensive internal logic")