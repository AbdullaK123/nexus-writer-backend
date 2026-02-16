from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class CharacterRelationship(BaseModel):
    """Relationship between this character and another"""
    character_name: str = Field(description="Canonical full name of the other character in this relationship")
    relationship_type: str = Field(description="The nature of the relationship using a concise label (e.g., 'mentor', 'rival', 'romantic_interest', 'sibling', 'commanding_officer', 'betrayer')")
    evolution: str = Field(description="How this relationship changed over the course of the story, noting key turning points (e.g., 'Started as reluctant allies in Ch. 3, became close friends after the escape in Ch. 12, strained by betrayal in Ch. 20')")


class CharacterBio(BaseModel):
    """Complete biography of a character"""
    
    canonical_name: str = Field(description="The character's primary full name as used most consistently in the narrative (e.g., 'Commander Elena Vex')")
    aliases: List[str] = Field(default=[], max_length=5, description="All alternate names, nicknames, titles, or codenames used to refer to this character (e.g., ['The Commander', 'Lena', 'Subject 7'])")
    
    role: Literal["protagonist", "antagonist", "supporting", "minor"] = Field(
        description="The character's overall narrative role across the full story: protagonist (drives the main plot), antagonist (primary opposition), supporting (significant but secondary), minor (limited presence)"
    )
    
    first_appearance: int = Field(description="Chapter number where this character first appears or is first mentioned")
    last_appearance: int = Field(description="Chapter number of this character's most recent appearance or mention")
    total_appearances: int = Field(description="Total number of chapters in which this character appears or is mentioned")
    
    arc_summary: str = Field(description="A 2-4 sentence summary of the character's journey, transformation, and key decisions across the entire story")
    
    character_traits: List[str] = Field(default=[], max_length=7, description="3-7 core personality traits that define how this character thinks and acts (e.g., ['fiercely loyal', 'morally pragmatic', 'emotionally guarded', 'quick-tempered'])")
    physical_description: Optional[str] = Field(default=None, description="Key physical attributes mentioned in the text — appearance, distinguishing features, injuries, or changes over time")
    background: Optional[str] = Field(default=None, description="The character's backstory as revealed in the narrative — origin, upbringing, formative experiences, and pre-story events")
    
    goals_and_motivations: Optional[str] = Field(default=None, description="What drives this character — their stated objectives and underlying psychological motivations (e.g., 'Seeks to destroy the artifact to atone for past failures')")
    internal_conflict: Optional[str] = Field(default=None, description="The character's central inner struggle or moral dilemma (e.g., 'Torn between duty to the corps and protecting the alien refugees')")
    
    key_relationships: List[CharacterRelationship] = Field(default=[], max_length=10, description="Significant relationships with other characters, ordered by narrative importance")
    
    character_growth: Optional[str] = Field(
        default=None,
        description="How the character meaningfully changed from their first appearance to their last — beliefs shifted, skills gained, relationships transformed. Null if the character remained static."
    )
    
    strengths: List[str] = Field(default=[], max_length=5, description="The character's key abilities, skills, or positive attributes that help them in the story (e.g., ['Expert pilot', 'Unshakeable composure under fire', 'Speaks three alien languages'])")
    weaknesses: List[str] = Field(default=[], max_length=5, description="The character's flaws, vulnerabilities, or limitations that create obstacles (e.g., ['Cannot trust authority figures', 'Chronic pain from old injury', 'Refuses to ask for help'])")
    
    notable_quotes: List[str] = Field(default=[], max_length=3, description="Up to 3 of the character's most memorable or defining lines of dialogue, quoted exactly as they appear in the text")


class CharacterBiosExtraction(BaseModel):
    """Complete character bios for all characters in the story"""
    
    characters: List[CharacterBio] = Field(max_length=30, description="Complete bios for every named character in the story, ordered by narrative importance (protagonists first)")
    
    total_characters: int = Field(description="Total number of distinct named characters identified across all chapters")
    major_character_names: List[str] = Field(max_length=10, description="Canonical names of characters with role 'protagonist', 'antagonist', or 'supporting' — the characters most central to the narrative")
    
    character_network_summary: str = Field(
        description="A 2-4 sentence overview of how the major characters relate to and influence each other, highlighting key alliances, rivalries, and power dynamics"
    )
    
    generated_at: datetime = Field(default_factory=datetime.now)