from typing import Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.prompts.edits import SYSTEM_PROMPT, build_line_edit_prompt
from app.ai.models.edits import ChapterEdit
from app.config.settings import app_config

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=None,
    max_retries=3,
)

line_edit_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(ChapterEdit),
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