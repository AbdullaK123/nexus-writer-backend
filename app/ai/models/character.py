from typing import Dict, List, Optional
from typing_extensions import Literal
from pydantic import BaseModel, Field
from app.ai.models.enums import EmotionalState


class CharacterMention(BaseModel):
    """A character mentioned in this chapter"""
    canonical_name: str = Field(description="Full canonical name (e.g., 'Captain Sarah Chen')")
    aliases_used: List[str] = Field(
        default_factory=list,
        description="All names/titles used in this chapter (e.g., ['Chen', 'the Captain', 'Sarah'])"
    )
    is_new_character: bool = Field(description="True if this is their first appearance in the story")
    role_in_chapter: str = Field(description="Their role/function in this chapter")
    

class CharacterAction(BaseModel):
    """Significant action taken by a character"""
    character_name: str
    action: str = Field(description="What they did")
    motivation: Optional[str] = Field(None, description="Why they did it, if clear")
    consequence: Optional[str] = Field(None, description="Immediate result of the action")


class CharacterRelationshipChange(BaseModel):
    """Change in relationship between characters"""
    character_a: str
    character_b: str
    previous_state: Optional[str] = Field(None, description="How relationship was before")
    new_state: str = Field(description="How relationship is now")
    catalyst: str = Field(description="What caused the change")


class CharacterSnapshot(BaseModel):
    """Complete state of a character at end of chapter"""
    character_name: str
    emotional_state: List[EmotionalState] = Field(description="Current emotional state(s)")
    physical_state: str = Field(description="Injuries, fatigue, condition")
    location: str = Field(description="Where they are")
    knowledge_gained: List[str] = Field(
        default_factory=list,
        description="New information learned this chapter"
    )
    goals: List[str] = Field(description="What they're trying to achieve")
    relationships: Dict[str, str] = Field(
        default_factory=dict,
        description="Key relationships and their current state"
    )


class CharacterExtraction(BaseModel):
    """All character-related information from a chapter"""
    characters_present: List[CharacterMention]
    character_actions: List[CharacterAction]
    relationship_changes: List[CharacterRelationshipChange]
    character_snapshots: List[CharacterSnapshot]
    dialogue_samples: Dict[str, List[str]] = Field(
        description="Character name -> list of their dialogue snippets (for voice consistency)"
    )

class CharacterBio(BaseModel):
    """Detailed Character Bio"""
    canonical_name: str = Field(description="The character's primary/full name.")
    aliases: List[str] = Field(
        default_factory=list,
        description="Other names or titles the character is known by."
    )
    role: Literal["protagonist", "antagonist", "supporting", "minor"] = Field(
        description="The character's role or function in the story."
    )
    first_appearance_chapter: int = Field(
        description="The chapter number where the character first appears."
    )
    last_appearance_chapter: int = Field(
        description="The chapter number where the character last appears."
    )
    chapters_present: List[int] = Field(
        default_factory=list,
        description="List of chapter numbers where the character appears."
    )
    arc_summary: str = Field(
        description="A brief summary of the character's story arc throughout the narrative."
    )
    personality_traits: List[str] = Field(
        default_factory=list,
        description="Key personality traits that define the character."
    )
    physical_description: str = Field(
        description="A description of the character's physical appearance."
    )
    background: str = Field(
        description="The character's backstory and relevant history."
    )
    motivations: List[str] = Field(
        default_factory=list,
        description="The main motivations driving the character's actions."
    )
    