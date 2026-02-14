from typing import Dict, List, Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai.prompts.character_bio import CHARACTER_BIO_SYSTEM_PROMPT, build_bios_extraction_prompt
from app.ai.models.character_bio import CharacterBiosExtraction
from dotenv import load_dotenv
from app.config.settings import app_config

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=app_config.ai_temperature,
    max_tokens=app_config.ai_maxtokens,
    timeout=None,
    max_retries = 3
)

character_bios_extraction_agent = create_agent(
    model=model,
    tools = [],
    system_prompt=CHARACTER_BIO_SYSTEM_PROMPT,
    response_format=ToolStrategy(CharacterBiosExtraction),
)

async def extract_character_bios(
    story_context: str,
    character_extractions: List[Dict | None],
    story_title: str,
    total_chapters: int
) -> CharacterBiosExtraction:
    
    result = await character_bios_extraction_agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": build_bios_extraction_prompt(
                    story_context,
                    character_extractions,
                    story_title,
                    total_chapters
                )
            }
        ]
    })

    return result["structured_response"]