from typing import Dict, List, Optional
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from app.ai.prompts.character_bio import CHARACTER_BIO_SYSTEM_PROMPT, build_bios_extraction_prompt
from app.ai.models.character_bio import CharacterBiosExtraction
from dotenv import load_dotenv

load_dotenv()

character_bios_extraction_agent = create_agent(
    "google_genai:gemini-2.5-flash-lite",
    tools = [],
    system_prompt=CHARACTER_BIO_SYSTEM_PROMPT,
    response_format=ToolStrategy(CharacterBiosExtraction)
)

async def extract_characters(
    story_context: str,
    character_extractions: List[Dict],
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