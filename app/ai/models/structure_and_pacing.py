from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class TensionPoint(BaseModel):
    """A point on the tension curve"""
    chapter: int = Field(description="Chapter number this tension point corresponds to")
    tension_level: int = Field(ge=1, le=10, description="Tension intensity at this chapter: 1-2 = calm/reflective, 3-4 = low unease, 5-6 = mounting pressure, 7-8 = high-stakes confrontation, 9-10 = peak crisis or climax")
    structural_role: str = Field(
        description="This chapter's function in the story's dramatic structure (e.g., 'setup', 'rising_action', 'midpoint_reversal', 'dark_night_of_soul', 'climax', 'denouement')"
    )
    key_event: str = Field(description="The primary event driving the tension level at this point, in one sentence")


class PacingPattern(BaseModel):
    """Pacing characteristics across a range of chapters"""
    chapter_range: str = Field(description="The span of chapters analyzed in this pattern (e.g., 'Chapters 1-5', 'Chapters 15-20')")
    dominant_pace: Literal["fast", "moderate", "slow", "varied"] = Field(
        description="The overall pacing feel across this chapter range: 'fast' (rapid events, high stakes), 'moderate' (balanced), 'slow' (reflective, character-focused), 'varied' (intentional shifts)"
    )
    action_average: float = Field(description="Average percentage of content dedicated to action/conflict across chapters in this range (0-100)")
    dialogue_average: float = Field(description="Average percentage of content dedicated to dialogue/conversation across chapters in this range (0-100)")
    introspection_average: float = Field(description="Average percentage of content dedicated to internal thought/reflection across chapters in this range (0-100)")
    exposition_average: float = Field(description="Average percentage of content dedicated to explanation/worldbuilding/description across chapters in this range (0-100)")
    description: str = Field(description="A 1-2 sentence characterization of the pacing rhythm in this range, noting any notable patterns or shifts")


class SceneStatistics(BaseModel):
    """Aggregate scene data"""
    total_scenes: int = Field(description="Total number of distinct scenes identified across all chapters")
    average_scenes_per_chapter: float = Field(description="Mean number of scenes per chapter, rounded to one decimal")
    scene_type_distribution: Dict[str, int] = Field(
        description="Count of each scene type across the full story: {'action': 45, 'dialogue': 32, 'introspection': 18, 'exposition': 12, 'transition': 8}"
    )
    scene_type_percentages: Dict[str, float] = Field(
        description="Each scene type as a percentage of total scenes (values sum to ~100): {'action': 38.0, 'dialogue': 27.0, ...}"
    )
    average_scene_length: int = Field(description="Average word count per scene across the full story")
    longest_scene: Dict[str, int | str] = Field(
        description="Details of the longest scene by word count: {'chapter': 15, 'scene': 3, 'word_count': 5000, 'type': 'action'}"
    )
    shortest_scene: Dict[str, int | str] = Field(
        description="Details of the shortest scene by word count: {'chapter': 2, 'scene': 1, 'word_count': 200, 'type': 'transition'}"
    )


class POVAnalysis(BaseModel):
    """Point of view distribution"""
    pov_characters: List[str] = Field(max_length=10, description="All characters used as point-of-view narrators, using canonical names")
    pov_distribution: Dict[str, int] = Field(
        description="Number of scenes narrated from each POV character's perspective: {'Commander Vex': 45, 'Chen': 12, 'Dr. Okafor': 8}"
    )
    pov_percentages: Dict[str, float] = Field(
        description="Each POV character's share of total scenes as a percentage (values sum to ~100): {'Commander Vex': 60.0, 'Chen': 25.0, ...}"
    )
    dominant_pov: str = Field(description="Canonical name of the character with the most POV scenes")
    pov_switches_per_chapter: float = Field(
        description="Average number of times the POV shifts between characters within a single chapter. 0 means single-POV chapters throughout."
    )
    multi_pov_story: bool = Field(description="True if the story uses two or more POV characters. False for single-narrator stories.")


class EmotionalArc(BaseModel):
    """Story's emotional journey"""
    emotional_peak_chapters: List[int] = Field(
        max_length=10,
        description="Chapter numbers containing the most powerful emotional moments — scenes that hit hardest"
    )
    emotional_valley_chapters: List[int] = Field(
        max_length=10,
        description="Chapter numbers with the weakest emotional resonance — chapters that feel flat or emotionally inert"
    )
    dominant_emotions: List[str] = Field(
        max_length=5,
        description="The 3-5 emotions most frequently evoked across the full story (e.g., ['dread', 'determination', 'grief', 'hope'])"
    )
    emotional_range: str = Field(
        description="Breadth of emotions explored: 'narrow' (1-2 recurring emotions), 'moderate' (3-5 distinct emotions), 'wide' (6+ varied emotional registers)"
    )
    emotional_progression: str = Field(
        description="How the story's emotional landscape evolves from beginning to end in 2-3 sentences (e.g., 'Opens with wonder and curiosity, shifts to paranoia and dread at midpoint, resolves into bittersweet acceptance')"
    )
    weak_emotional_beats: List[Dict[str, int | str]] = Field(
        max_length=10,
        description="Chapters where emotional beats fell flat, with specific issue: [{'chapter': 8, 'issue': 'Major character death lands without weight due to minimal prior development'}]"
    )


