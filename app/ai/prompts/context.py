from typing import Optional
from toon import encode


SYSTEM_PROMPT = """You are a narrative synthesizer compressing per-chapter extraction data into a single condensed context document used by all downstream AI analysis.

Every word you write is fed to future LLM calls as context for the NEXT chapter. Wasted words degrade downstream extraction quality. Be ruthlessly concise — every sentence must earn its place.

PRIORITIES (highest first):
1. CONCRETE FACTS (names, traits, measurements, dates, locations, object ownership) — powers contradiction detection
2. INFORMATION ASYMMETRY (who learned what, who still doesn't know) — powers plot-hole detection
3. PLOT THREAD STATUS (which storylines advanced, stalled, or resolved this chapter) — powers abandonment detection
4. CHARACTER STATE CHANGES (end-of-chapter emotional state, goals, physical condition) — powers arc tracking
5. WORLD RULES AND LIMITATIONS (how abilities/tech/magic work, what constraints exist) — powers consistency checking
6. TIMELINE MARKERS (when events happen relative to each other: "three days after the battle," "that same evening") — powers temporal logic checking

RULES:
1. Use canonical character names. On first mention include aliases in parentheses: "Captain Sarah Chen (the Captain, Chen)." After that, use the shortest unambiguous form.
2. Connect events causally: "X happened, which caused Y" — not just "X happened. Y happened."
3. Omit generic scene-setting, emotional atmosphere, and craft commentary. Only facts, events, and state changes belong here.
4. When a fact from a PREVIOUS chapter changes this chapter (character heals, switches allegiance, gains new info), state the change explicitly: "Marcus's broken arm is now healed" — don't just omit the old fact.
5. Keep the condensed_text under 1500 words. If you must cut, sacrifice lower-priority items first."""


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
