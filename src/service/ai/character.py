# app/ai/character.py
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from src.service.ai.prompts.character import (
    ANALYZER_SYSTEM_PROMPT,
    PARSER_SYSTEM_PROMPT,
    build_character_analysis_prompt,
    build_character_parser_prompt,
)
from src.service.ai.prompts.planners import CHARACTER_PLANNER_SYSTEM_PROMPT, build_character_planner_prompt
from src.data.models.ai.character import CharacterExtraction
from typing import Optional, List
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

character_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(CharacterExtraction),
)


class CharacterExtractionState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    use_lfm: bool = False
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    result: Optional[CharacterExtraction] = None


async def character_planner_node(state: CharacterExtractionState) -> dict:
    log.debug("graph.character.planner.start", chapter_number=state.chapter_number)
    t0 = time.perf_counter()
    try:
        plan_result: AIMessage = await model.ainvoke([
            SystemMessage(content=CHARACTER_PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=build_character_planner_prompt(
                state.story_context, state.current_chapter_content, state.chapter_number
            ))
        ])
    except Exception:
        log.opt(exception=True).error("graph.character.planner.error", chapter_number=state.chapter_number, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.character.planner.done", chapter_number=state.chapter_number, elapsed_s=elapsed, tokens=getattr(plan_result, 'usage_metadata', None))
    return {"extraction_plan": plan_result.content}


async def character_analyzer_node(state: CharacterExtractionState) -> dict:
    log.debug("graph.character.analyzer.start", chapter_number=state.chapter_number)
    t0 = time.perf_counter()
    try:
        analysis_result: AIMessage = await model.ainvoke([
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=build_character_analysis_prompt(
                extraction_plan=state.extraction_plan or "",
                current_chapter_content=state.current_chapter_content,
                chapter_number=state.chapter_number,
                chapter_title=state.chapter_title,
            ))
        ])
    except Exception:
        log.opt(exception=True).error("graph.character.analyzer.error", chapter_number=state.chapter_number, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.character.analyzer.done", chapter_number=state.chapter_number, elapsed_s=elapsed, tokens=getattr(analysis_result, 'usage_metadata', None))
    return {"analysis": analysis_result.content}


async def character_parser_node(state: CharacterExtractionState) -> dict:
    prompt = build_character_parser_prompt(state.analysis or "")
    log.debug("graph.character.parser.start", chapter_number=state.chapter_number, use_lfm=state.use_lfm)
    t0 = time.perf_counter()
    try:
        if state.use_lfm:
            from src.service.ai.utils.extractors import character_extractor
            result = await character_extractor.extract(prompt)
        else:
            resp = await character_parser_agent.ainvoke({
                "messages": [
                    SystemMessage(content=PARSER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ]
            })
            result = resp["structured_response"]
    except Exception:
        log.opt(exception=True).error("graph.character.parser.error", chapter_number=state.chapter_number, use_lfm=state.use_lfm, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    character_count = len(result.characters) if result.characters else 0
    log.debug("graph.character.parser.done", chapter_number=state.chapter_number, elapsed_s=elapsed, characters_found=character_count)
    return {"result": result}


graph = StateGraph(CharacterExtractionState)
graph.add_node("planner", character_planner_node, retry_policy=heavy_retry)
graph.add_node("analyzer", character_analyzer_node, retry_policy=heavy_retry)
graph.add_node("parser", character_parser_node, retry_policy=heavy_retry)
graph.add_edge("planner", "analyzer")
graph.add_edge("analyzer", "parser")
graph.add_edge("parser", END)
graph.set_entry_point("planner")
character_app = graph.compile()


async def extract_characters(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    use_lfm: bool = False,
    story_id: str = "",
) -> CharacterExtraction:
    with log.contextualize(story_id=story_id):
        log.info("graph.character.invoke", chapter_number=chapter_number, use_lfm=use_lfm)
        t0 = time.perf_counter()
        state = CharacterExtractionState(
            story_context=story_context,
            current_chapter_content=current_chapter_content,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            use_lfm=use_lfm,
        )
        result = await character_app.ainvoke(state)  # type: ignore
        elapsed = round(time.perf_counter() - t0, 2)
        log.info("graph.character.complete", chapter_number=chapter_number, elapsed_s=elapsed)
        return result["result"]