class ThematicAnalysis(BaseModel):
    """Theme tracking across story"""
    recurring_themes: Dict[str, List[int]] = Field(
        description="Each theme mapped to the chapters where it is actively explored (not just mentioned): {'redemption': [1, 5, 12, 20], 'corrupting power': [3, 8, 15, 22]}"
    )
    theme_frequencies: Dict[str, int] = Field(
        description="Number of chapters each theme appears in: {'redemption': 4, 'corrupting power': 4, 'found family': 6}"
    )
    primary_themes: List[str] = Field(
        max_length=5,
        description="The 3-5 most prominent themes by frequency and narrative weight, ordered by importance"
    )
    theme_introduction: Dict[str, int] = Field(
        description="Chapter number where each major theme is first meaningfully explored: {'redemption': 1, 'corrupting power': 3}"
    )
    theme_resolution: Dict[str, Optional[int]] = Field(
        description="Chapter number where each theme reaches its final statement or resolution. None if the theme remains open: {'redemption': 28, 'corrupting power': None}"
    )
    symbols_used: Dict[str, List[int]] = Field(
        description="Recurring symbolic objects, images, or motifs and the chapters where they appear: {'broken mirror': [3, 15, 29], 'the locked door': [1, 8, 25]}"
    )
    thematic_consistency: Literal["strong", "moderate", "weak"] = Field(
        description="How consistently themes are woven through the narrative: 'strong' (themes reinforce each other and recur naturally), 'moderate' (themes present but unevenly developed), 'weak' (themes appear sporadically or feel disconnected)"
    )


class ShowVsTellAnalysis(BaseModel):
    """Show vs tell patterns"""
    overall_ratio: float = Field(ge=0, le=1, description="Average show-vs-tell ratio across all chapters: 0.0 = entirely told/narrated, 0.5 = balanced, 1.0 = entirely shown/dramatized")
    ratio_by_chapter: Dict[str, float] = Field(
        description="Show-vs-tell ratio for each chapter (chapter number as string key): {'1': 0.75, '2': 0.60, '3': 0.45}"
    )
    problematic_chapters: List[Dict[str, int | float | str]] = Field(
        max_length=10,
        description="Chapters with excessively 'telly' writing (ratio below ~0.35): [{'chapter': 8, 'ratio': 0.20, 'issue': 'Heavy exposition dump explaining faction history'}]"
    )
    exemplary_chapters: List[Dict[str, int | float | str]] = Field(
        max_length=10,
        description="Chapters with strong showing (ratio above ~0.75): [{'chapter': 15, 'ratio': 0.85, 'strength': 'Character emotions conveyed entirely through action and dialogue'}]"
    )
    trend: Literal["improving", "declining", "stable", "inconsistent"] = Field(
        description="How the show-vs-tell ratio changes over the course of the story: 'improving' (getting more dramatized), 'declining' (getting more narrated), 'stable' (consistent), 'inconsistent' (no clear pattern)"
    )


class StructuralAssessment(BaseModel):
    """Overall story structure evaluation"""
    story_structure: Literal["three_act", "five_act", "hero_journey", "kishotenketsu", "episodic", "non_linear", "custom"] = Field(
        description="The dominant structural pattern identified: 'three_act' (setup/confrontation/resolution), 'five_act' (exposition/rising/climax/falling/denouement), 'hero_journey' (Campbell monomyth), 'kishotenketsu' (introduction/development/twist/conclusion), 'episodic' (loosely connected episodes), 'non_linear' (fragmented timeline), 'custom' (doesn't match standard patterns)"
    )
    act_breakdown: Dict[str, str] = Field(
        description="Each structural act mapped to its chapter range: {'Act 1 (Setup)': 'Chapters 1-8', 'Act 2 (Confrontation)': 'Chapters 9-24', 'Act 3 (Resolution)': 'Chapters 25-30'}"
    )
    key_structural_beats: Dict[str, int] = Field(
        description="Major narrative turning points mapped to their chapter numbers: {'inciting_incident': 3, 'first_pinch_point': 8, 'midpoint': 16, 'dark_moment': 22, 'climax': 28, 'resolution': 30}"
    )
    structural_balance: Literal["well_balanced", "front_heavy", "back_heavy", "uneven"] = Field(
        description="Whether the acts are proportionally balanced: 'well_balanced' (acts feel properly weighted), 'front_heavy' (too much setup), 'back_heavy' (rushed beginning, drawn-out ending), 'uneven' (inconsistent proportions)"
    )
    missing_beats: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="Expected structural elements for the identified story structure that were not found or were undercooked: ['clear midpoint reversal', 'dark night of the soul', 'satisfying denouement']"
    )


