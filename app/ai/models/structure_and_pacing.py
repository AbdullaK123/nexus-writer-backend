from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class TensionPoint(BaseModel):
    """A point on the tension curve"""
    chapter: int
    tension_level: int = Field(ge=1, le=10)
    structural_role: str = Field(
        description="What role this chapter plays: setup, rising_action, midpoint, etc."
    )
    key_event: str = Field(description="Main event driving tension at this point")


class PacingPattern(BaseModel):
    """Pacing characteristics across a range of chapters"""
    chapter_range: str = Field(description="e.g., 'Chapters 1-5', 'Chapters 15-20'")
    dominant_pace: Literal["fast", "moderate", "slow", "varied"]
    action_average: float = Field(description="Average action percentage")
    dialogue_average: float
    introspection_average: float
    exposition_average: float
    description: str = Field(description="Summary of pacing in this range (1-2 sentences)")


class SceneStatistics(BaseModel):
    """Aggregate scene data"""
    total_scenes: int
    average_scenes_per_chapter: float
    scene_type_distribution: Dict[str, int] = Field(
        description="Count of each scene type: {'action': 45, 'dialogue': 32, ...}"
    )
    scene_type_percentages: Dict[str, float] = Field(
        description="Percentage of each scene type"
    )
    average_scene_length: int = Field(description="Average words per scene")
    longest_scene: Dict[str, int | str] = Field(
        description="{'chapter': 15, 'scene': 3, 'word_count': 5000, 'type': 'action'}"
    )
    shortest_scene: Dict[str, int | str]


class POVAnalysis(BaseModel):
    """Point of view distribution"""
    pov_characters: List[str] = Field(description="All POV characters used")
    pov_distribution: Dict[str, int] = Field(
        description="Scene count per POV: {'Commander Vex': 45, 'Chen': 12}"
    )
    pov_percentages: Dict[str, float]
    dominant_pov: str = Field(description="Character with most POV scenes")
    pov_switches_per_chapter: float = Field(
        description="Average POV switches within chapters"
    )
    multi_pov_story: bool = Field(description="Does story use multiple POVs?")


class EmotionalArc(BaseModel):
    """Story's emotional journey"""
    emotional_peak_chapters: List[int] = Field(
        description="Chapters with strongest emotional beats"
    )
    emotional_valley_chapters: List[int] = Field(
        description="Chapters with minimal emotional impact"
    )
    dominant_emotions: List[str] = Field(
        description="Most frequently targeted emotions across story"
    )
    emotional_range: str = Field(
        description="Breadth of emotions: narrow (1-2 emotions), moderate (3-5), wide (6+)"
    )
    emotional_progression: str = Field(
        description="How emotions evolve: e.g., 'fear → determination → hope' (2-3 sentences)"
    )
    weak_emotional_beats: List[Dict[str, int | str]] = Field(
        description="Chapters with weak emotional impact: [{'chapter': 8, 'issue': 'No strong moments'}]"
    )


class ThematicAnalysis(BaseModel):
    """Theme tracking across story"""
    recurring_themes: Dict[str, List[int]] = Field(
        description="Themes and chapters where they appear: {'redemption': [1, 5, 12, 20]}"
    )
    theme_frequencies: Dict[str, int] = Field(
        description="How often each theme appears"
    )
    primary_themes: List[str] = Field(
        description="3-5 most prominent themes"
    )
    theme_introduction: Dict[str, int] = Field(
        description="When each major theme first appears: {'redemption': 1}"
    )
    theme_resolution: Dict[str, Optional[int]] = Field(
        description="When each theme resolves (None if unresolved): {'redemption': 28}"
    )
    symbols_used: Dict[str, List[int]] = Field(
        description="Recurring symbols and where they appear: {'broken mirror': [3, 15, 29]}"
    )
    thematic_consistency: Literal["strong", "moderate", "weak"] = Field(
        description="How consistently themes are woven through story"
    )


