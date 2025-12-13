from typing import Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.edits import SYSTEM_PROMPT, build_line_edit_prompt
from app.ai.models.edits import ChapterEdit
from dotenv import load_dotenv

load_dotenv()

line_edit_agent = create_agent(
    "google_genai:gemini-2.5-flash-lite",
    tools = [],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(ChapterEdit)
)

async def generate_line_edits(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> ChapterEdit:
    
    result = await line_edit_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_line_edit_prompt(
                    story_context, 
                    current_chapter_content, 
                    chapter_number, 
                    chapter_title
                )
            }
        ]
    })

    return result["structured_response"]