from typing import Annotated, Dict, List, Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from src.service.ai.prompts.edits import (
    PARSER_SYSTEM_PROMPT, 
    CRITIC_SYSTEM_PROMPT, 
    GENERATE_SYSTEM_PROMPT, 
    REVIEW_SYSTEM_PROMPT, 
    build_line_edit_prompt, 
    build_line_edit_review_prompt, 
    build_critic_user_prompt,
    build_parser_user_prompt
)
from src.data.models.ai.edits import ChapterEdit, LineEdit
from src.infrastructure.config.settings import config
from src.service.ai.utils.model_factory import create_chat_model
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel
from src.shared.utils.html import html_to_paragraphs
from src.service.ai.utils.ai import extract_text
import time
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)




heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,  # seconds
    backoff_factor=2.0,    # exponential backoff
)

model = create_chat_model(config.ai.lite_model)

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
    use_lfm: bool = False
    editor_plan: Optional[str] = None
    current_edits: Optional[str] = None
    paragraphs: Optional[List[str]] = None
    edits: Optional[List[LineEdit]] = None


async def generate_edit_plan_node(state: EditorState) -> dict:
    log.debug("graph.edits.plan.start", chapter_number=state.chapter_number)
    t0 = time.perf_counter()
    try:
        editor_plan_result: AIMessage = await model.ainvoke([
            SystemMessage(content=CRITIC_SYSTEM_PROMPT),
            HumanMessage(content=build_critic_user_prompt(state.story_context, state.current_chapter_content))
        ])
    except Exception:
        log.opt(exception=True).error("graph.edits.plan.error", chapter_number=state.chapter_number, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.edits.plan.done", chapter_number=state.chapter_number, elapsed_s=elapsed, tokens=getattr(editor_plan_result, 'usage_metadata', None))
    return {
        "editor_plan": extract_text(editor_plan_result.content),
        "paragraphs": html_to_paragraphs(state.current_chapter_content)
    }


async def generate_line_edits_node(state: EditorState) -> dict:
    log.debug("graph.edits.generate.start", chapter_number=state.chapter_number)
    t0 = time.perf_counter()
    
    try:
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
    except Exception:
        log.opt(exception=True).error("graph.edits.generate.error", chapter_number=state.chapter_number, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.edits.generate.done", chapter_number=state.chapter_number, elapsed_s=elapsed, tokens=getattr(current_edits_result, 'usage_metadata', None))

    return {
        "current_edits": extract_text(current_edits_result.content)
    }

async def review_line_edits_node(state: EditorState) -> dict:
    log.debug("graph.edits.review.start", chapter_number=state.chapter_number)
    t0 = time.perf_counter()
    
    try:
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
    except Exception:
        log.opt(exception=True).error("graph.edits.review.error", chapter_number=state.chapter_number, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    log.debug("graph.edits.review.done", chapter_number=state.chapter_number, elapsed_s=elapsed, tokens=getattr(revised_edits_result, 'usage_metadata', None))

    return {
        "current_edits": extract_text(revised_edits_result.content)
    }

async def generate_edit_model_node(state: EditorState) -> dict:
    prompt = build_parser_user_prompt(
        state.current_edits if state.current_edits else "",
        state.paragraphs if state.paragraphs else []
    )
    log.debug("graph.edits.parse.start", chapter_number=state.chapter_number, use_lfm=state.use_lfm)
    t0 = time.perf_counter()
    try:
        if state.use_lfm:
            from src.service.ai.utils.extractors import edits_extractor
            structured = await edits_extractor.extract(prompt)
        else:
            result = await parser_agent.ainvoke(
                {
                    "messages": [
                        SystemMessage(content=PARSER_SYSTEM_PROMPT),
                        HumanMessage(content=prompt)
                    ]
                }
            )
            structured = result["structured_response"]
    except Exception:
        log.opt(exception=True).error("graph.edits.parse.error", chapter_number=state.chapter_number, use_lfm=state.use_lfm, elapsed_s=round(time.perf_counter() - t0, 2))
        raise
    elapsed = round(time.perf_counter() - t0, 2)
    edit_count = len(structured.edits) if structured.edits else 0
    log.debug("graph.edits.parse.done", chapter_number=state.chapter_number, elapsed_s=elapsed, edits_parsed=edit_count)
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
    chapter_title: Optional[str] = None,
    use_lfm: bool = False,
    story_id: str = "",
) -> ChapterEdit:
    with log.contextualize(story_id=story_id):
        log.info("graph.edits.invoke", chapter_number=chapter_number, use_lfm=use_lfm)
        t0 = time.perf_counter()
        state = EditorState(
            story_context=story_context,
            current_chapter_content=current_chapter_content,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            use_lfm=use_lfm,
        )
        result = await app.ainvoke(state) # type: ignore
        edits = result["edits"]
        elapsed = round(time.perf_counter() - t0, 2)
        edit_count = len(edits) if edits else 0
        log.info("graph.edits.complete", chapter_number=chapter_number, elapsed_s=elapsed, edits_generated=edit_count)
        return ChapterEdit(edits=edits)
    
