from typing import Tuple
from loguru import logger
from src.data.models import Chapter, Story, Extraction
from src.data.schemas import (
    CreateChapterRequest,
    UpdateChapterRequest,
    ReorderChapterRequest,
    ChapterListItem,
    ChapterContentResponse,
    ChapterListResponse,
    SceneExtraction
)
from src.service.exceptions import NotFoundError, ValidationError, InternalError
from src.shared.utils.html import get_preview_content, get_word_count, html_to_plain_text
from src.service.chapter.utils import (
    handle_chapter_creation,
    handle_chapter_deletion,
    handle_chapter_reordering,
)
from src.data.utils.decorators import transaction
from src.service.utils.decorators import handle_service_errors
from src.service.extraction import extraction_is_stale

@handle_service_errors
async def get_chapter_with_navigation(
    chapter_id: str, user_id: str, as_html: bool = True
) -> ChapterContentResponse:
    chapter = (
        await Chapter.filter(id=chapter_id, user_id=user_id)
        .prefetch_related("story")
        .first()
    )

    if not chapter:
        raise NotFoundError(
            "We couldn't find this chapter. It may have been deleted."
        )

    return ChapterContentResponse.from_chapter(
        chapter,
        content=chapter.content if as_html else get_preview_content(chapter.content),
    )


@handle_service_errors
@transaction
async def create(
    story_id: str,
    user_id: str,
    data: CreateChapterRequest,
) -> ChapterContentResponse:
    story = await Story.get_or_none(id=story_id)
    if not story:
        raise NotFoundError("We couldn't find this story. It may have been deleted.")

    try:
        chapter_to_create = await Chapter.create(
            story_id=story_id,
            user_id=user_id,
            title=data.title,
            content=data.content,
            word_count=get_word_count(data.content) if data.content else 0,
        )

        await handle_chapter_creation(story_id, chapter_to_create.id)
        logger.info(
            "chapter.create.done",
            story_id=story_id,
            chapter_id=chapter_to_create.id,
            user_id=user_id,
        )

        return await get_chapter_with_navigation(
            chapter_to_create.id, user_id, as_html=True
        )

    except (NotFoundError, ValidationError, InternalError):
        raise
    except Exception as e:
        logger.error(
            "chapter.create_failed",
            story_id=story_id,
            user_id=user_id,
            error=str(e),
        )
        raise InternalError(
            "Something went wrong while creating your chapter. Please try again."
        )


@handle_service_errors
@transaction
async def update(
    chapter_id: str, user_id: str, data: UpdateChapterRequest
) -> ChapterContentResponse:
    chapter = (
        await Chapter.filter(id=chapter_id, user_id=user_id)
        .prefetch_related("story")
        .first()
    )

    if not chapter:
        raise NotFoundError(
            "We couldn't find this chapter. It may have been deleted."
        )

    updated_data = data.model_dump(exclude_unset=True)

    if "content" in updated_data:

        updated_data["word_count"] = get_word_count(updated_data["content"])
        
        extraction_raw = await Extraction.filter(chapter_id=chapter_id).first()

        if extraction_raw:

            extraction_data = SceneExtraction(**extraction_raw.data)

            updated_chapter_content = html_to_plain_text(updated_data["content"])

            if extraction_is_stale(extraction_data, updated_chapter_content):
                extraction_raw.needs_reextraction = True
                await extraction_raw.save(update_fields=["needs_reextraction"])



    for field, value in updated_data.items():
        setattr(chapter, field, value)

    await chapter.save(update_fields=list(updated_data.keys()))

    logger.info(
        "chapter.update.done",
        chapter_id=chapter_id,
        user_id=user_id,
        fields=list(updated_data.keys()),
    )

    return ChapterContentResponse.from_chapter(chapter)


@handle_service_errors
@transaction
async def delete(chapter_id: str, user_id: str) -> dict:
    chapter = await Chapter.filter(user_id=user_id, id=chapter_id).first()
    if not chapter:
        raise NotFoundError(
            "We couldn't find this chapter. It may have been deleted."
        )

    story_id = chapter.story_id
    await chapter.delete()
    await handle_chapter_deletion(story_id, chapter_id)
    logger.info(
        "chapter.delete.done",
        chapter_id=chapter_id,
        user_id=user_id,
        story_id=story_id,
    )

    return {"message": "Chapter was successfully deleted"}


@handle_service_errors
async def get_story_chapters(
    story_id: str, user_id: str
) -> ChapterListResponse:
    story = await Story.filter(id=story_id, user_id=user_id).first()
    if not story:
        raise NotFoundError("We couldn't find this story. It may have been deleted.")

    chapters = await Chapter.filter(story_id=story_id, user_id=user_id)

    if not story.path_array or not chapters:
        return ChapterListResponse.from_story(story, [])

    chapters_lookup = {chapter.id: chapter for chapter in chapters}
    list_items = [
        ChapterListItem.model_validate(chapters_lookup[chapter_id])
        for chapter_id in story.path_array
        if chapter_id in chapters_lookup
    ]

    return ChapterListResponse.from_story(story, list_items)


@handle_service_errors
@transaction
async def reorder_chapters(
    story_id: str,
    user_id: str,
    data: ReorderChapterRequest,
) -> dict:
    story = await Story.filter(id=story_id, user_id=user_id).first()
    if not story:
        raise NotFoundError("We couldn't find this story. It may have been deleted.")

    if not story.path_array:
        raise ValidationError(message="This story has no chapters to reorder.")

    max_pos = len(story.path_array) - 1

    if data.from_pos < 0 or data.from_pos > max_pos:
        raise ValidationError(
            message=f"Invalid chapter position. Must be between 0 and {max_pos}."
        )

    if data.to_pos < 0 or data.to_pos > max_pos:
        raise ValidationError(
            message=f"Invalid target position. Must be between 0 and {max_pos}."
        )

    if data.from_pos == data.to_pos:
        return {"message": "No reordering needed"}

    try:
        await handle_chapter_reordering(story_id, data.from_pos, data.to_pos)
        logger.info(
            "chapter.reorder.done",
            story_id=story_id,
            user_id=user_id,
            from_pos=data.from_pos,
            to_pos=data.to_pos,
        )
        return {"message": "Chapters reordered successfully"}
    except Exception as e:
        logger.error(
            "chapter.reorder_failed",
            story_id=story_id,
            user_id=user_id,
            error=str(e),
        )
        raise InternalError(
            "Something went wrong while reordering your chapters. Please try again."
        )
