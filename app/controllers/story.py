from fastapi import APIRouter, Depends, Query
from app.providers.story import StoryProvider, get_story_provider
from app.providers.chapter import ChapterProvider, get_chapter_provider
from app.providers.auth import get_current_user
from app.models import User
from app.schemas.analytics import StoryAnalyticsResponse
from app.schemas.story import CreateStoryRequest, StoryListItemResponse, UpdateStoryRequest, StoryGridResponse, StoryDetailResponse
from app.schemas.chapter import CreateChapterRequest, ChapterContentResponse, ReorderChapterRequest, ChapterListResponse
from app.providers.analytics import get_analytics_provider, AnalyticsProvider
from app.providers.target import TargetProvider, get_target_provider
from app.schemas.target import TargetResponse, CreateTargetRequest, UpdateTargetRequest, TargetListResponse
from app.models import FrequencyType
from typing import List, Optional
from datetime import datetime, timedelta


story_controller = APIRouter(prefix='/stories')

@story_controller.get('/targets', response_model=List[StoryListItemResponse])
async def get_stories_with_targets(
    current_user: User = Depends(get_current_user),
    story_provider: StoryProvider = Depends(get_story_provider)
) -> List[StoryListItemResponse]:
    return await story_provider.get_all_story_list_items(current_user.id)

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


@story_controller.get('/{story_id}/analytics', response_model=StoryAnalyticsResponse)
async def get_story_analytics(
    story_id: str,
    frequency: FrequencyType = Query(default=FrequencyType.DAILY),
    from_date: datetime = Query(default_factory=lambda:datetime.now() - timedelta(days=30)),
    to_date: datetime = Query(default_factory=datetime.now),
    current_user: User = Depends(get_current_user),
    analytics_provider: AnalyticsProvider = Depends(get_analytics_provider)
) -> StoryAnalyticsResponse:
    return await analytics_provider.get_story_analytics(
        story_id,
        current_user.id,
        frequency,
        from_date,
        to_date
    )

@story_controller.post('/{story_id}/targets', response_model=TargetResponse)
async def create_target(
    story_id: str,
    payload: CreateTargetRequest,
    current_user: User = Depends(get_current_user),
    target_provider: TargetProvider = Depends(get_target_provider)
) -> TargetResponse:
    return await target_provider.create_target(
        story_id,
        current_user.id,
        payload
    )

@story_controller.get('/{story_id}/targets')
async def get_targets(
    story_id: str,
    frequency: Optional[FrequencyType] = Query(default=None),
    current_user: User = Depends(get_current_user),
    target_provider: TargetProvider = Depends(get_target_provider)
):
    """
    Get targets for a story.
    - If frequency is provided, returns a single target (or null)
    - If frequency is not provided, returns all targets for the story
    """
    if frequency:
        return await target_provider.get_target_by_story_id_and_frequency(
            story_id,
            current_user.id,
            frequency
        )
    else:
        targets = await target_provider.get_all_targets_by_story_id(
            story_id,
            current_user.id
        )
        return TargetListResponse(targets=targets)

@story_controller.put('/{story_id}/targets/{target_id}', response_model=TargetResponse)
async def update_target(
    story_id: str,
    target_id: str,
    payload: UpdateTargetRequest,
    current_user: User = Depends(get_current_user),
    target_provider: TargetProvider = Depends(get_target_provider)
) -> TargetResponse:
    return await target_provider.update_target(
        story_id,
        target_id,
        current_user.id,
        payload
    )

@story_controller.delete('/{story_id}/targets/{target_id}')
async def delete_target(
    story_id: str,
    target_id: str,
    current_user: User = Depends(get_current_user),
    target_provider: TargetProvider = Depends(get_target_provider)
) -> dict:
    return await target_provider.delete_target(
        story_id,
        current_user.id,
        target_id
    )