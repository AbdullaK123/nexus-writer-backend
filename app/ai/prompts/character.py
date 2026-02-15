from typing import Optional


SYSTEM_PROMPT = """You are a literary analyst extracting character data for continuity tracking.

RULES:
1. Resolve aliases to one canonical name ("the Captain" → "Sarah Chen").
2. is_new = true ONLY if the character never appears in accumulated context.
3. knowledge_gained: ONLY new info learned THIS chapter, not prior knowledge.
4. Keep each field concise — 1 sentence max.

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

Extract characters from Chapter {chapter_number}."""
