from typing import Dict, List, Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.plot_thread import PLOT_THREADS_SYSTEM_PROMPT, build_plot_threads_extraction_prompt
from app.ai.models.plot_thread import PlotThreadsExtraction
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware
from dotenv import load_dotenv

load_dotenv()

plot_thread_extraction_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools = [],
    system_prompt=PLOT_THREADS_SYSTEM_PROMPT,
    response_format=ToolStrategy(PlotThreadsExtraction),
    middleware=[
        AnthropicPromptCachingMiddleware(ttl="5m", min_messages_to_cache=0)
    ]
)

async def extract_plot_threads(
    story_context: str,
    plot_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> PlotThreadsExtraction:
    
    result = await plot_thread_extraction_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_plot_threads_extraction_prompt(
                    story_context,
                    plot_extractions,
                    story_title,
                    total_chapters
                )
            }
        ]
    })

    return result["structured_response"]