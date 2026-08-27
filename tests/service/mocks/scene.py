from datetime import datetime, timezone

from src.data.schemas.scene import SceneRow, SceneSearchResult

from .chapter import FakeChapterRepository
from .common import now
from .db import FakePool


class FakeSceneRepository:
    def __init__(self, chapter_repo: FakeChapterRepository):
        self._scenes: dict[str, SceneRow] = {}
        self._chapter_repo = chapter_repo
        self.error: Exception | None = None
        self.pool: FakePool = FakePool()
        self.embedding_updates: list[tuple[str, list[float], str]] = []
        self.update_embedding_errors: dict[str, Exception] = {}
        self.pending_limit: int | None = None

    def seed(self, scene: SceneRow) -> None:
        self._scenes[scene.id] = scene

    def get(self, scene_id: str) -> SceneRow | None:
        return self._scenes.get(scene_id)

    async def list_by_chapter(self, chapter_id: str, *, executor=None) -> list[SceneRow]:
        if self.error:
            raise self.error
        return [scene for scene in self._scenes.values() if scene.chapter_id == chapter_id]

    async def list_by_story(
        self,
        story_id: str,
        user_id: str,
        chapter_id: str | None = None,
        *,
        executor=None,
    ) -> list[SceneRow]:
        if self.error:
            raise self.error
        results = [
            scene
            for scene in self._scenes.values()
            if scene.story_id == story_id and scene.user_id == user_id
        ]
        if chapter_id:
            results = [scene for scene in results if scene.chapter_id == chapter_id]
        return results

    async def get_scene_text(self, scene_id: str, *, executor=None) -> str | None:
        if self.error:
            raise self.error
        scene = self._scenes.get(scene_id)
        return scene.description if scene else None

    async def get_scene_word_count(self, scene_id: str, *, executor=None) -> int:
        if self.error:
            raise self.error
        return 100

    async def replace_for_chapter(
        self,
        *,
        chapter_id: str,
        story_id: str,
        user_id: str,
        scenes: list,
        executor=None,
    ) -> list:
        if self.error:
            raise self.error
        self._scenes = {
            key: value
            for key, value in self._scenes.items()
            if value.chapter_id != chapter_id
        }
        return scenes

    async def update_embedding(
        self,
        *,
        scene_id: str,
        embedding: list[float],
        embedding_model: str,
        executor=None,
    ) -> None:
        if self.error:
            raise self.error
        if error := self.update_embedding_errors.get(scene_id):
            raise error

        self.embedding_updates.append((scene_id, list(embedding), embedding_model))
        scene = self._scenes.get(scene_id)
        if scene is not None:
            current = datetime.now(timezone.utc)
            self._scenes[scene_id] = scene.model_copy(
                update={
                    "embedding_model": embedding_model,
                    "embedded_at": current,
                    "updated_at": current,
                }
            )

    async def list_pending_embeddings(
        self,
        *,
        limit: int,
        executor=None,
    ) -> list[SceneRow]:
        if self.error:
            raise self.error
        self.pending_limit = limit
        pending = [
            scene
            for scene in self._scenes.values()
            if scene.embedded_at is None
        ]
        pending.sort(key=lambda scene: scene.created_at)
        return pending[:limit]

    async def mark_chapter_stale(self, chapter_id: str, *, executor=None) -> None:
        if self.error:
            raise self.error
        chapter = self._chapter_repo._chapters.get(chapter_id)
        if chapter is None:
            return
        chapter.scenes_need_reextraction = True
        chapter.updated_at = now()

    async def mark_chapter_extracted(self, chapter_id: str, *, executor=None) -> None:
        if self.error:
            raise self.error
        chapter = self._chapter_repo._chapters.get(chapter_id)
        if chapter is None:
            return
        current = now()
        chapter.scenes_need_reextraction = False
        chapter.scenes_extracted_at = current
        chapter.updated_at = current

    async def list_stale_chapter_ids(self, story_id: str, *, executor=None) -> tuple[list[str], str]:
        if self.error:
            raise self.error
        return [], ""

    async def search_scenes(
        self,
        user_id: str,
        story_id: str,
        query_text: str,
        k: int,
        candidate_pool: int,
        query_embedding: list[float],
        **filters,
    ) -> list[SceneSearchResult]:
        if self.error:
            raise self.error
        return []

    async def list_story_tags(self, *, user_id: str, story_id: str, executor=None) -> list[dict]:
        if self.error:
            raise self.error
        return []

    async def list_story_entities(self, *, user_id: str, story_id: str, executor=None) -> list[dict]:
        if self.error:
            raise self.error
        return []

    async def list_povs(self, *, user_id: str, story_id: str, executor=None) -> list[dict]:
        if self.error:
            raise self.error
        return []
