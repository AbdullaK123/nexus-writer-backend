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
        description="Primary scene type: 'action' (physical conflict, movement, or stakes-driven events), 'dialogue' (conversation-driven), 'introspection' (internal thought/emotion), 'exposition' (worldbuilding, backstory, or information delivery), 'transition' (bridging between major scenes)"
    )
    location: str = Field(description="The specific place where this scene occurs, using the most precise name from the text (e.g., 'Engineering Bay, Deck 3' not 'the ship')")
    pov: str | None = Field(default=None, description="The point-of-view character whose perspective this scene is filtered through, using canonical name. None if the narration is omniscient or the POV is unclear.")
    goal: str = Field(description="What the POV character (or primary character) wants to accomplish in this scene — their immediate objective driving the scene forward")
    conflict: str = Field(description="The obstacle, opposition, or tension preventing the goal from being easily achieved — what creates dramatic friction in this scene")
    outcome: str = Field(description="The scene's result and how it changes the story state: 'success' (goal achieved), 'failure' (goal blocked), 'partial' (mixed result), or 'twist' (unexpected redirect)")
    word_count: int = Field(description="Approximate word count of this scene based on its proportion of the chapter")


class Pacing(BaseModel):
    """Chapter pacing breakdown. Percentages must sum to 100."""
    action_pct: float = Field(description="Percentage of the chapter dedicated to physical action, movement, or high-stakes conflict (0-100)")
    dialogue_pct: float = Field(description="Percentage of the chapter dedicated to conversation and verbal exchange (0-100)")
    introspection_pct: float = Field(description="Percentage of the chapter dedicated to internal thought, reflection, or emotional processing (0-100)")
    exposition_pct: float = Field(description="Percentage of the chapter dedicated to worldbuilding, backstory, explanation, or descriptive prose (0-100)")
    pace: Literal["fast", "moderate", "slow", "varied"] = Field(description="Overall chapter pace: 'fast' (rapid events, short scenes, high tension), 'moderate' (balanced rhythm), 'slow' (deliberate, reflective, character-focused), 'varied' (intentional shifts between fast and slow)")
    tension: int = Field(ge=1, le=10, description="Overall tension level of the chapter: 1-2 = calm/safe/reflective, 3-4 = low-level unease, 5-6 = mounting pressure, 7-8 = high stakes confrontation, 9-10 = peak climax or crisis")


class Theme(BaseModel):
    """A theme actively explored in this chapter."""
    theme: str = Field(description="The core thematic concept in 1-2 words (e.g., 'sacrifice', 'corrupting power', 'found family', 'identity crisis')")
    how_explored: str = Field(description="A 1-2 sentence explanation of how this chapter engages with the theme through its events, character choices, or imagery")
    symbols: list[str] = Field(default_factory=list, max_length=5, description="Concrete objects, images, or recurring motifs that represent or reinforce this theme in the chapter (e.g., ['the cracked mirror', 'the locked door', 'the wilting garden'])")


class EmotionalBeat(BaseModel):
    """A moment designed to create emotional impact on the reader."""
    moment: str = Field(description="The specific scene moment in 1-2 sentences, described concretely enough to locate in the text (e.g., 'When Vex finds the child's drawing in the wreckage')")
    emotion: str = Field(description="The primary emotion this moment is designed to evoke in the reader (e.g., 'heartbreak', 'dread', 'cathartic relief', 'righteous anger', 'bittersweet hope')")
    techniques: list[str] = Field(max_length=5, description="Craft techniques used to achieve the emotional effect (e.g., ['sensory detail', 'short staccato sentences', 'callback to Ch. 2 promise', 'silence/white space', 'contrast with preceding humor'])")
    effectiveness: Literal["strong", "moderate", "weak"] = Field(
        description="Honest assessment of craft execution: 'strong' (lands powerfully, well-crafted), 'moderate' (works but could be sharper), 'weak' (falls flat due to telling, rushed setup, or cliché)"
    )


class StructureExtraction(BaseModel):
    """Structural and craft analysis of a single chapter."""
    structural_role: Literal[
        "exposition", "inciting_incident", "rising_action",
        "climax", "falling_action", "resolution", "transition", "flashback"
    ] = Field(default="exposition", description="This chapter's function in the overall story arc: 'exposition' (establishes world/characters), 'inciting_incident' (disrupts status quo), 'rising_action' (escalates conflict), 'climax' (peak confrontation), 'falling_action' (aftermath), 'resolution' (wraps up), 'transition' (bridges major story sections), 'flashback' (reveals past events)")
    scenes: list[Scene] = Field(default_factory=list, max_length=12, description="All distinct scenes in the chapter, in narrative order")
    pacing: Pacing = Field(default_factory=lambda: Pacing(
        action_pct=0, dialogue_pct=0, introspection_pct=0, exposition_pct=0,
        pace="moderate", tension=1
    ), description="Pacing breakdown for this chapter including content distribution and tension level")
    themes: list[Theme] = Field(default_factory=list, max_length=5, description="Themes actively explored in this chapter (not just present — the chapter must engage with them through action, dialogue, or imagery)")
    emotional_beats: list[EmotionalBeat] = Field(default_factory=list, max_length=8, description="Key moments designed to create emotional impact on the reader, in order of appearance")
    show_vs_tell_ratio: float = Field(default=0.5, ge=0, le=1, description="Ratio of demonstrated/dramatized content vs. narrated/explained content: 0.0 = entirely told (narrator summarizes everything), 0.5 = balanced, 1.0 = entirely shown (all action, dialogue, and sensory detail)")

    @classmethod
    def empty(cls) -> "StructureExtraction":
        """Return a valid empty extraction for use as a fallback."""
        return cls()
