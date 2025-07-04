from fastapi import APIRouter, Depends, BackgroundTasks
from app.providers.chapter import ChapterProvider, get_chapter_provider
from app.providers.story import StoryProvider, get_story_provider
from app.core.database import get_db
from sqlmodel.ext.asyncio.session import AsyncSession
from app.providers.auth import get_current_user
from sqlmodel import select
from app.models import User, Story, Chapter
from app.background_jobs.chapter import handle_chapter_deletion
from app.schemas.chapter import (
    ChapterContentResponse,
    UpdateChapterRequest
)

chapter_controller = APIRouter(prefix='/chapters')

@chapter_controller.get('/{chapter_id}', response_model=ChapterContentResponse)
async def get_chapter_with_navigation(
    chapter_id: str,
    as_lexical_json: bool = True,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterContentResponse:
    return await chapter_provider.get_chapter_with_navigation(
        chapter_id, 
        current_user.id, 
        as_lexical_json
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> dict:
    
    story_query = select(Chapter.story_id).where(Chapter.id == chapter_id)

    story_id = (await db.execute(story_query)).scalar_one_or_none()

    background_tasks.add_task(handle_chapter_deletion, story_id, chapter_id)

    return await chapter_provider.delete(
        chapter_id, 
        current_user.id
    )