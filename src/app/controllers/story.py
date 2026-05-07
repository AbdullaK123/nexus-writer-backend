from fastapi import APIRouter, BackgroundTasks, Depends

from src.app.dependencies import (
    get_current_user,
    get_chapter_service,
    get_extraction_service,
    get_story_service,
)
from src.data.schemas import UserRow
from src.data.schemas.story import (
    CreateStoryRequest,
    UpdateStoryRequest,
    StoryGridResponse,
    StoryDetailResponse,
)
from src.data.schemas.chapter import (
    CreateChapterRequest,
    ChapterContentResponse,
    ReorderChapterRequest,
    ChapterListResponse,
)
from src.data.schemas.scene import (
    SceneSearchRequest,
    SceneSearchListResponse,
    VocabularyListResponse,
)
from src.service.chapter import ChapterService
from src.service.extraction import ExtractionService
from src.service.story import StoryService
from src.app.controllers.story_chat import chat_controller


story_controller = APIRouter(prefix="/stories")
story_controller.include_router(chat_controller)


@story_controller.post("")
async def create_story(
    story_info: CreateStoryRequest,
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> dict:
    return await story_service.create_story(current_user.id, story_info)


@story_controller.put("/{story_id}")
async def update_story(
    story_id: str,
    update_info: UpdateStoryRequest,
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> dict:
    return await story_service.update_story(
        current_user.id, story_id, update_info,
    )


@story_controller.delete("/{story_id}")
async def delete_story(
    story_id: str,
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> dict:
    return await story_service.delete_story(current_user.id, story_id)


@story_controller.get("", response_model=StoryGridResponse)
async def get_stories(
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> StoryGridResponse:
    return await story_service.get_all_stories(current_user.id)


@story_controller.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story_details(
    story_id: str,
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> StoryDetailResponse:
    return await story_service.get_story_details(current_user.id, story_id)


@story_controller.post("/{story_id}/chapters", response_model=ChapterContentResponse)
async def create_chapter(
    story_id: str,
    chapter_info: CreateChapterRequest,
    background_tasks: BackgroundTasks,
    current_user: UserRow = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service),
    extraction_service: ExtractionService = Depends(get_extraction_service),
) -> ChapterContentResponse:
    result = await chapter_service.create_chapter(
        story_id, current_user.id, chapter_info,
    )
    background_tasks.add_task(extraction_service.extract_scenes, result.id)
    return result


@story_controller.post("/{story_id}/chapters/reorder")
async def reorder_chapters(
    story_id: str,
    reorder_info: ReorderChapterRequest,
    current_user: UserRow = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service),
) -> dict:
    return await chapter_service.reorder_chapters(
        story_id, current_user.id, reorder_info,
    )


@story_controller.get("/{story_id}/chapters", response_model=ChapterListResponse)
async def get_story_chapters(
    story_id: str,
    current_user: UserRow = Depends(get_current_user),
    chapter_service: ChapterService = Depends(get_chapter_service),
) -> ChapterListResponse:
    return await chapter_service.get_story_chapters(
        story_id, current_user.id,
    )


@story_controller.post(
    "/{story_id}/search", 
    response_model=SceneSearchListResponse,
)
async def search_story_scenes(
    story_id: str,
    search_info: SceneSearchRequest,
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> SceneSearchListResponse:
    results = await story_service.search_story_scenes(
        user_id=current_user.id,
        story_id=story_id,
        query_text=search_info.query,
        k=search_info.k,
        candidate_pool=search_info.candidate_pool,
        tension=search_info.tension,
        pacing=search_info.pacing,
        tags=search_info.tags,
        mentioned_entities=search_info.mentioned_entities,
        chapter_ids=search_info.chapter_ids,
    )
    return SceneSearchListResponse(results=results)


@story_controller.get(
    "/{story_id}/tags",
    response_model=VocabularyListResponse,
)
async def list_story_tags(
    story_id: str,
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> VocabularyListResponse:
    return await story_service.list_story_tags(current_user.id, story_id)


@story_controller.get(
    "/{story_id}/entities",
    response_model=VocabularyListResponse,
)
async def list_story_entities(
    story_id: str,
    current_user: UserRow = Depends(get_current_user),
    story_service: StoryService = Depends(get_story_service),
) -> VocabularyListResponse:
    return await story_service.list_story_entities(current_user.id, story_id)
