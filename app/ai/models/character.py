from typing import List, Optional
from pydantic import BaseModel, Field
from app.ai.models.enums import EmotionalState


class CharacterMention(BaseModel):
    """A character mentioned in this chapter"""
    canonical_name: str = Field(description="Full name (e.g., 'Captain Sarah Chen')")
    aliases_used: List[str] = Field(default=[], description="Names/titles used this chapter")
    is_new_character: bool = Field(description="First appearance in story?")
    role_in_chapter: str = Field(description="Their role/function this chapter")
    

class CharacterAction(BaseModel):
    """Significant action taken by a character"""
    character_name: str
    action: str = Field(description="What they did")
    consequence: Optional[str] = None


class CharacterSnapshot(BaseModel):
    """Complete state of a character at end of chapter"""
    character_name: str
    emotional_state: List[EmotionalState] = Field(description="Current emotions")
    physical_state: str = Field(description="Injuries, fatigue, condition")
    location: str
    goals: List[str] = Field(default=[], description="What they're trying to achieve")


class CharacterExtraction(BaseModel):
    """All character-related information from a chapter"""
    characters_present: List[CharacterMention]
    character_actions: List[CharacterAction]
    character_snapshots: List[CharacterSnapshot]
    dialogue_samples: List[str] = Field(
        default=[],
        description="Notable dialogue snippets for voice consistency"
    )