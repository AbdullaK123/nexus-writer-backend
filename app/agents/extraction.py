from typing import Any
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from dotenv import load_dotenv
from app.agents.models.extraction import CharacterExtractionResult
from app.agents.prompts.extraction import *

load_dotenv()

character_extraction_agent = create_agent(
    "openai:gpt-5-mini",
    tools=[],
    system_prompt=CHARACTER_EXTRACTION_SYSTEM_PROMPT,
    response_format=ToolStrategy(CharacterExtractionResult)
)

async def extract_characters(
    chapter_id: str,
    chapter_number: int,
    book_title: str,
    chapter_text: str
) -> CharacterExtractionResult:
    payload: Any = {
        "messages": [
            {"role": "user", "content": CHARACTER_EXTRACTION_PROMPT.format(
                chapter_id=chapter_id,
                chapter_number=chapter_number,
                book_title=book_title,
                chapter_text=chapter_text
            )}
        ]
    }
    response: Any = await character_extraction_agent.ainvoke(payload)
    structured_response = response["structured_response"]
    return CharacterExtractionResult(**structured_response)