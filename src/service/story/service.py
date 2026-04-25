from typing import List
from loguru import logger
from src.data.models import Story, Chapter
from src.data.schemas.chapter import ChapterListItem
from src.service.exceptions import NotFoundError, ConflictError
from src.service.utils.decorators import handle_service_errors
from src.data.schemas.story import (
    CreateStoryRequest,
    UpdateStoryRequest,
    StoryCardResponse,
    StoryDetailResponse,
    StoryGridResponse,
)



@handle_service_errors
async def create(user_id: str, story_info: CreateStoryRequest) -> dict:
    story = await Story.filter(user_id=user_id, title=story_info.title).first()

    if story:
        logger.warning("story.create.conflict", user_id=user_id, title=story_info.title)
        raise ConflictError(
            "You already have a story with this title. Please choose a different one."
        )

    await Story.create(user_id=user_id, title=story_info.title, path_array=[])
    logger.info("story.create.done", user_id=user_id, title=story_info.title)

    return {"message": "Story successfully created"}


@handle_service_errors
async def update(
    user_id: str, story_id: str, update_info: UpdateStoryRequest
) -> dict:
    story = await Story.filter(user_id=user_id, id=story_id).first()

    if not story:
        raise NotFoundError("We couldn't find this story. It may have been deleted.")

    update_data = update_info.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(story, field, value)

    await story.save(update_fields=list(update_data.keys()))
    logger.info(
        "story.update.done",
        user_id=user_id,
        story_id=story_id,
        fields=list(update_data.keys()),
    )

    return {"message": "Story successfully updated"}


@handle_service_errors
async def delete(user_id: str, story_id: str) -> dict:
    story = await Story.filter(user_id=user_id, id=story_id).first()

    if not story:
        raise NotFoundError("We couldn't find this story. It may have been deleted.")

    await story.delete()
    logger.info("story.delete.done", user_id=user_id, story_id=story_id)

    return {"message": "Story successfully deleted"}


@handle_service_errors
async def get_ordered_chapters(user_id: str, story_id: str) -> List[Chapter]:
    story = await Story.filter(user_id=user_id, id=story_id).first()

    if not story:
        raise NotFoundError("Story not found")

    all_chapters = await Chapter.filter(
        user_id=user_id, story_id=story_id
    ).prefetch_related("story")

    if not story.path_array:
        return sorted(all_chapters, key=lambda c: c.created_at, reverse=True)

    chapter_lookup = {chapter.id: chapter for chapter in all_chapters}

    ordered_chapters = []
    for chapter_id in story.path_array:
        if chapter_id in chapter_lookup:
            ordered_chapters.append(chapter_lookup[chapter_id])

    return ordered_chapters


@handle_service_errors
async def get_story_details(user_id: str, story_id: str) -> StoryDetailResponse:
    chapters = await get_ordered_chapters(user_id, story_id)

    story = await Story.filter(user_id=user_id, id=story_id).first()

    if not story:
        raise NotFoundError("A story with that title does not exist")

    chapter_items = [
        ChapterListItem.model_validate(chapter) for chapter in chapters
    ] if chapters else []

    return StoryDetailResponse.from_story(story, chapter_items)


@handle_service_errors
async def get_all_stories(user_id: str) -> StoryGridResponse:
    stories = await Story.filter(user_id=user_id).order_by("-created_at")

    story_ids = [story.id for story in stories]
    all_chapters = await Chapter.filter(story_id__in=story_ids)

    chapters: dict[str, list[Chapter]] = {}
    for chapter in all_chapters:
        chapters.setdefault(chapter.story_id, []).append(chapter)

    story_cards = [
        StoryCardResponse.from_story(story, chapters.get(story.id, []))
        for story in stories
    ]

    return StoryGridResponse(stories=story_cards)
