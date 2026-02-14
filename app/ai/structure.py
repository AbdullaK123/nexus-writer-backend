from typing import Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.prompts.structure import SYSTEM_PROMPT, build_structure_extraction_prompt
from app.ai.models.structure import StructureExtraction
from app.config.settings import app_config

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=None,
    max_retries=3,
)

story_structure_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(StructureExtraction),
)

async def extract_story_structure(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> StructureExtraction:
    
    result = await story_structure_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_structure_extraction_prompt(
                    story_context, 
                    current_chapter_content, 
                    chapter_number, 
                    chapter_title
                )
            }
        ]
    })

    return result["structured_response"]