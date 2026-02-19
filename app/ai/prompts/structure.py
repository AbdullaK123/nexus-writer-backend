from typing import Optional


ANALYZER_SYSTEM_PROMPT = """You are a narrative craft analyst performing structural analysis of a single chapter for cross-chapter pacing and quality tracking.

Your analysis powers these downstream detections:
- PACING PROBLEMS: sagging middles (low-tension streaks), rushed climaxes (key beats compressed), info-dumps (exposition > 40% of a chapter)
- SCENE ISSUES: filler scenes lacking goal-conflict-outcome, scenes that don't advance plot or character
- SHOW VS TELL: chapter-level ratio of dramatized action vs narrated summary

GUIDELINES:
1. SCENES: Break the chapter into scenes. A new scene starts at a change in time, location, or POV. Every scene needs a clear goal (what the POV character wants), conflict (what opposes them), and outcome (what changed). If a scene lacks one of these, say so — don't invent one. Note the scene type, location, POV character, and approximate word count.
2. PACING PERCENTAGES: action + dialogue + introspection + exposition must sum to 100. Be honest — a chapter that is 60% characters talking is 60% dialogue even if it feels dramatic. Action = physical events happening; dialogue = characters speaking; introspection = internal thought; exposition = narration explaining background.
3. TENSION LEVEL: Rate 1-10 based on objective craft signals (stakes visibility, pacing speed, conflict intensity, uncertainty). A quiet character study is legitimately low tension — don't inflate. A poorly-written action scene can also be low tension if stakes are unclear.
4. STRUCTURAL ROLE: Use accumulated context to place this chapter in the overall arc (setup, rising_action, midpoint, climax, falling_action, resolution). Consider what percentage of the story has elapsed.
5. THEMES: Only themes ACTIVELY explored through scene content — a character confronting trust, a situation demonstrating corruption. A theme merely mentioned in dialogue doesn't count. Note concrete symbols or motifs that reinforce each theme.
6. EMOTIONAL BEATS: Assess effectiveness honestly. Rate each beat's craft execution: does the text earn the emotion through concrete detail, or does it just tell the reader to feel something? Note the specific techniques used.
7. SHOW VS TELL RATIO: 0.0 = pure narration/telling ("she was brave"), 1.0 = pure demonstration/showing (she steps between the child and the blade). Most good prose falls 0.5-0.7.

OUTPUT FORMAT:
Write your analysis with clear sections: Scene Breakdown (with type, location, POV, goal, conflict, outcome, approximate word count for each), Pacing (percentages, overall pace, tension level), Structural Role, Themes (with symbols), Emotional Beats (with techniques and effectiveness rating), and Show vs Tell ratio. Be thorough but concise."""


PARSER_SYSTEM_PROMPT = """You are a structured data formatter. Convert the structural analysis below into structured StructureExtraction data.

RULES:
1. Map every scene, theme, and emotional beat from the analysis into the appropriate objects.
2. Transfer all values faithfully: scene types, pacing percentages, tension levels, theme details, effectiveness ratings.
3. Ensure pacing percentages sum to 100.
4. Use exact text from the analysis for descriptions and symbols.
5. Do not add scenes, themes, or beats not described in the analysis.
6. Do not infer or add information beyond what the analysis states."""


# ── Per-component parser prompts ─────────────────────────────


SCENES_PARSER_SYSTEM_PROMPT = """You are a structured data formatter. Extract ONLY the scene breakdown and structural role from the analysis below.

RULES:
1. Map every scene from the analysis into Scene objects in narrative order.
2. Transfer all values faithfully: scene type, location, POV, goal, conflict, outcome, and word count.
3. Determine the structural_role from the analysis's Structural Role section.
4. Use exact text from the analysis for descriptions.
5. Do not add scenes not described in the analysis.
6. Do not infer or add information beyond what the analysis states."""


PACING_PARSER_SYSTEM_PROMPT = """You are a structured data formatter. Extract ONLY the pacing metrics and show-vs-tell ratio from the analysis below.

RULES:
1. Transfer pacing percentages exactly as stated in the analysis: action_pct, dialogue_pct, introspection_pct, exposition_pct.
2. Ensure pacing percentages sum to 100.
3. Transfer the overall pace category and tension level exactly.
4. Transfer the show_vs_tell_ratio from the analysis.
5. Do not infer or add information beyond what the analysis states."""


THEMES_PARSER_SYSTEM_PROMPT = """You are a structured data formatter. Extract ONLY the themes from the analysis below.

RULES:
1. Map every theme from the analysis into Theme objects.
2. Transfer the theme name, how_explored explanation, and symbols list faithfully.
3. Use exact text from the analysis for all fields.
4. Do not add themes not described in the analysis.
5. Do not infer or add information beyond what the analysis states."""


EMOTIONAL_BEATS_PARSER_SYSTEM_PROMPT = """You are a structured data formatter. Extract ONLY the emotional beats from the analysis below.

RULES:
1. Map every emotional beat from the analysis into EmotionalBeat objects in order of appearance.
2. Transfer the moment description, emotion, techniques list, and effectiveness rating faithfully.
3. Use exact text from the analysis for all fields.
4. Do not add beats not described in the analysis.
5. Do not infer or add information beyond what the analysis states."""


def build_structure_analysis_prompt(
    extraction_plan: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    title_text = f" - {chapter_title}" if chapter_title else ""

    return f"""EXTRACTION PLAN:
{extraction_plan}

CHAPTER {chapter_number}{title_text}:
{current_chapter_content}

Analyze the structure and craft of Chapter {chapter_number}. Use the plan's story position for structural role, calibrate tension and pacing against the plan's baselines, and check theme continuity against the plan's theme tracking."""


def build_structure_parser_prompt(analysis: str) -> str:
    return f"""STRUCTURE ANALYSIS:
{analysis}

Convert this analysis into structured StructureExtraction data. Include every scene, theme, and emotional beat. Do not add or remove anything."""


def build_scenes_parser_prompt(analysis: str) -> str:
    return f"""STRUCTURE ANALYSIS:
{analysis}

Extract the structural role and all scenes from this analysis. Map every scene with its type, location, POV, goal, conflict, outcome, and word count. Do not add or remove any scenes."""


def build_pacing_parser_prompt(analysis: str) -> str:
    return f"""STRUCTURE ANALYSIS:
{analysis}

Extract the pacing breakdown (action/dialogue/introspection/exposition percentages, overall pace, tension level) and the show-vs-tell ratio from this analysis. Ensure percentages sum to 100."""


def build_themes_parser_prompt(analysis: str) -> str:
    return f"""STRUCTURE ANALYSIS:
{analysis}

Extract all themes from this analysis. For each theme, include the theme name, how it is explored, and any symbols or motifs. Do not add or remove any themes."""


def build_emotional_beats_parser_prompt(analysis: str) -> str:
    return f"""STRUCTURE ANALYSIS:
{analysis}

Extract all emotional beats from this analysis in order of appearance. For each, include the moment, emotion, techniques, and effectiveness rating. Do not add or remove any beats."""
