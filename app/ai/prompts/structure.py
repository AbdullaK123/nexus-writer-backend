from typing import Optional


SYSTEM_PROMPT = """You are a narrative craft analyst extracting structural data for automated story analysis.

Your extractions power these detections:
- PACING PROBLEMS: Saggy middle (low tension streaks), rushed climax (key scenes too short), info-dumps (exposition > 40%)
- SCENE ISSUES: Missing goal-conflict-outcome, filler scenes
- SHOW VS TELL: Chapter-level ratio of demonstration vs narration

RULES:
1. SCENES: Break chapter into scenes (new scene = change in time, location, or POV). Every scene needs clear goal, conflict, and outcome.
2. PACING: Percentages must sum to 100. Be honest about tension level.
3. STRUCTURAL ROLE: Use accumulated context to determine where this chapter sits in the overall arc.
4. THEMES: Only themes ACTIVELY explored, not briefly mentioned.
5. EMOTIONAL BEATS: Assess effectiveness honestly based on actual craft techniques used.
6. SHOW VS TELL RATIO: 0.0 = pure narration ("she was brave"), 1.0 = pure demonstration. Good prose = 0.5-0.7.

Output valid JSON matching the schema. No commentary."""


def build_structure_extraction_prompt(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    title_text = f" - {chapter_title}" if chapter_title else ""
    context_block = "[Chapter 1 — no prior context]" if chapter_number == 1 else story_context

    return f"""ACCUMULATED CONTEXT (Ch 1-{chapter_number - 1}):
{context_block}

CHAPTER {chapter_number}{title_text}:
{current_chapter_content}

Extract structural and craft data from Chapter {chapter_number}. Use accumulated context to determine structural role and thematic continuity."""
