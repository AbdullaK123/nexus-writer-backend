from typing import Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.plot import SYSTEM_PROMPT, build_plot_extraction_prompt
from app.ai.models.plot import PlotExtraction
from dotenv import load_dotenv

load_dotenv()

plot_extraction_agent = create_agent(
    "google_genai:gemini-2.5-flash-lite",
    tools = [],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(PlotExtraction),
)

async def extract_plot_information(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> PlotExtraction:
    
    result = await plot_extraction_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_plot_extraction_prompt(
                    story_context, 
                    current_chapter_content, 
                    chapter_number, 
                    chapter_title
                )
            }
        ]
    })

    return result["structured_response"]