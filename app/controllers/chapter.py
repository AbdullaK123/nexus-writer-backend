from fastapi import APIRouter, Depends

from app.agents.models import ChapterEditResponse
from app.providers.chapter import ChapterProvider, get_chapter_provider
from app.providers.auth import get_current_user
from app.models import User
from app.schemas.chapter import (
    ChapterContentResponse,
    UpdateChapterRequest, ChapterEditRequest
)

chapter_controller = APIRouter(prefix='/chapters')

@chapter_controller.post('/ai/edit', response_model=ChapterEditResponse)
async def edit_chapter(
    request: ChapterEditRequest,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterEditResponse:
    return await chapter_provider.edit_chapter(
        current_user.id,
        request
    )

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
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterContentResponse:
    return await chapter_provider.update(
        chapter_id,
        current_user.id,
        updated_info
    )

@chapter_controller.delete('/{chapter_id}', response_model=dict)
async def delete_chapter(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> dict:
    return await chapter_provider.delete(
        chapter_id, 
        current_user.id
    )
