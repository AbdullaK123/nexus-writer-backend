"""
Structure extraction models — optimized for detecting:
- Pacing problems (saggy middle, rushed climax, info-dumps)
- Scene construction issues (missing goal-conflict-outcome)
- Thematic consistency
- Emotional impact effectiveness
"""
from typing import Literal
from pydantic import BaseModel, Field


class Scene(BaseModel):
    """A scene within the chapter. List order = sequence."""
    type: Literal["action", "dialogue", "introspection", "exposition", "transition"] = Field(
        description="Primary scene type"
    )
    location: str = Field(description="Where the scene takes place")
    pov: str | None = Field(default=None, description="POV character, or null if omniscient")
    goal: str = Field(description="What the POV character wants in this scene")
    conflict: str = Field(description="What opposes the goal")
    outcome: str = Field(description="Result: success, failure, partial, twist")
    word_count: int = Field(description="Approximate word count of this scene")


class Pacing(BaseModel):
    """Chapter pacing breakdown. Percentages must sum to 100."""
    action_pct: float = Field(description="Percentage that is physical action/conflict")
    dialogue_pct: float = Field(description="Percentage that is conversation")
    introspection_pct: float = Field(description="Percentage that is internal thought/reflection")
    exposition_pct: float = Field(description="Percentage that is explanation/description/worldbuilding")
    pace: Literal["fast", "moderate", "slow", "varied"] = Field(description="Overall chapter pace")
    tension: int = Field(ge=1, le=10, description="1=calm/safe, 10=peak climax tension")


class Theme(BaseModel):
    """A theme actively explored in this chapter."""
    theme: str = Field(description="Core concept: grief, power, identity, betrayal, etc.")
    how_explored: str = Field(description="How the chapter engages with this theme")
    symbols: list[str] = Field(default_factory=list, description="Objects, images, or motifs representing the theme")


class EmotionalBeat(BaseModel):
    """A moment designed to create emotional impact on the reader."""
    moment: str = Field(description="The specific moment in 1-2 sentences")
    emotion: str = Field(description="Intended reader emotion: fear, joy, sadness, tension, etc.")
    techniques: list[str] = Field(description="How achieved: 'sensory details', 'short sentences', 'callback', etc.")
    effectiveness: Literal["strong", "moderate", "weak"] = Field(
        description="Honest assessment of craft execution"
    )


class StructureExtraction(BaseModel):
    """Structural and craft analysis of a single chapter."""
    structural_role: Literal[
        "exposition", "inciting_incident", "rising_action",
        "climax", "falling_action", "resolution", "transition", "flashback"
    ] = Field(description="This chapter's function in the overall story arc")
    scenes: list[Scene]
    pacing: Pacing
    themes: list[Theme] = Field(default_factory=list)
    emotional_beats: list[EmotionalBeat] = Field(default_factory=list)
    show_vs_tell_ratio: float = Field(ge=0, le=1, description="0.0=all narrated, 1.0=all demonstrated")
