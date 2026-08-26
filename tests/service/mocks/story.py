from typing import Sequence
from uuid_extensions import uuid7str

from src.data.schemas.enums import StoryStatus
from src.data.schemas.story import StoryRow

from .common import now


class FakeStoryRepository:
    def __init__(self):
        self._stories: dict[str, StoryRow] = {}
        self._path_arrays: dict[str, list[str]] = {}
        self.error: Exception | None = None
        self.force_update_none: bool = False

    def seed(self, story: StoryRow):
        self._stories[story.id] = story
        self._path_arrays[story.id] = list(story.path_array or [])

    async def get(self, story_id: str, user_id: str, *, executor=None) -> StoryRow | None:
        if self.error:
            raise self.error
        story = self._stories.get(story_id)
        if story and story.user_id == user_id:
            return story
        return None

    async def list_for_user(self, user_id: str) -> list[StoryRow]:
        if self.error:
            raise self.error
        return [s for s in self._stories.values() if s.user_id == user_id]

    async def exists_with_title(self, user_id: str, title: str) -> bool:
        if self.error:
            raise self.error
        return any(s.user_id == user_id and s.title == title for s in self._stories.values())

    async def create(self, *, user_id: str, title: str) -> StoryRow:
        if self.error:
            raise self.error
        story = StoryRow(
            id=uuid7str(),
            user_id=user_id,
            title=title,
            story_context=None,
            status=StoryStatus.ONGOING,
            path_array=[],
            created_at=now(),
            updated_at=now(),
        )
        self.seed(story)
        return story

    async def update(self, *, story_id: str, user_id: str, fields: dict) -> StoryRow | None:
        if self.error:
            raise self.error
        if self.force_update_none:
            return None
        story = await self.get(story_id, user_id)
        if not story:
            return None
        updated = story.model_copy(update={**fields, "updated_at": now()})
        self._stories[story_id] = updated
        return updated

    async def delete(self, *, story_id: str, user_id: str) -> bool:
        if self.error:
            raise self.error
        story = self._stories.get(story_id)
        if story and story.user_id == user_id:
            del self._stories[story_id]
            return True
        return False

    async def set_path_array(self, story_id: str, path: Sequence[str], *, executor=None) -> None:
        if self.error:
            raise self.error
        self._path_arrays[story_id] = list(path)

    async def get_path_array(self, story_id: str, *, executor=None) -> list[str] | None:
        if self.error:
            raise self.error
        if story_id not in self._stories:
            return None
        return self._path_arrays.get(story_id, [])

    async def touch(self, story_id: str, *, executor=None) -> None:
        if self.error:
            raise self.error

    async def get_stats(self, story_id: str, user_id: str, *, executor=None) -> dict:
        if self.error:
            raise self.error
        return {}
