from typing import Optional, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from app.ai.prompts.structure import (
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
from app.ai.prompts.planners import STRUCTURE_PLANNER_SYSTEM_PROMPT, build_structure_planner_prompt
from app.ai.models.structure import (
    StructureExtraction,
    ScenesExtraction,
    PacingExtraction,
    ThemesExtraction,
    EmotionalBeatsExtraction,
)
from app.config.settings import app_config
from app.ai.utils.model_factory import create_chat_model
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel

heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0,
)

model = create_chat_model(app_config.ai_model)

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
    plan_result: AIMessage = await model.ainvoke([
        SystemMessage(content=STRUCTURE_PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=build_structure_planner_prompt(
            state.story_context, state.current_chapter_content, state.chapter_number
        ))
    ])
    return {"extraction_plan": plan_result.content}


async def structure_analyzer_node(state: StructureExtractionState) -> dict:
    analysis_result: AIMessage = await model.ainvoke([
        SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
        HumanMessage(content=build_structure_analysis_prompt(
            extraction_plan=state.extraction_plan or "",
            current_chapter_content=state.current_chapter_content,
            chapter_number=state.chapter_number,
            chapter_title=state.chapter_title,
        ))
    ])
    return {"analysis": analysis_result.content}


async def scenes_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_scenes_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from app.ai.utils.extractors import scenes_extractor
        result = await scenes_extractor.extract(prompt)
    else:
        resp = await scenes_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=SCENES_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"scenes_result": result}


async def pacing_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_pacing_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from app.ai.utils.extractors import pacing_extractor
        result = await pacing_extractor.extract(prompt)
    else:
        resp = await pacing_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=PACING_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"pacing_result": result}


async def themes_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_themes_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from app.ai.utils.extractors import themes_extractor
        result = await themes_extractor.extract(prompt)
    else:
        resp = await themes_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=THEMES_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"themes_result": result}


async def emotional_beats_parser_node(state: StructureExtractionState) -> dict:
    prompt = build_emotional_beats_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from app.ai.utils.extractors import emotional_beats_extractor
        result = await emotional_beats_extractor.extract(prompt)
    else:
        resp = await emotional_beats_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=EMOTIONAL_BEATS_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"emotional_beats_result": result}


async def synthesize_node(state: StructureExtractionState) -> dict:
    return {
        "result": StructureExtraction.from_components(
            scenes=state.scenes_result or ScenesExtraction(),
            pacing=state.pacing_result or PacingExtraction(),
            themes=state.themes_result or ThemesExtraction(),
            emotional_beats=state.emotional_beats_result or EmotionalBeatsExtraction(),
        )
    }


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
) -> StructureExtraction:
    state = StructureExtractionState(
        story_context=story_context,
        current_chapter_content=current_chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        use_lfm=use_lfm,
    )
    result = await structure_app.ainvoke(state)  # type: ignore
    return result["result"]