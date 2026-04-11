from typing import Optional, List
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
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
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from pydantic import BaseModel

heavy_retry = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0,
)

model = create_chat_model(config.ai.model)

# ── Per-component parser agents ──────────────────────────────

events_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=EVENTS_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(EventsExtraction),
)

threads_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=THREADS_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(ThreadsExtraction),
)

setups_payoffs_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=SETUPS_PAYOFFS_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(SetupsPayoffsExtraction),
)

questions_contrivances_parser_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=QUESTIONS_CONTRIVANCES_PARSER_SYSTEM_PROMPT,
    response_format=ToolStrategy(QuestionsContrivancesExtraction),
)


# ── State ────────────────────────────────────────────────────


class PlotExtractionState(BaseModel):
    story_context: str
    current_chapter_content: str
    chapter_number: int
    chapter_title: Optional[str] = None
    use_lfm: bool = False
    extraction_plan: Optional[str] = None
    analysis: Optional[str] = None
    events_result: Optional[EventsExtraction] = None
    threads_result: Optional[ThreadsExtraction] = None
    setups_payoffs_result: Optional[SetupsPayoffsExtraction] = None
    questions_contrivances_result: Optional[QuestionsContrivancesExtraction] = None
    result: Optional[PlotExtraction] = None


# ── Nodes ────────────────────────────────────────────────────


async def plot_planner_node(state: PlotExtractionState) -> dict:
    plan_result: AIMessage = await model.ainvoke([
        SystemMessage(content=PLOT_PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=build_plot_planner_prompt(
            state.story_context, state.current_chapter_content, state.chapter_number
        ))
    ])
    return {"extraction_plan": plan_result.content}


async def plot_analyzer_node(state: PlotExtractionState) -> dict:
    analysis_result: AIMessage = await model.ainvoke([
        SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
        HumanMessage(content=build_plot_analysis_prompt(
            extraction_plan=state.extraction_plan or "",
            current_chapter_content=state.current_chapter_content,
            chapter_number=state.chapter_number,
            chapter_title=state.chapter_title,
        ))
    ])
    return {"analysis": analysis_result.content}


async def events_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_events_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from src.service.ai.utils.extractors import events_extractor
        result = await events_extractor.extract(prompt)
    else:
        resp = await events_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=EVENTS_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"events_result": result}


async def threads_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_threads_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from src.service.ai.utils.extractors import threads_extractor
        result = await threads_extractor.extract(prompt)
    else:
        resp = await threads_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=THREADS_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"threads_result": result}


async def setups_payoffs_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_setups_payoffs_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from src.service.ai.utils.extractors import setups_payoffs_extractor
        result = await setups_payoffs_extractor.extract(prompt)
    else:
        resp = await setups_payoffs_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=SETUPS_PAYOFFS_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"setups_payoffs_result": result}


async def questions_contrivances_parser_node(state: PlotExtractionState) -> dict:
    prompt = build_questions_contrivances_parser_prompt(state.analysis or "")
    if state.use_lfm:
        from src.service.ai.utils.extractors import questions_contrivances_extractor
        result = await questions_contrivances_extractor.extract(prompt)
    else:
        resp = await questions_contrivances_parser_agent.ainvoke({
            "messages": [
                SystemMessage(content=QUESTIONS_CONTRIVANCES_PARSER_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
        })
        result = resp["structured_response"]
    return {"questions_contrivances_result": result}


async def synthesize_node(state: PlotExtractionState) -> dict:
    return {
        "result": PlotExtraction.from_components(
            events=state.events_result or EventsExtraction(),
            threads=state.threads_result or ThreadsExtraction(),
            setups_payoffs=state.setups_payoffs_result or SetupsPayoffsExtraction(),
            questions_contrivances=state.questions_contrivances_result or QuestionsContrivancesExtraction(),
        )
    }


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
    use_lfm: bool = False,
) -> PlotExtraction:
    state = PlotExtractionState(
        story_context=story_context,
        current_chapter_content=current_chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        use_lfm=use_lfm,
    )
    result = await plot_app.ainvoke(state)  # type: ignore
    return result["result"]