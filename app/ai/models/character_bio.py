from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class CharacterRelationship(BaseModel):
    """Relationship between this character and another"""
    character_name: str
    relationship_type: str = Field(description="e.g., 'mentor', 'rival', 'romantic_interest'")
    evolution: str = Field(description="How the relationship changed")


class CharacterBio(BaseModel):
    """Complete biography of a character"""
    
    canonical_name: str = Field(description="Character's primary name")
    aliases: List[str] = Field(default=[], description="Nicknames, titles")
    
    role: Literal["protagonist", "antagonist", "supporting", "minor"]
    
    first_appearance: int
    last_appearance: int
    total_appearances: int
    
    arc_summary: str = Field(description="Character's journey and transformation")
    
    character_traits: List[str] = Field(default=[], description="Core personality traits")
    physical_description: Optional[str] = None
    background: Optional[str] = None
    
    goals_and_motivations: Optional[str] = None
    internal_conflict: Optional[str] = None
    
    key_relationships: List[CharacterRelationship] = Field(default=[])
    
    character_growth: Optional[str] = Field(
        default=None,
        description="How the character changed from beginning to end"
    )
    
    strengths: List[str] = Field(default=[])
    weaknesses: List[str] = Field(default=[])
    
    notable_quotes: List[str] = Field(default=[], description="Max 3 memorable quotes")


class CharacterBiosExtraction(BaseModel):
    """Complete character bios for all characters in the story"""
    
    characters: List[CharacterBio] = Field(description="All character bios")
    
    total_characters: int
    major_character_names: List[str] = Field(description="Names of major characters")
    
    character_network_summary: str = Field(
        description="Overview of how characters interact and relate"
    )
    
    generated_at: datetime = Field(default_factory=datetime.now)