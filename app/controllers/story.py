from fastapi import APIRouter, Depends, BackgroundTasks
from app.providers.story import StoryProvider, get_story_provider
from app.providers.chapter import ChapterProvider, get_chapter_provider
from app.providers.auth import get_current_user
from app.models import User
from app.schemas.story import CreateStoryRequest, UpdateStoryRequest, StoryGridResponse, StoryDetailResponse
from app.schemas.chapter import CreateChapterRequest, ChapterContentResponse, ReorderChapterRequest, ChapterListResponse
from app.background_jobs.chapter import handle_chapter_creation, handle_chapter_deletion, handle_chapter_reordering

story_controller = APIRouter(prefix='/stories')

@story_controller.post('/', response_model=dict)
async def create_story(
    story_info: CreateStoryRequest,
    current_user: User = Depends(get_current_user),
    story_provider: StoryProvider = Depends(get_story_provider)
) -> dict:
    return await story_provider.create(current_user.id, story_info)

@story_controller.put('/{story_id}', response_model=dict)
async def update_story(
    story_id: str,
    update_info: UpdateStoryRequest,
    current_user: User = Depends(get_current_user),
    story_provider: StoryProvider = Depends(get_story_provider)
) -> dict:
    return await story_provider.update(current_user.id, story_id, update_info)

@story_controller.delete('/{story_id}', response_model=dict)
async def delete_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    story_provider: StoryProvider = Depends(get_story_provider)
) -> dict:
    return await story_provider.delete(current_user.id, story_id)

@story_controller.get('/', response_model=StoryGridResponse)
async def get_stories(
    current_user: User = Depends(get_current_user),
    story_provider: StoryProvider = Depends(get_story_provider)
) -> StoryGridResponse:
    return await story_provider.get_all_stories(current_user.id)

@story_controller.get('/{story_id}', response_model=StoryDetailResponse)
async def get_story_details(
    story_id: str,
    current_user: User = Depends(get_current_user),
    story_provider: StoryProvider = Depends(get_story_provider)
) -> StoryDetailResponse:
    return await story_provider.get_story_details(current_user.id, story_id)

@story_controller.post('/{story_id}/chapters', response_model=ChapterContentResponse)
async def create_chapter(
    story_id: str,
    chapter_info: CreateChapterRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterContentResponse:
    
    # Create the chapter first
    chapter = await chapter_provider.create(
        story_id,
        current_user.id,
        chapter_info
    )
    
    # Pass the actual chapter ID to background task
    background_tasks.add_task(handle_chapter_creation, story_id, chapter.id)
    
    return chapter

@story_controller.post('/{story_id}/chapters/reorder', response_model=dict)
async def reorder_chapters(
    story_id: str,
    reorder_info: ReorderChapterRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> dict:
    background_tasks.add_task(
        handle_chapter_reordering, 
        story_id, 
        reorder_info.from_pos, 
        reorder_info.to_pos
    )
    return await chapter_provider.reorder_chapters(
        story_id,
        current_user.id,
        reorder_info,
        background_tasks
    )

@story_controller.get('/{story_id}/chapters', response_model=ChapterListResponse)
async def get_story_chapters(
    story_id: str,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterListResponse:
    return await chapter_provider.get_story_chapters(story_id, current_user.id)