from typing import Annotated, Dict, List, Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from app.ai.prompts.edits import (
    PARSER_SYSTEM_PROMPT, 
    CRITIC_SYSTEM_PROMPT, 
    GENERATE_SYSTEM_PROMPT, 
    REVIEW_SYSTEM_PROMPT, 
    build_line_edit_prompt, 
    build_line_edit_review_prompt, 
    build_critic_user_prompt,
    build_parser_user_prompt
)
from app.ai.models.edits import ChapterEdit, LineEdit
from app.config.settings import app_config
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel
from app.utils.html import html_to_paragraphs

heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,  # seconds
    backoff_factor=2.0,    # exponential backoff
)

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=app_config.ai_sdk_timeout,
    max_retries=app_config.ai_sdk_retries,
)

parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(ChapterEdit),
)

class EditorState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    editor_plan: Optional[str] = None
    current_edits: Optional[str] = None
    paragraphs: Optional[List[str]] = None
    edits: Optional[List[LineEdit]] = None


async def generate_edit_plan_node(state: EditorState) -> dict:
    editor_plan_result: AIMessage = await model.ainvoke([
        SystemMessage(content=CRITIC_SYSTEM_PROMPT),
        HumanMessage(content=build_critic_user_prompt(state.story_context, state.current_chapter_content))
    ])
    return {
        "editor_plan": editor_plan_result.content,
        "paragraphs": html_to_paragraphs(state.current_chapter_content)
    }


async def generate_line_edits_node(state: EditorState) -> dict:
    
    current_edits_result: AIMessage = await model.ainvoke([
        SystemMessage(content=GENERATE_SYSTEM_PROMPT),
        HumanMessage(
            content=build_line_edit_prompt(
                editor_plan=state.editor_plan if state.editor_plan else "",
                current_chapter_content=state.current_chapter_content, 
                chapter_number=state.chapter_number, 
                chapter_title=state.chapter_title
            )
        )
    ])

    return {
        "current_edits": current_edits_result.content
    }

async def review_line_edits_node(state: EditorState) -> dict:
    
    revised_edits_result = await model.ainvoke([
        SystemMessage(content=REVIEW_SYSTEM_PROMPT),
        HumanMessage(
            content=build_line_edit_review_prompt(
                current_edits=state.current_edits if state.current_edits else "",
                editor_plan=state.editor_plan if state.editor_plan else "",
                current_chapter_content=state.current_chapter_content,
                chapter_number=state.chapter_number,
                chapter_title=state.chapter_title
            )
        )
    ])

    return {
        "current_edits": revised_edits_result.content
    }

async def generate_edit_model_node(state: EditorState) -> dict:

    result = await parser_agent.ainvoke(
        {
            "messages": [
                SystemMessage(content=PARSER_SYSTEM_PROMPT),
                HumanMessage(
                    content=build_parser_user_prompt(
                        state.current_edits if state.current_edits else "", 
                        state.paragraphs if state.paragraphs else []
                    )
                )
            ]
        }
    )

    structured: ChapterEdit = result["structured_response"]
    return {
        "edits": structured.edits
    }


graph = StateGraph(EditorState)
graph.add_node("generate_edit_plan", generate_edit_plan_node, retry_policy=heavy_retry)
graph.add_node("generate_edits", generate_line_edits_node, retry_policy=heavy_retry)
graph.add_node("review_edits", review_line_edits_node, retry_policy=heavy_retry)
graph.add_node("generate_edit_model", generate_edit_model_node, retry_policy=heavy_retry)
graph.add_edge("generate_edit_plan", "generate_edits")
graph.add_edge("generate_edits", "review_edits")
graph.add_edge("review_edits", "generate_edit_model")
graph.add_edge("generate_edit_model", END)
graph.set_entry_point("generate_edit_plan")
app = graph.compile()


async def generate_line_edits(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> ChapterEdit:
    state = EditorState(
        story_context=story_context,
        current_chapter_content=current_chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title
    )
    result = await app.ainvoke(state) # type: ignore
    edits = result["edits"]
    return ChapterEdit(edits=edits)
    
