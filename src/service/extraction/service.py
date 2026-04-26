from src.data.models import Chapter, Extraction, ExtractionType
from src.infrastructure.ai import AIProvider, SCENE_EXTRACTION_PROMPT
from src.infrastructure.utils.decorators import retry_extraction
from src.service.exceptions import NotFoundError, ValidationError
from src.service.utils.decorators import handle_service_errors
from src.shared.utils.html import html_to_plain_text
from src.infrastructure.config import config
from src.data.schemas import SceneExtraction


@retry_extraction(ValidationError)
async def _extract_and_validate(
    provider: AIProvider,
    chapter_content: str
) -> SceneExtraction:
    extraction = await provider.extract(
        system_prompt=SCENE_EXTRACTION_PROMPT,
        text=chapter_content,
        max_tokens=config.ai.scene_extraction_max_tokens,
        schema=SceneExtraction,
    )
    for scene in extraction.scenes:
        if scene.start_quote not in chapter_content:
            raise ValidationError(
                fields={"start_quote": scene.start_quote},
                message="Extraction must contain verbatim start quote!",
            )
        if scene.end_quote not in chapter_content:
            raise ValidationError(
                fields={"end_quote": scene.end_quote},
                message="Extraction must contain verbatim end quote!",
            )
    return extraction


@handle_service_errors
async def extract_scenes(
    provider: AIProvider,
    chapter_id: str,
) -> None:
    
    chapter = await Chapter.get_or_none(id=chapter_id)

    if chapter is None:
        raise NotFoundError("Chapter not found")

    chapter_content = html_to_plain_text(chapter.content)

    extraction = await _extract_and_validate(
        provider=provider, 
        chapter_content=chapter_content
    )

    await Extraction.update_or_create(
        defaults={
            "data": extraction.model_dump(),
            "needs_reextraction": False,
        },
        chapter_id=chapter.id,
        extraction_type=ExtractionType.SCENES,
    )


def extraction_is_stale(extraction: SceneExtraction, chapter_content: str) -> bool:
    for scene in extraction.scenes:
        if scene.start_quote not in chapter_content:
            return True
        if scene.end_quote not in chapter_content:
            return True
    return False