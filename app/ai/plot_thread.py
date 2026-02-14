from typing import Dict, List, Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.prompts.plot_thread import PLOT_THREADS_SYSTEM_PROMPT, build_plot_threads_extraction_prompt
from app.ai.models.plot_thread import PlotThreadsExtraction
from app.config.settings import app_config

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=None,
    max_retries=3,
)

plot_thread_extraction_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=PLOT_THREADS_SYSTEM_PROMPT,
    response_format=ToolStrategy(PlotThreadsExtraction),
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