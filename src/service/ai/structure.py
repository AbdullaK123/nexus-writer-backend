from typing import Optional, List
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from src.service.ai.prompts.structure import (
    ANALYZER_SYSTEM_PROMPT,
    PARSER_SYSTEM_PROMPT,
    SCENES_PARSER_SYSTEM_PROMPT,
    PACING_PARSER_SYSTEM_PROMPT,
    THEMES_PARSER_SYSTEM_PROMPT,
    EMOTIONAL_BEATS_PARSER_SYSTEM_PROMPT,
    build_structure_analysis_prompt,
    build_structure_parser_prompt,
    build_scenes_parser_prompt,
    build_pacing_parser_prompt,
    build_themes_parser_prompt,
    build_emotional_beats_parser_prompt,
)
from src.service.ai.prompts.planners import STRUCTURE_PLANNER_SYSTEM_PROMPT, build_structure_planner_prompt
from src.data.models.ai.structure import (
    StructureExtraction,
    ScenesExtraction,
    PacingExtraction,
    ThemesExtraction,
    EmotionalBeatsExtraction,
)
from src.infrastructure.config.settings import config
from src.service.ai.utils.model_factory import create_chat_model
from src.service.ai.utils.extractors import (
    scenes_extractor,
    pacing_extractor,
    themes_extractor,
    emotional_beats_extractor,
)
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel
from src.shared.utils.decorators import timed_event
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0,
)

model = create_chat_model(config.ai.model)


# ── State ────────────────────────────────────────────────────


class StructureExtractionState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    scenes_result: Optional[ScenesExtraction] = None
    pacing_result: Optional[PacingExtraction] = None
    themes_result: Optional[ThemesExtraction] = None
    emotional_beats_result: Optional[EmotionalBeatsExtraction] = None
    result: Optional[StructureExtraction] = None


# ── Nodes ────────────────────────────────────────────────────


async def structure_planner_node(state: StructureExtractionState) -> dict:
    async with timed_event(log, "graph.structure.planner", chapter_number=state.chapter_number) as t:
        plan_result: AIMessage = await model.ainvoke([
            SystemMessage(content=STRUCTURE_PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=build_structure_planner_prompt(
                state.story_context, state.current_chapter_content, state.chapter_number
            ))
        ])
        t.set(tokens=getattr(plan_result, 'usage_metadata', None))
    return {"extraction_plan": plan_result.content}


async def structure_analyzer_node(state: StructureExtractionState) -> dict:
    async with timed_event(log, "graph.structure.analyzer", chapter_number=state.chapter_number) as t:
        analysis_result: AIMessage = await model.ainvoke([
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=build_structure_analysis_prompt(
                extraction_plan=state.extraction_plan or "",
                current_chapter_content=state.current_chapter_content,
                chapter_number=state.chapter_number,
                chapter_title=state.chapter_title,
            ))
        ])
        t.set(tokens=getattr(analysis_result, 'usage_metadata', None))
    return {"analysis": analysis_result.content}


async def scenes_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_scenes_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.structure.parse_scenes", chapter_number=state.chapter_number) as t:
        result = await scenes_extractor.extract(prompt)
        t.set(scenes_found=len(result.scenes) if result.scenes else 0)
    return {"scenes_result": result}


async def pacing_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_pacing_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.structure.parse_pacing", chapter_number=state.chapter_number):
        result = await pacing_extractor.extract(prompt)
    return {"pacing_result": result}


async def themes_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_themes_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.structure.parse_themes", chapter_number=state.chapter_number) as t:
        result = await themes_extractor.extract(prompt)
        t.set(themes_found=len(result.themes) if result.themes else 0)
    return {"themes_result": result}


async def emotional_beats_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_emotional_beats_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.structure.parse_emotional_beats", chapter_number=state.chapter_number) as t:
        result = await emotional_beats_extractor.extract(prompt)
        t.set(beats_found=len(result.emotional_beats) if result.emotional_beats else 0)
    return {"emotional_beats_result": result}


async def synthesize_node(state: StructureExtractionState) -> dict:
    log.debug("graph.structure.synthesize.start", chapter_number=state.chapter_number)
    result = StructureExtraction.from_components(
        scenes=state.scenes_result or ScenesExtraction(),
        pacing=state.pacing_result or PacingExtraction(),
        themes=state.themes_result or ThemesExtraction(),
        emotional_beats=state.emotional_beats_result or EmotionalBeatsExtraction(),
    )
    log.debug("graph.structure.synthesize.done", chapter_number=state.chapter_number)
    return {"result": result}


# ── Graph ────────────────────────────────────────────────────


graph = StateGraph(StructureExtractionState)
graph.add_node("planner", structure_planner_node, retry_policy=heavy_retry)
graph.add_node("analyzer", structure_analyzer_node, retry_policy=heavy_retry)
graph.add_node("parse_scenes", scenes_parser_node, retry_policy=heavy_retry)
graph.add_node("parse_pacing", pacing_parser_node, retry_policy=heavy_retry)
graph.add_node("parse_themes", themes_parser_node, retry_policy=heavy_retry)
graph.add_node("parse_emotional_beats", emotional_beats_parser_node, retry_policy=heavy_retry)
graph.add_node("synthesize", synthesize_node)

graph.add_edge("planner", "analyzer")
# Fan out: analyzer feeds all 4 parsers in parallel
graph.add_edge("analyzer", "parse_scenes")
graph.add_edge("analyzer", "parse_pacing")
graph.add_edge("analyzer", "parse_themes")
graph.add_edge("analyzer", "parse_emotional_beats")
# Fan in: all parsers feed into synthesize
graph.add_edge("parse_scenes", "synthesize")
graph.add_edge("parse_pacing", "synthesize")
graph.add_edge("parse_themes", "synthesize")
graph.add_edge("parse_emotional_beats", "synthesize")
graph.add_edge("synthesize", END)
graph.set_entry_point("planner")
structure_app = graph.compile()


async def extract_story_structure(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    story_id: str = "",
) -> StructureExtraction:
    with log.contextualize(story_id=story_id):
        async with timed_event(log, "graph.structure", level="INFO", chapter_number=chapter_number):
            state = StructureExtractionState(
                story_context=story_context,
                current_chapter_content=current_chapter_content,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
            )
            result = await structure_app.ainvoke(state)  # type: ignore
        return result["result"]