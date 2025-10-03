from fastapi import APIRouter, Depends, Query
from app.providers.story import StoryProvider, get_story_provider
from app.providers.chapter import ChapterProvider, get_chapter_provider
from app.providers.auth import get_current_user
from app.models import User
from app.schemas.analytics import StoryAnalyticsResponse
from app.schemas.story import CreateStoryRequest, UpdateStoryRequest, StoryGridResponse, StoryDetailResponse
from app.schemas.chapter import CreateChapterRequest, ChapterContentResponse, ReorderChapterRequest, ChapterListResponse
from app.providers.analytics import get_analytics_provider, AnalyticsProvider
from app.providers.target import TargetProvider, get_target_provider
from app.schemas.target import TargetResponse, CreateTargetRequest, UpdateTargetRequest
from app.models import FrequencyType
from datetime import datetime
from typing import List, Dict, Any, Optional


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


@story_controller.get('/{story_id}/analytics', response_model=StoryAnalyticsResponse)
async def get_story_analytics(
    story_id: str,
    frequency: FrequencyType = Query(),
    from_date: datetime = Query(),
    to_date: datetime = Query(),
    current_user: User = Depends(get_current_user),
    analytics_provider: AnalyticsProvider = Depends(get_analytics_provider),
    target_provider: TargetProvider = Depends(get_target_provider)
) -> List[Dict[str, Any]]:
    kpis = analytics_provider.get_writing_kpis(
        story_id=story_id,
        user_id=current_user.id,
        frequency=frequency
    )
    words_over_time = analytics_provider.get_writing_output_over_time(
        story_id=story_id,
        user_id=current_user.id,
        frequency=frequency,
        from_date=from_date,
        to_date=to_date
    )
    target = await target_provider.get_target_by_story_id_and_frequency(
        story_id,
        current_user.id,
        frequency
    )
    return StoryAnalyticsResponse(
        kpis=kpis,
        words_over_time=words_over_time,
        target=target
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

@story_controller.get('/{story_id}/targets', response_model=Optional[TargetResponse])
async def get_target(
    story_id: str,
    frequency: FrequencyType = Query(),
    current_user: User = Depends(get_current_user),
    target_provider: TargetProvider = Depends(get_target_provider)
) -> Optional[TargetResponse]:
    return await target_provider.get_target_by_story_id_and_frequency(
        story_id,
        current_user.id,
        frequency
    )

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