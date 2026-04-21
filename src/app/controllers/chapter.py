from fastapi import APIRouter, Depends
from src.service.chapter.service import ChapterService
from src.app.dependencies import get_current_user, get_chapter_service
from src.data.models import User
from src.data.schemas.chapter import ChapterContentResponse, UpdateChapterRequest

chapter_controller = APIRouter(prefix="/chapters")


@chapter_controller.get("/{chapter_id}", response_model=ChapterContentResponse)
async def get_chapter_with_navigation(
    chapter_id: str,
    as_html: bool = True,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service),
) -> ChapterContentResponse:
    return await chapter_service.get_chapter_with_navigation(
        chapter_id, current_user.id, as_html
    )


@chapter_controller.put("/{chapter_id}", response_model=ChapterContentResponse)
async def update_chapter(
    chapter_id: str,
    updated_info: UpdateChapterRequest,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service),
) -> ChapterContentResponse:
    return await chapter_service.update(
        chapter_id=chapter_id, user_id=current_user.id, data=updated_info
    )


@chapter_controller.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service),
) -> dict:
    return await chapter_service.delete(
        chapter_id=chapter_id,
        user_id=current_user.id,
    )
