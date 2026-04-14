from typing import Optional, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
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
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel
import time
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0,
)

model = create_chat_model(config.ai.model)

# ── Per-component parser agents ──────────────────────────────

scenes_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=SCENES_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(ScenesExtraction),
)

pacing_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=PACING_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(PacingExtraction),
)

themes_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=THEMES_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(ThemesExtraction),
)

emotional_beats_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=EMOTIONAL_BEATS_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(EmotionalBeatsExtraction),
)


# ── State ────────────────────────────────────────────────────


class StructureExtractionState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    use_lfm: bool = False
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    scenes_result: Optional[ScenesExtraction] = None
    pacing_result: Optional[PacingExtraction] = None
    themes_result: Optional[ThemesExtraction] = None
    emotional_beats_result: Optional[EmotionalBeatsExtraction] = None
    result: Optional[StructureExtraction] = None


# ── Nodes ────────────────────────────────────────────────────


async def structure_planner_node(state: StructureExtractionState) -> dict:
    log.debug("graph.structure.planner.start", chapter_number=state.chapter_number)
    t0 = time.perf_counter()
    try:
        plan_result: AIMessage = await model.ainvoke([
            SystemMessage(content=STRUCTURE_PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=build_structure_planner_prompt(
                state.story_context, state.current_chapter_content, state.chapter_number
            ))
        ])
    except Exception:
        log.opt(exception=True).error("graph.structure.planner.error", chapter_number=state.chapter_number, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.structure.planner.done", chapter_number=state.chapter_number, elapsed_s=elapsed, tokens=getattr(plan_result, 'usage_metadata', None))
    return {"extraction_plan": plan_result.content}


async def structure_analyzer_node(state: StructureExtractionState) -> dict:
    log.debug("graph.structure.analyzer.start", chapter_number=state.chapter_number)
    t0 = time.perf_counter()
    try:
        analysis_result: AIMessage = await model.ainvoke([
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=build_structure_analysis_prompt(
                extraction_plan=state.extraction_plan or "",
                current_chapter_content=state.current_chapter_content,
                chapter_number=state.chapter_number,
                chapter_title=state.chapter_title,
            ))
        ])
    except Exception:
        log.opt(exception=True).error("graph.structure.analyzer.error", chapter_number=state.chapter_number, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.structure.analyzer.done", chapter_number=state.chapter_number, elapsed_s=elapsed, tokens=getattr(analysis_result, 'usage_metadata', None))
    return {"analysis": analysis_result.content}


async def scenes_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_scenes_parser_prompt(state.analysis or "")
    log.debug("graph.structure.parse_scenes.start", chapter_number=state.chapter_number, use_lfm=state.use_lfm)
    t0 = time.perf_counter()
    try:
        if state.use_lfm:
            from src.service.ai.utils.extractors import scenes_extractor
            result = await scenes_extractor.extract(prompt)
        else:
            resp = await scenes_parser_agent.ainvoke({
                "messages": [
                    SystemMessage(content=SCENES_PARSER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ]
            })
            result = resp["structured_response"]
    except Exception:
        log.opt(exception=True).error("graph.structure.parse_scenes.error", chapter_number=state.chapter_number, use_lfm=state.use_lfm, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.structure.parse_scenes.done", chapter_number=state.chapter_number, elapsed_s=elapsed, scenes_found=len(result.scenes) if result.scenes else 0)
    return {"scenes_result": result}


async def pacing_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_pacing_parser_prompt(state.analysis or "")
    log.debug("graph.structure.parse_pacing.start", chapter_number=state.chapter_number, use_lfm=state.use_lfm)
    t0 = time.perf_counter()
    try:
        if state.use_lfm:
            from src.service.ai.utils.extractors import pacing_extractor
            result = await pacing_extractor.extract(prompt)
        else:
            resp = await pacing_parser_agent.ainvoke({
                "messages": [
                    SystemMessage(content=PACING_PARSER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ]
            })
            result = resp["structured_response"]
    except Exception:
        log.opt(exception=True).error("graph.structure.parse_pacing.error", chapter_number=state.chapter_number, use_lfm=state.use_lfm, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.structure.parse_pacing.done", chapter_number=state.chapter_number, elapsed_s=elapsed)
    return {"pacing_result": result}


async def themes_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_themes_parser_prompt(state.analysis or "")
    log.debug("graph.structure.parse_themes.start", chapter_number=state.chapter_number, use_lfm=state.use_lfm)
    t0 = time.perf_counter()
    try:
        if state.use_lfm:
            from src.service.ai.utils.extractors import themes_extractor
            result = await themes_extractor.extract(prompt)
        else:
            resp = await themes_parser_agent.ainvoke({
                "messages": [
                    SystemMessage(content=THEMES_PARSER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ]
            })
            result = resp["structured_response"]
    except Exception:
        log.opt(exception=True).error("graph.structure.parse_themes.error", chapter_number=state.chapter_number, use_lfm=state.use_lfm, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    themes_count = len(result.themes) if result.themes else 0
    log.debug("graph.structure.parse_themes.done", chapter_number=state.chapter_number, elapsed_s=elapsed, themes_found=themes_count)
    return {"themes_result": result}


async def emotional_beats_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_emotional_beats_parser_prompt(state.analysis or "")
    log.debug("graph.structure.parse_emotional_beats.start", chapter_number=state.chapter_number, use_lfm=state.use_lfm)
    t0 = time.perf_counter()
    try:
        if state.use_lfm:
            from src.service.ai.utils.extractors import emotional_beats_extractor
            result = await emotional_beats_extractor.extract(prompt)
        else:
            resp = await emotional_beats_parser_agent.ainvoke({
                "messages": [
                    SystemMessage(content=EMOTIONAL_BEATS_PARSER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ]
            })
            result = resp["structured_response"]
    except Exception:
        log.opt(exception=True).error("graph.structure.parse_emotional_beats.error", chapter_number=state.chapter_number, use_lfm=state.use_lfm, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    beats_count = len(result.emotional_beats) if result.emotional_beats else 0
    log.debug("graph.structure.parse_emotional_beats.done", chapter_number=state.chapter_number, elapsed_s=elapsed, beats_found=beats_count)
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
    use_lfm: bool = False,
    story_id: str = "",
) -> StructureExtraction:
    with log.contextualize(story_id=story_id):
        log.info("graph.structure.invoke", chapter_number=chapter_number, use_lfm=use_lfm)
        t0 = time.perf_counter()
        state = StructureExtractionState(
            story_context=story_context,
            current_chapter_content=current_chapter_content,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            use_lfm=use_lfm,
        )
        result = await structure_app.ainvoke(state)  # type: ignore
        elapsed = round(time.perf_counter() - t0, 2)
        log.info("graph.structure.complete", chapter_number=chapter_number, elapsed_s=elapsed)
        return result["result"]