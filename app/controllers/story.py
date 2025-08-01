from fastapi import APIRouter, Depends
from app.providers.story import StoryProvider, get_story_provider
from app.providers.chapter import ChapterProvider, get_chapter_provider
from app.providers.auth import get_current_user
from app.models import User
from app.schemas.story import CreateStoryRequest, UpdateStoryRequest, StoryGridResponse, StoryDetailResponse
from app.schemas.chapter import CreateChapterRequest, ChapterContentResponse, ReorderChapterRequest, ChapterListResponse

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
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterContentResponse:
    return await chapter_provider.create(
        story_id,
        current_user.id,
        chapter_info
    )

@story_controller.post('/{story_id}/chapters/reorder', response_model=dict)
async def reorder_chapters(
    story_id: str,
    reorder_info: ReorderChapterRequest,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> dict:
    return await chapter_provider.reorder_chapters(
        story_id,
        current_user.id,
        reorder_info
    )

@story_controller.get('/{story_id}/chapters', response_model=ChapterListResponse)
async def get_story_chapters(
    story_id: str,
    current_user: User = Depends(get_current_user),
    chapter_provider: ChapterProvider = Depends(get_chapter_provider)
) -> ChapterListResponse:
    return await chapter_provider.get_story_chapters(story_id, current_user.id)