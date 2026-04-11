from typing import Optional
from src.data.models.ai.character import CharacterExtraction
from src.data.models.ai.plot import PlotExtraction
from src.data.models.ai.structure import StructureExtraction
from src.data.models.ai.world import WorldExtraction
from src.service.ai.prompts.context import SYSTEM_PROMPT, build_condensed_context_prompt
from src.data.models.ai.context import CondensedChapterContext
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from src.infrastructure.config.settings import config
from src.service.ai.utils.model_factory import create_chat_model
from src.infrastructure.utils.retry import retry_llm

model = create_chat_model(config.ai.lite_model)

synthesis_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    response_format=ToolStrategy(CondensedChapterContext),
)

@retry_llm
async def synthesize_chapter_context(
    chapter_id: str,
    chapter_number: int,
    chapter_title: Optional[str],
    word_count: int,
    char_extract: CharacterExtraction,
    plot_extract: PlotExtraction,
    world_extract: WorldExtraction,
    struct_extract: StructureExtraction,
    use_lfm: bool = False,
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
    
    if use_lfm:
        from src.service.ai.utils.extractors import context_extractor
        return await context_extractor.extract(prompt)

    result = await synthesis_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    })
    
    return result["structured_response"]