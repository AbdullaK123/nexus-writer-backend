from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.ai.models.enums import SceneType, StructuralRole


class Scene(BaseModel):
    """A scene within the chapter"""
    scene_number: int
    scene_type: SceneType
    location: str
    characters_present: List[str]
    pov_character: Optional[str] = Field(None)
    goal: str = Field(description="What the POV character wants in this scene")
    conflict: str = Field(description="What opposes the goal")
    outcome: str = Field(description="Did they achieve the goal? What changed?")
    estimated_word_count: int


class PacingAnalysis(BaseModel):
    """Chapter pacing breakdown"""
    action_percentage: float = Field(description="Percentage of chapter that's action")
    dialogue_percentage: float
    introspection_percentage: float
    exposition_percentage: float
    overall_pace: Literal["fast", "moderate", "slow", "varied"]
    tension_level: int = Field(ge=1, le=10, description="1=low tension, 10=maximum tension")


class ThematicElement(BaseModel):
    """Theme explored in chapter"""
    theme: str = Field(description="grief, redemption, power, identity, etc.")
    how_explored: str = Field(description="How this theme was expressed")
    symbols_used: List[str] = Field(default_factory=list)


class EmotionalBeat(BaseModel):
    """Intended emotional impact moment"""
    moment: str = Field(description="The emotional moment")
    intended_emotion: str = Field(description="What reader should feel")
    techniques_used: List[str] = Field(description="How it was achieved")
    effectiveness: Literal["strong", "moderate", "weak"]


class StructureExtraction(BaseModel):
    """All structure and thematic information"""
    structural_role: StructuralRole
    scenes: List[Scene]
    pacing: PacingAnalysis
    themes: List[ThematicElement]
    emotional_beats: List[EmotionalBeat]
    show_vs_tell_ratio: float = Field(
        ge=0, le=1,
        description="0=all tell, 1=all show"
    )