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
import time
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

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
    log.info("ai.context_synthesis.start", chapter_number=chapter_number, chapter_id=chapter_id, use_lfm=use_lfm)
    t0 = time.perf_counter()
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
        result = await context_extractor.extract(prompt)
        elapsed = round(time.perf_counter() - t0, 2)
        log.info("ai.context_synthesis.complete", chapter_number=chapter_number, elapsed_s=elapsed, path="lfm")
        return result

    result = await synthesis_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    })
    elapsed = round(time.perf_counter() - t0, 2)
    log.info("ai.context_synthesis.complete", chapter_number=chapter_number, elapsed_s=elapsed, path="agent")
    
    return result["structured_response"]