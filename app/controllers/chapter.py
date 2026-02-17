from fastapi import APIRouter, Depends, BackgroundTasks
from app.services.chapter import ChapterService, get_chapter_service
from app.services.auth import get_current_user
from app.models import User
from app.ai.models.edits import ChapterEdit, ChapterEditResponse
from typing import Optional
from app.schemas.chapter import (
    ChapterContentResponse,
    UpdateChapterRequest
)

chapter_controller = APIRouter(prefix='/chapters')

@chapter_controller.get('/edit/{chapter_id}', response_model=ChapterEditResponse)
async def get_chapter_edits(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> ChapterEditResponse:
    return await chapter_service.get_line_edits(
        current_user.id,
        chapter_id
    )

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
    updated_info: UpdateChapterRequest,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> ChapterContentResponse:
    return await chapter_service.update(
        chapter_id=chapter_id,
        user_id=current_user.id,
        data=updated_info
    )

@chapter_controller.delete('/{chapter_id}', response_model=dict)
async def delete_chapter(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> dict:
    return await chapter_service.delete(
        chapter_id=chapter_id,
        user_id=current_user.id
    )
