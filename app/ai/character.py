# app/ai/character.py
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.prompts.character import SYSTEM_PROMPT, build_character_extraction_prompt
from app.ai.models.character import CharacterExtraction
from typing import Optional
from app.config.settings import app_config

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=app_config.ai_sdk_timeout,
    max_retries=app_config.ai_sdk_retries,
)

character_extraction_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(CharacterExtraction),
)

async def extract_characters(
    story_context: str,
    current_chapter_content: str,
    chapter_number: int,
    chapter_title: Optional[str] = None
) -> CharacterExtraction:
    
    result = await character_extraction_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": build_character_extraction_prompt(
                story_context, current_chapter_content, 
                chapter_number, chapter_title
            )
        }]
    })
    return result["structured_response"]