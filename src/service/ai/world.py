from typing import Optional, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from src.service.ai.prompts.world import (
    ANALYZER_SYSTEM_PROMPT,
    PARSER_SYSTEM_PROMPT,
    build_world_analysis_prompt,
    build_world_parser_prompt,
)
from src.service.ai.prompts.planners import WORLD_PLANNER_SYSTEM_PROMPT, build_world_planner_prompt
from src.data.models.ai.world import WorldExtraction
from src.infrastructure.config.settings import config
from src.service.ai.utils.model_factory import create_chat_model
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel

heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0,
)

model = create_chat_model(config.ai.model)

world_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(WorldExtraction),
)


class WorldExtractionState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    use_lfm: bool = False
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    result: Optional[WorldExtraction] = None


async def world_planner_node(state: WorldExtractionState) -> dict:
    plan_result: AIMessage = await model.ainvoke([
        SystemMessage(content=WORLD_PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=build_world_planner_prompt(
            state.story_context, state.current_chapter_content, state.chapter_number
        ))
    ])
    return {"extraction_plan": plan_result.content}


async def world_analyzer_node(state: WorldExtractionState) -> dict:
    analysis_result: AIMessage = await model.ainvoke([
        SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
        HumanMessage(content=build_world_analysis_prompt(
            extraction_plan=state.extraction_plan or "",
            current_chapter_content=state.current_chapter_content,
            chapter_number=state.chapter_number,
            chapter_title=state.chapter_title,
        ))
    ])
    return {"analysis": analysis_result.content}


async def world_parser_node(state: WorldExtractionState) -> dict:
    prompt = build_world_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from src.service.ai.utils.extractors import world_extractor
        result = await world_extractor.extract(prompt)
    else:
        resp = await world_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"result": result}


graph = StateGraph(WorldExtractionState)
graph.add_node("planner", world_planner_node, retry_policy=heavy_retry)
graph.add_node("analyzer", world_analyzer_node, retry_policy=heavy_retry)
graph.add_node("parser", world_parser_node, retry_policy=heavy_retry)
graph.add_edge("planner", "analyzer")
graph.add_edge("analyzer", "parser")
graph.add_edge("parser", END)
graph.set_entry_point("planner")
world_app = graph.compile()


async def extract_world_information(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    use_lfm: bool = False,
) -> WorldExtraction:
    state = WorldExtractionState(
        story_context=story_context,
        current_chapter_content=current_chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        use_lfm=use_lfm,
    )
    result = await world_app.ainvoke(state)  # type: ignore
    return result["result"]