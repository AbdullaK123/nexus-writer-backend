from typing import Optional
from app.ai.models.character import CharacterExtraction
from app.ai.models.plot import PlotExtraction
from app.ai.models.structure import StructureExtraction
from app.ai.models.world import WorldExtraction
from app.ai.prompts.context import SYSTEM_PROMPT, build_condensed_context_prompt
from app.ai.models.context import CondensedChapterContext
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware

# Create synthesis agent
synthesis_agent = create_agent(
    "anthropic:claude-haiku-4-5-20251001",
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(CondensedChapterContext),
    middleware=[
        AnthropicPromptCachingMiddleware(ttl="5m", min_messages_to_cache=0)
    ]
)

async def synthesize_chapter_context(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    char_extract: CharacterExtraction,
    plot_extract: PlotExtraction,
    world_extract: WorldExtraction,
    struct_extract: StructureExtraction
) -> CondensedChapterContext:
    
    prompt = build_condensed_context_prompt(
        chapter_id=chapter_id,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        word_count=word_count,
        character_extraction=char_extract.model_dump(),
        plot_extraction=plot_extract.model_dump(),
        world_extraction=world_extract.model_dump(),
        structure_extraction=struct_extract.model_dump()
    )
    
    result = await synthesis_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    })
    
    return result["structured_response"]