from typing import Optional


SYSTEM_PROMPT = """You are a literary analyst extracting character data for automated story analysis.

Your extractions power these detections:
- PLOT HOLES: Characters acting on information they haven't learned yet
- FLAT ARCS: Characters whose emotional state and goals never change
- VOICE DRIFT: Characters whose speech patterns shift inconsistently
- SHOW VS TELL: Traits narrated ("she was brave") instead of demonstrated

RULES:
1. ENTITY RESOLUTION: If "Sarah", "Captain Chen", and "the Captain" appear, determine if they are the same person using context. Use the canonical full name.
2. is_new is true ONLY if the character never appears in the accumulated context.
3. Extract ALL characters mentioned, even minor ones.
4. knowledge_gains: Only NEW information learned THIS chapter. Not prior knowledge.
5. dialogue_voices: One representative sample per speaking character.
6. trait_evidence: Flag EVERY instance. shown=true for action/dialogue demonstration, shown=false for narration/description.

Output valid JSON matching the schema. No commentary."""


def build_character_extraction_prompt(
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

Extract all character data from Chapter {chapter_number}. Use accumulated context for entity resolution and is_new determination."""
