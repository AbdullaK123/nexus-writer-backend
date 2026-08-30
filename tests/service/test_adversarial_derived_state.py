from datetime import datetime, timezone

from src.data.schemas.auth import UserResponse
from src.data.schemas.scene import SceneRow
from src.service.story.service import StoryService
from tests.service.mocks import FakeSceneRepository, FakeStoryRepository


def _orphan_scene(*, scene_id: str, story_id: str, user_id: str, position: int) -> SceneRow:
    now = datetime.now(timezone.utc)
    return SceneRow(
        id=scene_id,
        story_id=story_id,
        user_id=user_id,
        chapter_id="chapter-removed-from-path",
        position=position,
        start_quote="start",
        end_quote="end",
        description="stale derived metadata",
        pov="Mara",
        word_count=10,
        tension="medium",
        pacing="steady",
        mentioned_entities=["Mara"],
        tags=["stale"],
        questions_raised=[],
        title="Orphan scene",
        created_at=now,
        updated_at=now,
    )


async def test_stale_scene_rows_cannot_crash_story_context(
    story_service: StoryService,
    test_user: UserResponse,
    fake_story_repo: FakeStoryRepository,
    fake_scene_repo: FakeSceneRepository,
) -> None:
    story = await fake_story_repo.create(
        user_id=test_user.id,
        title="Story",
    )
    await fake_story_repo.set_path_array(story.id, [])

    for position in range(3):
        fake_scene_repo.seed(_orphan_scene(
            scene_id=f"orphan-{position}",
            story_id=story.id,
            user_id=test_user.id,
            position=position,
        ))

    result = await story_service.get_story_context(test_user.id, story.id)

    assert result == "NOT_ENOUGH_CONTEXT", (
        "derived scene rows whose chapter is no longer in canonical story.path_array must be "
        "ignored, never allowed to raise KeyError and turn stale metadata into a 500"
    )
