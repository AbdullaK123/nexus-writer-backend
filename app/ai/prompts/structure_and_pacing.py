from typing import List, Dict
from toon import encode


PACING_AND_STRUCTURE_SYSTEM_PROMPT = """You are a narrative structure analyst synthesizing per-chapter structure extractions into a comprehensive pacing and structural analysis for a complete story.

The output schema is provided via function definition — do NOT worry about JSON format. Focus on analytical quality.

# TENSION CURVE

Build a chapter-by-chapter tension map. Each chapter gets a tension_level (1-10) based on objective craft signals: stakes visibility, pacing speed, conflict intensity, uncertainty. A quiet character study is legitimately low tension — don't inflate. A poorly-written action scene can also be low tension if stakes are unclear.

Analyze the curve shape:
- tension_trend: "rising" (builds steadily), "falling" (diminishes), "fluctuating" (intentional peaks/valleys), "flat" (stays same — usually a problem)
- Good curves have steady rises with recovery periods after intense moments, higher at climax than at start.

# PACING PATTERNS

Group chapters into sections with similar pacing profiles. Don't create one pattern per chapter — identify 3-6 distinct phases (e.g., "Chapters 1-5: setup with moderate pace and high exposition," "Chapters 6-12: rising action with accelerating pace"). For each pattern, report average percentages for action/dialogue/introspection/exposition and characterize the dominant pace: "fast" (action 40%+), "moderate" (balanced), "slow" (introspection/exposition heavy), "varied" (intentional shifts).

Pace consistency: "consistent" (maintains rhythm), "variable" (changes with purpose), "erratic" (random shifts).

# SCENE STATISTICS

Aggregate scene data from all chapter extractions. Report total scenes, average per chapter, type distribution (action/dialogue/introspection/exposition) as both counts and percentages (must sum to 1.0), average scene length, and longest/shortest scenes with chapter references.

# POV ANALYSIS

Track which characters hold POV and how scenes distribute among them. pov_percentages must sum to 1.0. Note whether the story is single or multi-POV, and flag excessive POV switching per chapter (>3 is usually disorienting).

# EMOTIONAL ARC

Identify emotional peak and valley chapters. List dominant emotions across the story. Rate emotional_range: "narrow" (1-2 emotions), "moderate" (3-5), "wide" (6+). Write emotional_progression as a 2-3 sentence summary of the reader's emotional journey. Flag weak_emotional_beats — chapters where extraction marked beats as ineffective.

# THEMATIC ANALYSIS

Map recurring themes to the chapters where they're ACTIVELY explored (not merely mentioned). Track theme introduction and resolution chapters. Note symbols and their recurrences. Rate thematic_consistency: "strong" (woven throughout), "moderate" (sporadic), "weak" (mentioned but unexplored).

# SHOW VS TELL

Report overall_ratio and per-chapter ratios (0.0 = pure telling, 1.0 = pure showing, good prose = 0.5-0.7). Flag problematic_chapters (ratio < 0.35 with specific issue description) and exemplary_chapters (ratio > 0.75). Assess trend: "improving," "declining," "stable," "inconsistent."

# STRUCTURAL ASSESSMENT

Identify the structural framework that best fits the story (three_act, five_act, hero_journey, episodic, non_linear, etc.). Map act boundaries to chapter ranges. Identify key beats (inciting_incident, first_plot_point, midpoint, second_plot_point, climax, resolution) with chapter numbers. Flag missing beats. Assess structural_balance: "well_balanced" (acts proportional), "front_heavy" (too much setup), "back_heavy" (short setup, long ending), "uneven" (wildly disproportionate).

# PACING ISSUES

Detect specific problems with actionable recommendations:
- sagging_middle: Sustained low tension in the middle third. Cite chapter range, average tension, and dominant content type.
- rushed_ending: Climax/resolution compressed relative to buildup. Cite act percentages.
- slow_start: Inciting incident arrives too late. Cite chapter and tension levels.
- monotonous_pace: Multiple consecutive chapters with identical pacing profile. Cite tension variance.
- exposition_dump: Single chapter with exposition > 40%. Cite show/tell ratio.
- uneven_tension: Whiplash tension swings without narrative justification.

Every issue must include: chapters_affected, severity (minor/moderate/major), specific description with metrics, and an actionable recommendation referencing chapter numbers. Recommendations like "improve pacing" are not acceptable — "compress chapters 14-17 into 2 chapters" is.

# SCORES

- pacing_score (1-10): Consider tension curve shape, pace variety, issue severity, genre appropriateness.
- structure_score (1-10): Consider framework clarity, beat identification, balance, completeness.
Scores must be justified by the analysis — don't inflate.

# KEY RECOMMENDATIONS

Provide 3-5 actionable improvements prioritized by impact. Each must reference specific chapter numbers and propose a concrete change."""


def build_pacing_and_structure_extraction_prompt(
    story_context: str,
    structure_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> str:
    """
    Build the user prompt for pacing and structure analysis.
    
    Args:
        story_context: TOON-encoded accumulated story context
        structure_extractions: List of structure extraction dicts from all chapters
        story_title: Title of the story
        total_chapters: Total number of chapters analyzed
        
    Returns:
        Complete user prompt string
    """
    
    # Encode structure extractions as TOON for token efficiency
    structure_extractions_toon = encode({
        "chapters": [
            {
                "chapter_number": i + 1,
                "extraction": extraction
            }
            for i, extraction in enumerate(structure_extractions)
        ]
    })
    
    prompt = f"""Generate comprehensive pacing and structural analysis for: **{story_title}** ({total_chapters} chapters)

ACCUMULATED STORY CONTEXT:
{story_context}

STRUCTURE EXTRACTIONS BY CHAPTER:
{structure_extractions_toon}

Analyze all data above: build the tension curve, identify pacing patterns, aggregate scene and POV statistics, chart the emotional arc, assess thematic consistency, evaluate show-vs-tell balance, determine the structural framework and key beats, detect pacing issues with specific metrics, and provide 3-5 actionable recommendations referencing chapter numbers."""
    
    return prompt