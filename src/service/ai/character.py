# app/ai/character.py
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
from src.service.ai.utils.extractors import character_extractor
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


class CharacterExtractionState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    result: Optional[CharacterExtraction] = None


async def character_planner_node(state: CharacterExtractionState) -> dict:
    async with timed_event(log, "graph.character.planner", chapter_number=state.chapter_number) as t:
        plan_result: AIMessage = await model.ainvoke([
            SystemMessage(content=CHARACTER_PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=build_character_planner_prompt(
                state.story_context, state.current_chapter_content, state.chapter_number
            ))
        ])
        t.set(tokens=getattr(plan_result, 'usage_metadata', None))
    return {"extraction_plan": plan_result.content}


async def character_analyzer_node(state: CharacterExtractionState) -> dict:
    async with timed_event(log, "graph.character.analyzer", chapter_number=state.chapter_number) as t:
        analysis_result: AIMessage = await model.ainvoke([
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=build_character_analysis_prompt(
                extraction_plan=state.extraction_plan or "",
                current_chapter_content=state.current_chapter_content,
                chapter_number=state.chapter_number,
                chapter_title=state.chapter_title,
            ))
        ])
        t.set(tokens=getattr(analysis_result, 'usage_metadata', None))
    return {"analysis": analysis_result.content}


async def character_parser_node(state: CharacterExtractionState) -> dict:
    prompt = build_character_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.character.parser", chapter_number=state.chapter_number) as t:
        result = await character_extractor.extract(prompt)
        t.set(characters_found=len(result.characters) if result.characters else 0)
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
    story_id: str = "",
) -> CharacterExtraction:
    with log.contextualize(story_id=story_id):
        async with timed_event(log, "graph.character", level="INFO", chapter_number=chapter_number):
            state = CharacterExtractionState(
                story_context=story_context,
                current_chapter_content=current_chapter_content,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
            )
            result = await character_app.ainvoke(state)  # type: ignore
        return result["result"]