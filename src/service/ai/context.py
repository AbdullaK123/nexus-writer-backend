from typing import Optional
from src.data.models.ai.character import CharacterExtraction
from src.data.models.ai.plot import PlotExtraction
from src.data.models.ai.structure import StructureExtraction
from src.data.models.ai.world import WorldExtraction
from src.service.ai.prompts.context import SYSTEM_PROMPT, build_condensed_context_prompt
from src.data.models.ai.context import CondensedChapterContext
from langchain.messages import SystemMessage, HumanMessage
from src.infrastructure.config.settings import config
from src.service.ai.utils.model_factory import create_chat_model
from src.service.ai.utils.extractors import context_extractor
from src.infrastructure.utils.retry import retry_llm
from src.shared.utils.decorators import timed_event
from src.shared.utils.logging_context import get_layer_logger, LAYER_SERVICE

log = get_layer_logger(LAYER_SERVICE)

model = create_chat_model(config.ai.lite_model)

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
    
    async with timed_event(log, "ai.context_synthesis", level="INFO", chapter_number=chapter_number, chapter_id=chapter_id):
        result = await context_extractor.extract(prompt)
    return result