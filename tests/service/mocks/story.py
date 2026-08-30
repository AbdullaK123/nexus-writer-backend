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

    def _store_path(self, story_id: str, path: Sequence[str]) -> list[str]:
        stored = list(path)
        self._path_arrays[story_id] = stored

        story = self._stories.get(story_id)
        if story is not None:
            self._stories[story_id] = story.model_copy(
                update={
                    "path_array": stored,
                    "updated_at": now(),
                }
            )

        return list(stored)

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
        if "path_array" in fields:
            self._path_arrays[story_id] = list(updated.path_array or [])
        return updated

    async def delete(self, *, story_id: str, user_id: str) -> bool:
        if self.error:
            raise self.error
        story = self._stories.get(story_id)
        if story and story.user_id == user_id:
            del self._stories[story_id]
            self._path_arrays.pop(story_id, None)
            return True
        return False

    async def set_path_array(self, story_id: str, path: Sequence[str], *, executor=None) -> None:
        if self.error:
            raise self.error
        self._store_path(story_id, path)

    async def get_path_array(self, story_id: str, *, executor=None) -> list[str] | None:
        if self.error:
            raise self.error
        if story_id not in self._stories:
            return None
        return list(self._path_arrays.get(story_id, []))

    async def append_chapter_to_path(
        self,
        story_id: str,
        chapter_id: str,
        *,
        executor=None,
    ) -> list[str]:
        if self.error:
            raise self.error
        path = list(self._path_arrays.get(story_id, []))
        path.append(chapter_id)
        return self._store_path(story_id, path)

    async def remove_chapter_from_path(
        self,
        story_id: str,
        chapter_id: str,
        *,
        executor=None,
    ) -> list[str]:
        if self.error:
            raise self.error
        path = list(self._path_arrays.get(story_id, []))
        path.remove(chapter_id)
        return self._store_path(story_id, path)

    async def reorder_chapter_path(
        self,
        story_id: str,
        from_pos: int,
        to_pos: int,
        *,
        executor=None,
    ) -> list[str]:
        if self.error:
            raise self.error
        path = list(self._path_arrays.get(story_id, []))
        chapter_id = path.pop(from_pos)
        path.insert(to_pos, chapter_id)
        return self._store_path(story_id, path)

    async def touch(self, story_id: str, *, executor=None) -> None:
        if self.error:
            raise self.error

    async def get_stats(self, story_id: str, user_id: str, *, executor=None) -> dict:
        if self.error:
            raise self.error
        return {}
