from typing import Optional


SYSTEM_PROMPT = """You are a story structure analyst extracting plot data for automated story analysis.

Your extractions power these detections:
- ABANDONED THREADS: Important storylines that disappear without resolution
- CHEKHOV'S GUN: Emphasized setups that never pay off
- DEUS EX MACHINA: Problems solved by things that appeared from nowhere
- UNANSWERED QUESTIONS: Major mysteries never resolved

RULES:
1. EVENTS: Only SIGNIFICANT plot events. Skip routine actions unless they have consequences.
2. THREADS: Report ALL active storylines visible in this chapter with current status.
3. SETUPS: Flag objects, abilities, or details given unusual emphasis — they must pay off later.
4. PAYOFFS: When this chapter resolves something set up earlier, note it. Post-processing matches to setups.
5. CONTRIVANCE: If a problem is solved too conveniently, flag it. has_prior_setup=false if the solution was never foreshadowed.
6. Use accumulated context to recognize returning threads and callbacks to earlier material.

Output valid JSON matching the schema. No commentary."""


def build_plot_extraction_prompt(
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

Extract all plot data from Chapter {chapter_number}. Use accumulated context to identify returning threads, callbacks, and cross-chapter causality."""
