"""
Character extraction models — optimized for detecting:
- Plot holes (knowledge tracking)
- Flat arcs (emotional state + goal diffs across chapters)
"""
from pydantic import BaseModel, Field


class Character(BaseModel):
    """One entry per character present in the chapter."""
    name: str = Field(description="The character's full canonical name as established in the story, used consistently for cross-chapter tracking. Use the most complete form (e.g., 'Commander Elena Vex' not 'Vex' or 'Elena')")
    is_new: bool = Field(description="True only if this is the character's very first appearance across all chapters in the story so far. False for any character who appeared in a prior chapter, even if only briefly mentioned.")
    role: str = Field(description="The character's narrative function in this specific chapter in one sentence (e.g., 'Provides exposition about the colony's history' or 'Serves as the antagonist blocking the protagonist's escape')")
    emotional_state: str = Field(description="The character's dominant emotional state at the END of this chapter, reflecting any shifts that occurred (e.g., 'Determined but guilt-ridden after learning the truth about the experiment')")
    goals: list[str] = Field(default_factory=list, max_length=5, description="Active goals the character is pursuing in this chapter — include both stated and implicit objectives (e.g., ['Escape the station before lockdown', 'Keep the crew from discovering her identity'])")
    knowledge_gained: list[str] = Field(default_factory=list, max_length=5, description="Specific new information the character learns during THIS chapter only — facts, revelations, or discoveries not known to them before (e.g., ['The artifact is a weapon, not a beacon', 'Chen was the saboteur'])")


class CharacterExtraction(BaseModel):
    """All character data extracted from a single chapter."""
    characters: list[Character] = Field(default_factory=list, max_length=15, description="One entry per character with a meaningful presence in this chapter. Skip characters only mentioned in passing with no dialogue, action, or story impact.")

    @classmethod
    def empty(cls) -> "CharacterExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()
