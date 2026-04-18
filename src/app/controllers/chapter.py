from fastapi import APIRouter, BackgroundTasks, Depends
from src.service.ai.summarization import mark_summaries_stale
from src.service.chapter.service import ChapterService
from src.app.dependencies import get_current_user, get_chapter_service
from src.data.models import User
from src.data.schemas.chapter import (
    ChapterContentResponse,
    UpdateChapterRequest
)

chapter_controller = APIRouter(prefix='/chapters')

@chapter_controller.get('/{chapter_id}', response_model=ChapterContentResponse)
async def get_chapter_with_navigation(
    chapter_id: str,
    as_html: bool = True,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> ChapterContentResponse:
    return await chapter_service.get_chapter_with_navigation(
        chapter_id, 
        current_user.id, 
        as_html
    )

@chapter_controller.put('/{chapter_id}', response_model=ChapterContentResponse)
async def update_chapter(
    chapter_id: str,
    background_tasks: BackgroundTasks,
    updated_info: UpdateChapterRequest,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> ChapterContentResponse:
    story_id, result =  await chapter_service.update(
        chapter_id=chapter_id,
        user_id=current_user.id,
        data=updated_info
    )
    if updated_info.content is not None:
        background_tasks.add_task(
            mark_summaries_stale,
            story_id=story_id,
            starting_chapter_id=chapter_id
        )
    return result

@chapter_controller.delete('/{chapter_id}')
async def delete_chapter(
    chapter_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service),
) -> dict:
    story_id, next_chapter_id, result = await chapter_service.delete(
        chapter_id=chapter_id, 
        user_id=current_user.id,
    )
    if next_chapter_id:
        background_tasks.add_task(
            mark_summaries_stale,
            story_id=story_id,
            starting_chapter_id=next_chapter_id,
        )
    return result
