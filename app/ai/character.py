# app/ai/character.py
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from app.ai.prompts.character import (
    ANALYZER_SYSTEM_PROMPT,
    PARSER_SYSTEM_PROMPT,
    build_character_analysis_prompt,
    build_character_parser_prompt,
)
from app.ai.prompts.planners import CHARACTER_PLANNER_SYSTEM_PROMPT, build_character_planner_prompt
from app.ai.models.character import CharacterExtraction
from typing import Optional, List
from app.config.settings import app_config
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel

heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0,
)

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=app_config.ai_sdk_timeout,
    max_retries=app_config.ai_sdk_retries,
)

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
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    result: Optional[CharacterExtraction] = None


async def character_planner_node(state: CharacterExtractionState) -> dict:
    plan_result: AIMessage = await model.ainvoke([
        SystemMessage(content=CHARACTER_PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=build_character_planner_prompt(
            state.story_context, state.current_chapter_content, state.chapter_number
        ))
    ])
    return {"extraction_plan": plan_result.content}


async def character_analyzer_node(state: CharacterExtractionState) -> dict:
    analysis_result: AIMessage = await model.ainvoke([
        SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
        HumanMessage(content=build_character_analysis_prompt(
            extraction_plan=state.extraction_plan or "",
            current_chapter_content=state.current_chapter_content,
            chapter_number=state.chapter_number,
            chapter_title=state.chapter_title,
        ))
    ])
    return {"analysis": analysis_result.content}


async def character_parser_node(state: CharacterExtractionState) -> dict:
    result = await character_parser_agent.ainvoke({
        "messages": [
            SystemMessage(content=PARSER_SYSTEM_PROMPT),
            HumanMessage(content=build_character_parser_prompt(state.analysis or ""))
        ]
    })
    return {"result": result["structured_response"]}


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
    chapter_title: Optional[str] = None
) -> CharacterExtraction:
    state = CharacterExtractionState(
        story_context=story_context,
        current_chapter_content=current_chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
    )
    result = await character_app.ainvoke(state)  # type: ignore
    return result["result"]