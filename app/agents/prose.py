from typing import Any, cast
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.agents.models import ChapterEdit
from app.agents.prompts import PROSE_AGENT_EDIT_PROMPT, PROSE_AGENT_SYSTEM_PROMPT
from app.agents.tools.prose import calculate_readability_metrics, compare_readability_metrics
from app.caches import EditCache
from app.schemas.chapter import ChapterEditRequest

prose_agent = create_agent(
    "openai:gpt-5-mini",
    tools=[
        calculate_readability_metrics,
        compare_readability_metrics,
    ],
    response_format=ToolStrategy(ChapterEdit),
    system_prompt=PROSE_AGENT_SYSTEM_PROMPT,
)

async def edit_chapter(request: ChapterEditRequest) -> ChapterEdit:
    payload: Any = {
        "messages": [
            {"role": "user", "content": PROSE_AGENT_EDIT_PROMPT.format(raw_text=request.content)}
        ]
    }
    response: Any = await prose_agent.ainvoke(payload)
    structured_response = response["structured_response"]
    return ChapterEdit.model_validate(structured_response)