from copy import deepcopy
from datetime import datetime, timedelta, timezone

from src.data.schemas.chapter import ChapterRow
from src.data.schemas.scene import Scene, SceneRow
from tests.service.mocks.chapter import FakeChapterRepository
from tests.service.mocks.scene import FakeSceneRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ExtractionChapterRepository(FakeChapterRepository):
    def __init__(self) -> None:
        super().__init__()
        self.mark_extracted_error: Exception | None = None
        self.last_mark_executor = None
        self.last_stale_query: tuple[int, int] | None = None

    async def mark_chapter_extracted(self, chapter_id: str, *, executor=None) -> None:
        self.last_mark_executor = executor
        if self.mark_extracted_error:
            raise self.mark_extracted_error
        if self.error:
            raise self.error

        chapter = self._chapters.get(chapter_id)
        if chapter is None:
            return

        now = _now()
        self._chapters[chapter_id] = chapter.model_copy(
            update={
                "scenes_need_reextraction": False,
                "scenes_extracted_at": now,
                "updated_at": now,
            }
        )

    async def list_stale_chapter_ids(
        self,
        *,
        window_seconds: int,
        limit: int,
        executor=None,
    ) -> tuple[list[str], str]:
        self.last_stale_query = (window_seconds, limit)
        cutoff = _now() - timedelta(seconds=window_seconds)
        results = [
            chapter
            for chapter in self._chapters.values()
            if chapter.scenes_need_reextraction
            and chapter.updated_at <= cutoff
            and chapter.published
        ]
        results.sort(key=lambda chapter: chapter.updated_at)
        results = results[:limit]
        return [chapter.id for chapter in results], results[0].user_id if results else ""


class SnapshotTransaction:
    def __init__(
        self,
        chapter_repo: ExtractionChapterRepository,
        scene_repo: "ExtractionSceneRepository",
    ) -> None:
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo
        self._chapter_snapshot: dict[str, ChapterRow] = {}
        self._scene_snapshot: dict[str, SceneRow] = {}

    async def __aenter__(self):
        self._chapter_snapshot = deepcopy(self._chapter_repo._chapters)
        self._scene_snapshot = deepcopy(self._scene_repo._scenes)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self._chapter_repo._chapters = self._chapter_snapshot
            self._scene_repo._scenes = self._scene_snapshot
        return False


class SnapshotConnection:
    def __init__(
        self,
        chapter_repo: ExtractionChapterRepository,
        scene_repo: "ExtractionSceneRepository",
    ) -> None:
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo

    def transaction(self) -> SnapshotTransaction:
        return SnapshotTransaction(self._chapter_repo, self._scene_repo)


class SnapshotAcquireContext:
    def __init__(
        self,
        chapter_repo: ExtractionChapterRepository,
        scene_repo: "ExtractionSceneRepository",
    ) -> None:
        self._connection = SnapshotConnection(chapter_repo, scene_repo)

    async def __aenter__(self) -> SnapshotConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class SnapshotPool:
    def __init__(
        self,
        chapter_repo: ExtractionChapterRepository,
        scene_repo: "ExtractionSceneRepository",
    ) -> None:
        self._chapter_repo = chapter_repo
        self._scene_repo = scene_repo

    def acquire(self) -> SnapshotAcquireContext:
        return SnapshotAcquireContext(self._chapter_repo, self._scene_repo)


class ExtractionSceneRepository(FakeSceneRepository):
    def __init__(self, chapter_repo: ExtractionChapterRepository) -> None:
        super().__init__(chapter_repo)
        self.fail_after_delete: Exception | None = None
        self.last_replace_executor = None
        self.pool = SnapshotPool(chapter_repo, self) # type: ignore

    async def replace_for_chapter( #type: ignore
        self,
        *,
        chapter_id: str,
        story_id: str,
        user_id: str,
        scenes: list[Scene],
        executor=None,
    ) -> None:
        self.last_replace_executor = executor
        if self.error:
            raise self.error

        self._scenes = {
            scene_id: scene
            for scene_id, scene in self._scenes.items()
            if scene.chapter_id != chapter_id
        }

        if self.fail_after_delete:
            raise self.fail_after_delete

        now = _now()
        for position, scene in enumerate(scenes):
            row = SceneRow(
                id=f"scene-{chapter_id}-{position}",
                chapter_id=chapter_id,
                story_id=story_id,
                user_id=user_id,
                position=position,
                title=scene.title,
                start_quote=scene.start_quote,
                end_quote=scene.end_quote,
                description=scene.description,
                pov=scene.pov,
                word_count=len(scene.description.split()),
                tension=scene.tension,
                pacing=scene.pacing,
                mentioned_entities=scene.mentioned_entities,
                tags=scene.tags,
                questions_raised=scene.questions_raised,
                embedding_model=None,
                embedded_at=None,
                created_at=now,
                updated_at=now,
            )
            self._scenes[row.id] = row


class RecordingLogger:
    def __init__(self) -> None:
        self.infos: list[tuple[str, dict]] = []
        self.warnings: list[tuple[str, dict]] = []

    def info(self, event: str, **kwargs) -> None:
        self.infos.append((event, kwargs))

    def warning(self, event: str, **kwargs) -> None:
        self.warnings.append((event, kwargs))