class ShowVsTellAnalysis(BaseModel):
    """Show vs tell patterns"""
    overall_ratio: float = Field(ge=0, le=1, description="Average across all chapters")
    ratio_by_chapter: Dict[str, float] = Field(
        description="Chapter number (as string) to ratio: {'1': 0.75, '2': 0.60}"
    )
    problematic_chapters: List[Dict[str, int | float | str]] = Field(
        description="Chapters too 'telly': [{'chapter': 8, 'ratio': 0.20, 'issue': 'Heavy exposition'}]"
    )
    exemplary_chapters: List[Dict[str, int | float | str]] = Field(
        description="Chapters with great show/tell: [{'chapter': 15, 'ratio': 0.85, 'strength': 'Immersive action'}]"
    )
    trend: Literal["improving", "declining", "stable", "inconsistent"] = Field(
        description="How show/tell ratio changes across story"
    )


class StructuralAssessment(BaseModel):
    """Overall story structure evaluation"""
    story_structure: Literal["three_act", "five_act", "hero_journey", "kishotenketsu", "episodic", "non_linear", "custom"] = Field(
        description="Identified structure pattern"
    )
    act_breakdown: Dict[str, str] = Field(
        description="Acts and their chapter ranges: {'Act 1 (Setup)': 'Chapters 1-8', 'Act 2 (Confrontation)': 'Chapters 9-24'}"
    )
    key_structural_beats: Dict[str, int] = Field(
        description="Major beats and chapters: {'inciting_incident': 3, 'midpoint': 16, 'climax': 28}"
    )
    structural_balance: Literal["well_balanced", "front_heavy", "back_heavy", "uneven"] = Field(
        description="Are acts proportional?"
    )
    missing_beats: List[str] = Field(
        default_factory=list,
        description="Expected structural elements not found: ['clear midpoint', 'dark night of soul']"
    )


class PacingIssue(BaseModel):
    """A pacing problem detected"""
    issue_type: Literal["sagging_middle", "rushed_ending", "slow_start", "monotonous_pace", "exposition_dump", "uneven_tension"] = Field(
        description="Type of pacing problem"
    )
    chapters_affected: List[int]
    severity: Literal["minor", "moderate", "major"]
    description: str = Field(description="What the problem is")
    recommendation: str = Field(description="How to fix it")
    metrics: Dict[str, float] = Field(
        description="Supporting data: {'avg_tension': 3.2, 'exposition_pct': 0.65}"
    )


class PacingAndStructureAnalysis(BaseModel):
    """Complete pacing and structural analysis of the story"""
    
    # Tension tracking
    tension_curve: List[TensionPoint] = Field(
        description="Tension level at each chapter"
    )
    average_tension: float = Field(ge=1, le=10)
    tension_range: str = Field(
        description="Low and high: 'Ranges from 2 (low) to 9 (climax)'"
    )
    tension_trend: Literal["rising", "falling", "fluctuating", "flat"] = Field(
        description="Overall tension trajectory"
    )
    
    # Pacing patterns
    pacing_patterns: List[PacingPattern] = Field(
        description="Pacing characteristics across different story sections"
    )
    overall_pace: Literal["fast", "moderate", "slow", "varied"]
    pace_consistency: Literal["consistent", "variable", "erratic"] = Field(
        description="Does pacing feel intentional or chaotic?"
    )
    
    # Scene analysis
    scene_statistics: SceneStatistics
    
    # POV tracking
    pov_analysis: POVAnalysis
    
    # Emotional journey
    emotional_arc: EmotionalArc
    
    # Thematic patterns
    thematic_analysis: ThematicAnalysis
    
    # Show vs tell
    show_vs_tell: ShowVsTellAnalysis
    
    # Structure assessment
    structural_assessment: StructuralAssessment
    
    # Issue detection
    pacing_issues: List[PacingIssue] = Field(
        default_factory=list,
        description="Detected pacing problems"
    )
    
    # Statistics
    total_chapters: int
    total_estimated_words: int = Field(
        description="Sum of all scene word counts"
    )
    average_chapter_length: int
    
    # Overall assessment
    pacing_score: int = Field(
        ge=1, le=10,
        description="Overall pacing quality (1=poor, 10=excellent)"
    )
    structure_score: int = Field(
        ge=1, le=10,
        description="Overall structural quality"
    )
    
    # Summary
    pacing_summary: str = Field(
        description="2-3 sentence overview of story's pacing and rhythm"
    )
    structural_summary: str = Field(
        description="2-3 sentence overview of story's structure"
    )
    key_recommendations: List[str] = Field(
        description="Top 3-5 actionable recommendations for improving pacing/structure"
    )