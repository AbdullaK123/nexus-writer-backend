from typing import Optional
from toon import encode


SYSTEM_PROMPT = """You are a narrative synthesizer creating condensed chapter summaries for downstream AI analysis.

Synthesize character, plot, world, and structure extractions into a single condensed context (max 1500 words) that preserves ALL story-critical information.

PRIORITIES (in order):
1. Every concrete fact (names, traits, measurements, dates) — powers contradiction detection
2. Who learned what information — powers plot hole detection
3. Plot thread status changes — powers abandonment detection
4. Character state changes (emotional state, goals, condition) — powers arc tracking
5. World rules and limitations — powers consistency checking
6. Timeline markers — powers temporal logic checking

FORMAT:
- Use canonical character names with aliases on first mention
- Connect events causally
- Be ruthlessly concise — every word must earn its place

Output valid JSON matching the schema. No commentary."""


def build_condensed_context_prompt(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    character_extraction: dict,
    plot_extraction: dict,
    world_extraction: dict,
    structure_extraction: dict
) -> str:
    title_text = f' - "{chapter_title}"' if chapter_title else ""

    char_toon = encode(character_extraction)
    plot_toon = encode(plot_extraction)
    world_toon = encode(world_extraction)
    struct_toon = encode(structure_extraction)

    return f"""Synthesize Chapter {chapter_number}{title_text} into condensed context.

chapter_id: "{chapter_id}"
word_count: {word_count}
estimated_reading_time_minutes: {word_count // 250}

CHARACTER DATA:
{char_toon}

PLOT DATA:
{plot_toon}

WORLD DATA:
{world_toon}

STRUCTURE DATA:
{struct_toon}

Write condensed_text (max 1500 words) using this structure:
=== CHAPTER {chapter_number}{title_text} ===
[TIMELINE] When this happens in the story
[ENTITIES] Characters (canonical name + aliases), locations, objects
[EVENTS] Key events in sequence with outcomes and causality
[KNOWLEDGE] Who learned what and how
[CHARACTER STATES] End-of-chapter emotional state, goals, condition per character
[PLOT THREADS] Active storylines and current status
[SETUPS] Emphasized elements that need payoff
[FACTS] ALL concrete claims: physical traits, measurements, dates, capabilities, rules
[STRUCTURE] Pacing, tension level, themes"""
