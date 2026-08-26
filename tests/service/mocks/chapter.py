from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid_extensions import uuid7str

from src.data.schemas.chapter import ChapterRow

from .common import now
from .db import FakePool


class FakeChapterRepository:
    def __init__(self):
        self._chapters: dict[str, ChapterRow] = {}
        self.error: Exception | None = None
        self.force_return_none: bool = False
        self.pool = FakePool()

    def seed(self, chapter: ChapterRow):
        self._chapters[chapter.id] = chapter

    async def get(self, chapter_id: str, user_id: str, *, executor=None) -> ChapterRow | None:
        if self.error:
            raise self.error
        chapter = self._chapters.get(chapter_id)
        if chapter and chapter.user_id == user_id:
            return chapter
        return None

    async def get_for_system(self, chapter_id: str) -> ChapterRow | None:
        if self.error:
            raise self.error
        return self._chapters.get(chapter_id)

    async def get_with_story_title(self, chapter_id: str, user_id: str) -> tuple[ChapterRow, str, int] | None:
        if self.error:
            raise self.error
        chapter = await self.get(chapter_id, user_id)
        if not chapter:
            return None
        return chapter, "Test Story", 1

    async def list_by_story(self, story_id: str, user_id: str, *, executor=None) -> list[ChapterRow]:
        if self.error:
            raise self.error
        return [
            chapter
            for chapter in self._chapters.values()
            if chapter.story_id == story_id and chapter.user_id == user_id
        ]

    async def list_by_ids(self, chapter_ids: list[str], *, executor=None) -> list[ChapterRow]:
        if self.error:
            raise self.error
        return [self._chapters[cid] for cid in chapter_ids if cid in self._chapters]

    async def list_by_story_ids(self, story_ids: list[str], *, executor=None) -> list[ChapterRow]:
        if self.error:
            raise self.error
        return [chapter for chapter in self._chapters.values() if chapter.story_id in story_ids]

    async def create(
        self,
        *,
        story_id: str,
        user_id: str,
        title: str,
        content: str,
        word_count: int,
    ) -> ChapterRow:
        if self.error:
            raise self.error
        chapter = ChapterRow(
            id=uuid7str(),
            story_id=story_id,
            user_id=user_id,
            title=title,
            content=content,
            published=False,
            word_count=word_count,
            next_chapter_id=None,
            prev_chapter_id=None,
            scenes_need_reextraction=False,
            scenes_extracted_at=None,
            created_at=now(),
            updated_at=now(),
        )
        self.seed(chapter)
        return chapter

    async def update(
        self,
        *,
        chapter_id: str,
        user_id: str,
        fields: dict,
        executor=None,
    ) -> ChapterRow | None:
        if self.error:
            raise self.error
        if self.force_return_none:
            return None
        chapter = await self.get(chapter_id, user_id)
        if not chapter:
            return None
        updated = chapter.model_copy(update={**fields, "updated_at": now()})
        self._chapters[chapter_id] = updated
        return updated

    async def delete(self, *, chapter_id: str, user_id: str, executor=None) -> ChapterRow | None:
        if self.error:
            raise self.error
        chapter = self._chapters.get(chapter_id)
        if chapter and chapter.user_id == user_id:
            del self._chapters[chapter_id]
            return chapter
        return None

    async def sync_pointers(self, path: Sequence[str], *, executor=None) -> None:
        if self.error:
            raise self.error

    async def mark_schapter_stale(self, chapter_id: str, *, executor=None) -> None:
        if self.error:
            raise self.error
        chapter = self._chapters.get(chapter_id)
        if not chapter:
            return None
        self._chapters[chapter_id] = chapter.model_copy(
            update={"scenes_need_reextraction": True}
        )

    async def mark_chapter_extracted(self, chapter_id: str, *, executor=None) -> None:
        if self.error:
            raise self.error
        chapter = self._chapters.get(chapter_id)
        if not chapter:
            return None
        self._chapters[chapter_id] = chapter.model_copy(
            update={"scenes_extracted_at": now()}
        )

    async def list_stale_chapter_ids(
        self,
        *,
        window_seconds: int,
        limit: int,
        executor=None,
    ) -> tuple[list[str], str]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        results = [
            chapter
            for chapter in self._chapters.values()
            if chapter.scenes_need_reextraction
            and chapter.updated_at <= cutoff
            and chapter.published
        ]
        return [chapter.id for chapter in results], results[0].user_id
