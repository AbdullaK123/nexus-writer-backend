"""
Structured parser extractors for the parser nodes in each LangGraph pipeline.

Each extractor is a module-level singleton that converts analysis text into a
structured Pydantic model.

OpenAI extractors use Strict Mode (constrained decoding) via the OpenAI API,
making malformed output impossible by construction.
"""

from src.service.ai.utils.openai_extractor import OpenAIExtractor
from src.data.models.ai.character import CharacterExtraction
from src.data.models.ai.plot import (
    EventsExtraction,
    ThreadsExtraction,
    SetupsPayoffsExtraction,
    QuestionsContrivancesExtraction,
)
from src.data.models.ai.world import WorldExtraction
from src.data.models.ai.structure import (
    ScenesExtraction,
    PacingExtraction,
    ThemesExtraction,
    EmotionalBeatsExtraction,
)
from src.data.models.ai.context import CondensedChapterContext
from src.data.models.ai.edits import ChapterEdit


# ── System Prompts (parser-level: analysis text → structured JSON) ────────

_CHARACTER_PROMPT = (
    "You are a structured data formatter. Convert the provided character analysis "
    "into structured character extraction data. Extract every character with a "
    "meaningful presence, using canonical names, and capture their role, emotional "
    "state, goals, and knowledge gained."
)

_EVENTS_PROMPT = (
    "You are a structured data formatter. Convert the provided plot analysis "
    "into structured event extraction data. Capture each significant plot event "
    "with characters involved, location, and outcome."
)

_THREADS_PROMPT = (
    "You are a structured data formatter. Convert the provided plot analysis "
    "into structured plot thread data. Capture each active storyline with its "
    "status, importance, and resolution requirements."
)

_SETUPS_PAYOFFS_PROMPT = (
    "You are a structured data formatter. Convert the provided plot analysis "
    "into structured setups and payoffs data. Capture foreshadowing setups and "
    "their resolutions with matching element labels."
)

_QUESTIONS_CONTRIVANCES_PROMPT = (
    "You are a structured data formatter. Convert the provided plot analysis "
    "into structured story questions and contrivance risk data."
)

_WORLD_PROMPT = (
    "You are a structured data formatter. Convert the provided world analysis "
    "into structured entity/attribute/value fact triples for continuity checking."
)

_SCENES_PROMPT = (
    "You are a structured data formatter. Convert the provided structure analysis "
    "into structured scene breakdown data with structural role classification."
)

_PACING_PROMPT = (
    "You are a structured data formatter. Convert the provided structure analysis "
    "into structured pacing metrics and show-vs-tell ratio data."
)

_THEMES_PROMPT = (
    "You are a structured data formatter. Convert the provided structure analysis "
    "into structured theme data with exploration methods and symbols."
)

_EMOTIONAL_BEATS_PROMPT = (
    "You are a structured data formatter. Convert the provided structure analysis "
    "into structured emotional beat data with techniques and effectiveness."
)

_CONTEXT_PROMPT = (
    "You are a structured data formatter. Synthesize the provided chapter extraction "
    "data into condensed context for downstream AI analysis. Be ruthlessly concise. "
    "Prioritize concrete facts, information asymmetry, plot thread status, "
    "character state changes, world rules, and timeline markers."
)

_EDITS_PROMPT = (
    "You are a structured data formatter. Convert the provided reviewed line edits "
    "from plain-text format into structured LineEdit objects. Map each edit block "
    "to a LineEdit with the correct paragraph_idx, original_paragraph, edited_paragraph, "
    "and justification. Transfer faithfully without modification."
)


# ── Extractor Singletons ─────────────────────────────────────

character_extractor = OpenAIExtractor(model=CharacterExtraction, system_prompt=_CHARACTER_PROMPT)

events_extractor = OpenAIExtractor(model=EventsExtraction, system_prompt=_EVENTS_PROMPT)
threads_extractor = OpenAIExtractor(model=ThreadsExtraction, system_prompt=_THREADS_PROMPT)
setups_payoffs_extractor = OpenAIExtractor(model=SetupsPayoffsExtraction, system_prompt=_SETUPS_PAYOFFS_PROMPT)
questions_contrivances_extractor = OpenAIExtractor(model=QuestionsContrivancesExtraction, system_prompt=_QUESTIONS_CONTRIVANCES_PROMPT)

world_extractor = OpenAIExtractor(model=WorldExtraction, system_prompt=_WORLD_PROMPT)

scenes_extractor = OpenAIExtractor(model=ScenesExtraction, system_prompt=_SCENES_PROMPT)
pacing_extractor = OpenAIExtractor(model=PacingExtraction, system_prompt=_PACING_PROMPT)
themes_extractor = OpenAIExtractor(model=ThemesExtraction, system_prompt=_THEMES_PROMPT)
emotional_beats_extractor = OpenAIExtractor(model=EmotionalBeatsExtraction, system_prompt=_EMOTIONAL_BEATS_PROMPT)

context_extractor = OpenAIExtractor(model=CondensedChapterContext, system_prompt=_CONTEXT_PROMPT)

edits_extractor = OpenAIExtractor(model=ChapterEdit, system_prompt=_EDITS_PROMPT)
