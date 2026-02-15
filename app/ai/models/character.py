"""
Character extraction models — optimized for detecting:
- Plot holes (knowledge tracking)
- Flat arcs (emotional state + goal diffs across chapters)
"""
from pydantic import BaseModel, Field


class Character(BaseModel):
    """One entry per character present in the chapter."""
    name: str = Field(description="Canonical full name")
    is_new: bool = Field(description="True only if first appearance in the entire story")
    role: str = Field(description="Their function this chapter in 1 sentence")
    emotional_state: str = Field(description="Emotional state at chapter end")
    goals: list[str] = Field(default_factory=list, description="What they are actively trying to achieve")
    knowledge_gained: list[str] = Field(default_factory=list, description="New info learned THIS chapter only")


class CharacterExtraction(BaseModel):
    """All character data extracted from a single chapter."""
    characters: list[Character] = Field(default_factory=list)

    @classmethod
    def empty(cls) -> "CharacterExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()
