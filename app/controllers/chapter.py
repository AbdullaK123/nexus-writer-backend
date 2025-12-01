from fastapi import APIRouter, Depends, BackgroundTasks
from app.providers.chapter import ChapterProvider, get_chapter_provider
from app.providers.auth import get_current_user
from app.models import User
from app.schemas.chapter import (
    ChapterContentResponse,
    UpdateChapterRequest
)

chapter_controller = APIRouter(prefix='/chapters')

@chapter_controller.get('/{chapter_id}', response_model=ChapterContentResponse)
async def get_chapter_with_navigation(
    chapter_id: str,
    as_html: bool = True,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterContentResponse:
    return await chapter_provider.get_chapter_with_navigation(
        chapter_id, 
        current_user.id, 
        as_html
    )

@chapter_controller.put('/{chapter_id}', response_model=ChapterContentResponse)
async def update_chapter(
    chapter_id: str,
    updated_info: UpdateChapterRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterContentResponse:
    return await chapter_provider.update(
        chapter_id=chapter_id,
        user_id=current_user.id,
        data=updated_info,
        background_tasks=background_tasks
    )

@chapter_controller.delete('/{chapter_id}', response_model=dict)
async def delete_chapter(
    chapter_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> dict:
    return await chapter_provider.delete(
        chapter_id=chapter_id,
        background_tasks=background_tasks,
        user_id=current_user.id
    )
