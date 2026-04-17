from fastapi import APIRouter, Depends, Query, BackgroundTasks
from src.service.story.service import StoryService
from src.service.chapter.service import ChapterService
from src.app.dependencies import get_current_user, get_story_service, get_chapter_service, get_analytics_service
from src.data.models import User, FrequencyType
from src.data.schemas.analytics import StoryAnalyticsResponse
from src.data.schemas.story import CreateStoryRequest, StoryListItemResponse, UpdateStoryRequest, StoryGridResponse, StoryDetailResponse
from src.data.schemas.chapter import CreateChapterRequest, ChapterContentResponse, ReorderChapterRequest, ChapterListResponse
from src.service.analytics.service import AnalyticsService
from src.app.controllers.story_targets import router as targets_router
from src.app.controllers.story_plot import router as plot_router
from src.app.controllers.story_characters import router as characters_router
from src.app.controllers.story_structure import router as structure_router
from src.app.controllers.story_world import router as world_router
from typing import List
from datetime import datetime, timedelta, timezone


story_controller = APIRouter(prefix='/stories')

story_controller.include_router(targets_router, prefix="/{story_id}/targets", tags=["targets"])
story_controller.include_router(plot_router, prefix="/{story_id}/plot", tags=["plot"])
story_controller.include_router(characters_router, prefix="/{story_id}/characters", tags=["characters"])
story_controller.include_router(structure_router, prefix="/{story_id}/structure", tags=["structure"])
story_controller.include_router(world_router, prefix="/{story_id}/world", tags=["world"])

@story_controller.get('/targets', response_model=List[StoryListItemResponse])
async def get_stories_with_targets(
    current_user: User = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service)
) -> List[StoryListItemResponse]:
    return await story_service.get_all_story_list_items(current_user.id)

@story_controller.post('/', response_model=dict)
async def create_story(
    story_info: CreateStoryRequest,
    current_user: User = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service)
) -> dict:
    return await story_service.create(current_user.id, story_info)

@story_controller.put('/{story_id}', response_model=dict)
async def update_story(
    story_id: str,
    update_info: UpdateStoryRequest,
    current_user: User = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service)
) -> dict:
    return await story_service.update(current_user.id, story_id, update_info)

@story_controller.delete('/{story_id}', response_model=dict)
async def delete_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service)
) -> dict:
    return await story_service.delete(current_user.id, story_id)

@story_controller.get('/', response_model=StoryGridResponse)
async def get_stories(
    current_user: User = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service)
) -> StoryGridResponse:
    return await story_service.get_all_stories(current_user.id)

@story_controller.get('/{story_id}', response_model=StoryDetailResponse)
async def get_story_details(
    story_id: str,
    current_user: User = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service)
) -> StoryDetailResponse:
    return await story_service.get_story_details(current_user.id, story_id)

@story_controller.post('/{story_id}/chapters', response_model=ChapterContentResponse)
async def create_chapter(
    story_id: str,
    chapter_info: CreateChapterRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> ChapterContentResponse:
    return await chapter_service.create(
        story_id,
        current_user.id,
        chapter_info,
        background_tasks
    )

@story_controller.post('/{story_id}/chapters/reorder', response_model=dict)
async def reorder_chapters(
    story_id: str,
    reorder_info: ReorderChapterRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> dict:
    return await chapter_service.reorder_chapters(
        story_id,
        current_user.id,
        reorder_info,
        background_tasks
    )

@story_controller.get('/{story_id}/chapters', response_model=ChapterListResponse)
async def get_story_chapters(
    story_id: str,
    current_user: User = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service)
) -> ChapterListResponse:
    return await chapter_service.get_story_chapters(story_id, current_user.id)


@story_controller.get('/{story_id}/analytics', response_model=StoryAnalyticsResponse)
async def get_story_analytics(
    story_id: str,
    frequency: FrequencyType = Query(default=FrequencyType.DAILY),
    from_date: datetime = Query(default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=30)),
    to_date: datetime = Query(default_factory=lambda: datetime.now(timezone.utc)),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> StoryAnalyticsResponse:
    return await analytics_service.get_story_analytics(
        story_id,
        current_user.id,
        frequency,
        from_date,
        to_date
    )