class PacingIssue(BaseModel):
    """A pacing problem detected"""
    issue_type: Literal["sagging_middle", "rushed_ending", "slow_start", "monotonous_pace", "exposition_dump", "uneven_tension"] = Field(
        description="Category of pacing problem: 'sagging_middle' (tension drops in the middle act), 'rushed_ending' (resolution feels compressed), 'slow_start' (takes too long to engage), 'monotonous_pace' (same rhythm for too many chapters), 'exposition_dump' (large blocks of information delivery), 'uneven_tension' (jarring shifts in tension level)"
    )
    chapters_affected: List[int] = Field(max_length=15, description="Chapter numbers where this pacing problem is present")
    severity: Literal["minor", "moderate", "major"] = Field(
        description="Impact on reader experience: 'minor' (slightly noticeable), 'moderate' (most readers will feel it), 'major' (significantly damages engagement)"
    )
    description: str = Field(description="Specific explanation of the pacing problem, referencing chapter content and metrics (e.g., 'Chapters 12-16 maintain tension at 3-4 with no escalation, creating a sense of stagnation after the midpoint crisis')")
    recommendation: str = Field(description="Actionable fix with chapter references (e.g., 'Introduce a subplot reversal in Ch. 14 and raise tension to 6+ by Ch. 15 to bridge the midpoint to the climax')")
    metrics: Dict[str, float] = Field(
        description="Quantitative data supporting this diagnosis: {'avg_tension': 3.2, 'exposition_pct': 0.65, 'chapter_count': 5}"
    )


class PacingAndStructureAnalysis(BaseModel):
    """Complete pacing and structural analysis of the story"""
    
    # Tension tracking
    tension_curve: List[TensionPoint] = Field(
        max_length=50,
        description="One entry per chapter mapping the story's tension trajectory from start to finish"
    )
    average_tension: float = Field(ge=1, le=10, description="Mean tension level across all chapters (1-10 scale)")
    tension_range: str = Field(
        description="The span between lowest and highest tension values with context: 'Ranges from 2 (quiet setup in Ch. 1) to 9 (climactic battle in Ch. 28)'"
    )
    tension_trend: Literal["rising", "falling", "fluctuating", "flat"] = Field(
        description="Overall tension trajectory across the story: 'rising' (builds steadily), 'falling' (front-loaded intensity), 'fluctuating' (peaks and valleys), 'flat' (minimal variation)"
    )
    
    # Pacing patterns
    pacing_patterns: List[PacingPattern] = Field(
        max_length=6,
        description="Pacing analysis broken into logical story sections (typically 3-6 ranges covering the full chapter span)"
    )
    overall_pace: Literal["fast", "moderate", "slow", "varied"] = Field(
        description="The dominant pacing feel across the entire story"
    )
    pace_consistency: Literal["consistent", "variable", "erratic"] = Field(
        description="Whether pacing shifts feel intentional and controlled: 'consistent' (steady rhythm), 'variable' (deliberate shifts for effect), 'erratic' (jarring or uncontrolled pace changes)"
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
        max_length=10,
        description="All detected pacing and rhythm problems, ordered by severity (major first)"
    )
    
    # Statistics
    total_chapters: int = Field(description="Total number of chapters analyzed")
    total_estimated_words: int = Field(
        description="Estimated total word count of the story, summed from all scene word counts"
    )
    average_chapter_length: int = Field(description="Mean word count per chapter")
    
    # Overall assessment
    pacing_score: int = Field(
        ge=1, le=10,
        description="Overall pacing quality: 1-3 = significant pacing problems, 4-6 = functional but uneven, 7-8 = well-paced with minor issues, 9-10 = masterful rhythm and flow"
    )
    structure_score: int = Field(
        ge=1, le=10,
        description="Overall structural quality: 1-3 = missing key beats or structurally confused, 4-6 = recognizable structure with weaknesses, 7-8 = solid architecture, 9-10 = expertly constructed"
    )
    
    # Summary
    pacing_summary: str = Field(
        description="A 2-3 sentence overview of the story's pacing and rhythm, noting strengths and weaknesses"
    )
    structural_summary: str = Field(
        description="A 2-3 sentence overview of the story's structural architecture, identifying the pattern used and how well it serves the narrative"
    )
    key_recommendations: List[str] = Field(
        max_length=5,
        description="The 3-5 most impactful actionable suggestions for improving pacing and structure, each referencing specific chapters"
    )