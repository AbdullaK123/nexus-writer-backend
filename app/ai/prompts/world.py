from typing import Optional


SYSTEM_PROMPT = """You are a continuity analyst. Extract entity/attribute/value fact triples from a single chapter.

These triples are compared across chapters to catch contradictions automatically.

Extract 10-20 facts. Prioritize details that COULD CONTRADICT another chapter:
- Numbers: ages, distances, populations, dates, durations
- Physical traits: eye color, height, scars, species
- Relationships: "X is Y's sister"
- Injuries and healing status
- Named abilities and their limitations
- Locations characters are at

Skip generic facts. Every triple must be specific and verifiable."""


def build_world_extraction_prompt(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> str:
    title_text = f" - {chapter_title}" if chapter_title else ""
    context_block = "[Chapter 1 — no prior context]" if chapter_number == 1 else story_context

    return f"""CONTEXT (Ch 1-{chapter_number - 1}):
{context_block}

CHAPTER {chapter_number}{title_text}:
{current_chapter_content}

Extract fact triples from Chapter {chapter_number}."""
