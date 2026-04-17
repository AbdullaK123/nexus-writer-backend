from typing import Optional, List
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from src.service.ai.prompts.plot import (
    ANALYZER_SYSTEM_PROMPT,
    PARSER_SYSTEM_PROMPT,
    EVENTS_PARSER_SYSTEM_PROMPT,
    THREADS_PARSER_SYSTEM_PROMPT,
    SETUPS_PAYOFFS_PARSER_SYSTEM_PROMPT,
    QUESTIONS_CONTRIVANCES_PARSER_SYSTEM_PROMPT,
    build_plot_analysis_prompt,
    build_plot_parser_prompt,
    build_events_parser_prompt,
    build_threads_parser_prompt,
    build_setups_payoffs_parser_prompt,
    build_questions_contrivances_parser_prompt,
)
from src.service.ai.prompts.planners import PLOT_PLANNER_SYSTEM_PROMPT, build_plot_planner_prompt
from src.data.models.ai.plot import (
    PlotExtraction,
    EventsExtraction,
    ThreadsExtraction,
    SetupsPayoffsExtraction,
    QuestionsContrivancesExtraction,
)
from src.infrastructure.config.settings import config
from src.service.ai.utils.model_factory import create_chat_model
from src.service.ai.utils.extractors import (
    events_extractor,
    threads_extractor,
    setups_payoffs_extractor,
    questions_contrivances_extractor,
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


class PlotExtractionState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    events_result: Optional[EventsExtraction] = None
    threads_result: Optional[ThreadsExtraction] = None
    setups_payoffs_result: Optional[SetupsPayoffsExtraction] = None
    questions_contrivances_result: Optional[QuestionsContrivancesExtraction] = None
    result: Optional[PlotExtraction] = None


# ── Nodes ────────────────────────────────────────────────────


async def plot_planner_node(state: PlotExtractionState) -> dict:
    async with timed_event(log, "graph.plot.planner", chapter_number=state.chapter_number) as t:
        plan_result: AIMessage = await model.ainvoke([
            SystemMessage(content=PLOT_PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=build_plot_planner_prompt(
                state.story_context, state.current_chapter_content, state.chapter_number
            ))
        ])
        t.set(tokens=getattr(plan_result, 'usage_metadata', None))
    return {"extraction_plan": plan_result.content}


async def plot_analyzer_node(state: PlotExtractionState) -> dict:
    async with timed_event(log, "graph.plot.analyzer", chapter_number=state.chapter_number) as t:
        analysis_result: AIMessage = await model.ainvoke([
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=build_plot_analysis_prompt(
                extraction_plan=state.extraction_plan or "",
                current_chapter_content=state.current_chapter_content,
                chapter_number=state.chapter_number,
                chapter_title=state.chapter_title,
            ))
        ])
        t.set(tokens=getattr(analysis_result, 'usage_metadata', None))
    return {"analysis": analysis_result.content}


async def events_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_events_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.plot.parse_events", chapter_number=state.chapter_number) as t:
        result = await events_extractor.extract(prompt)
        t.set(events_found=len(result.events) if result.events else 0)
    return {"events_result": result}


async def threads_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_threads_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.plot.parse_threads", chapter_number=state.chapter_number) as t:
        result = await threads_extractor.extract(prompt)
        t.set(threads_found=len(result.threads) if result.threads else 0)
    return {"threads_result": result}


async def setups_payoffs_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_setups_payoffs_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.plot.parse_setups_payoffs", chapter_number=state.chapter_number) as t:
        result = await setups_payoffs_extractor.extract(prompt)
        t.set(
            setups_found=len(result.setups) if result.setups else 0,
            payoffs_found=len(result.payoffs) if result.payoffs else 0,
        )
    return {"setups_payoffs_result": result}


async def questions_contrivances_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_questions_contrivances_parser_prompt(state.analysis or "")
    async with timed_event(log, "graph.plot.parse_questions_contrivances", chapter_number=state.chapter_number) as t:
        result = await questions_contrivances_extractor.extract(prompt)
        t.set(
            questions_found=len(result.questions) if result.questions else 0,
            contrivances_found=len(result.contrivance_risks) if result.contrivance_risks else 0,
        )
    return {"questions_contrivances_result": result}


async def synthesize_node(state: PlotExtractionState) -> dict:
    log.debug("graph.plot.synthesize.start", chapter_number=state.chapter_number)
    result = PlotExtraction.from_components(
        events=state.events_result or EventsExtraction(),
        threads=state.threads_result or ThreadsExtraction(),
        setups_payoffs=state.setups_payoffs_result or SetupsPayoffsExtraction(),
        questions_contrivances=state.questions_contrivances_result or QuestionsContrivancesExtraction(),
    )
    log.debug("graph.plot.synthesize.done", chapter_number=state.chapter_number)
    return {"result": result}


# ── Graph ────────────────────────────────────────────────────


graph = StateGraph(PlotExtractionState)
graph.add_node("planner", plot_planner_node, retry_policy=heavy_retry)
graph.add_node("analyzer", plot_analyzer_node, retry_policy=heavy_retry)
graph.add_node("parse_events", events_parser_node, retry_policy=heavy_retry)
graph.add_node("parse_threads", threads_parser_node, retry_policy=heavy_retry)
graph.add_node("parse_setups_payoffs", setups_payoffs_parser_node, retry_policy=heavy_retry)
graph.add_node("parse_questions_contrivances", questions_contrivances_parser_node, retry_policy=heavy_retry)
graph.add_node("synthesize", synthesize_node)

graph.add_edge("planner", "analyzer")
# Fan out: analyzer feeds all 4 parsers in parallel
graph.add_edge("analyzer", "parse_events")
graph.add_edge("analyzer", "parse_threads")
graph.add_edge("analyzer", "parse_setups_payoffs")
graph.add_edge("analyzer", "parse_questions_contrivances")
# Fan in: all parsers feed into synthesize
graph.add_edge("parse_events", "synthesize")
graph.add_edge("parse_threads", "synthesize")
graph.add_edge("parse_setups_payoffs", "synthesize")
graph.add_edge("parse_questions_contrivances", "synthesize")
graph.add_edge("synthesize", END)
graph.set_entry_point("planner")
plot_app = graph.compile()


async def extract_plot_information(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None,
    story_id: str = "",
) -> PlotExtraction:
    with log.contextualize(story_id=story_id):
        async with timed_event(log, "graph.plot", level="INFO", chapter_number=chapter_number):
            state = PlotExtractionState(
                story_context=story_context,
                current_chapter_content=current_chapter_content,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
            )
            result = await plot_app.ainvoke(state)  # type: ignore
        return result["result"]
        return result["result"]